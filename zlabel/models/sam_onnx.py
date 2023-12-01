import copy
from functools import lru_cache
import hashlib
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
import onnxruntime as ort
from numpy.typing import NDArray

from ..utils.logger import ZLogger
from .types import PromptType, SamOnnxEncodedInput, SamOnnxPrompt, SamOnnxResult


class SamOnnxModel:
    """Segmentation model using SegmentAnything"""

    def __init__(self, encoder_path: str, decoder_path: str) -> None:
        self.img_size: int = 1024
        self.input_size = (1024, 1024)
        self.logger = ZLogger("SamOnnxModel")
        self.img = None
        self._cache: Dict[str, SamOnnxEncodedInput] = {}

        # Load models
        providers: List[str] = ort.get_available_providers()

        # Pop TensorRT Runtime due to crashing issues
        # TODO: Add back when TensorRT backend is stable
        providers = [p for p in providers if p != "TensorrtExecutionProvider"]

        if providers:
            self.logger.info(f"Available providers for ONNXRuntime: {providers}")
        else:
            self.logger.warning("No available providers for ONNXRuntime")
        self.encoder = ort.InferenceSession(encoder_path, providers=providers)
        self.encoder_input_name: str = self.encoder.get_inputs()[0].name
        self.decoder = ort.InferenceSession(decoder_path, providers=providers)

    def add_encoded_input(self, key: str, inp: SamOnnxEncodedInput):
        if key not in self._cache:
            self._cache[key] = inp

    def key_cached(self, key: str):
        return key in self._cache

    def get_encoded_input(self, key: str):
        return self._cache.get(key, None)

    def get_input_points(self, prompt: List[SamOnnxPrompt]):
        """Get input points"""
        points = []
        labels = []
        for i, mark in enumerate(prompt):
            if mark.type_ == PromptType.POINT:
                points.append(mark.point)
                labels.append(mark.label)
            elif mark.type_ == PromptType.RECTANGLE:
                points.append([mark.point[0], mark.point[1]])  # top left
                points.append([mark.point[2], mark.point[3]])  # type: ignore bottom right
                labels.append(2)
                labels.append(3)
            else:
                raise NotImplementedError
        points, labels = (
            np.array(points, dtype=np.float32),
            np.array(labels, dtype=np.float32),
        )
        return points, labels

    def run_encoder(self, img: NDArray) -> NDArray[np.float32]:
        """Run encoder"""
        if img.dtype != np.float32:
            img = img.astype(np.float32)
        if img.ndim == 2:
            img = np.expand_dims(img, 2)
        if img.ndim == 3:
            img = np.expand_dims(img, 0)
        encoder_inputs = {self.encoder_input_name: img}
        image_embedding = self.encoder.run(None, encoder_inputs)[0]
        return image_embedding

    @staticmethod
    def get_preprocess_shape(oldh: int, oldw: int, long_side_length: int):
        """
        Compute the output size given input size and target long side length.
        """
        scale = long_side_length * 1.0 / max(oldh, oldw)
        newh, neww = oldh * scale, oldw * scale
        neww = int(neww + 0.5)
        newh = int(newh + 0.5)
        return (newh, neww)

    def transform_point_labels(
        self,
        points: NDArray,
        labels: NDArray,
        original_height: int,
        original_width: int,
        resized_height: int,
        resized_width: int,
    ):
        """
        Expects a numpy array of length 2 in the final dimension. Requires the
        original image size in (H, W) format.
        """
        assert points.ndim == 2 and labels.ndim == 1
        if (labels == 2).astype(np.int8).sum() == 0:
            onnx_coord = np.concatenate(
                [points, np.array([[0.0, 0.0]])],
                axis=0,
            )[None, ...]
            onnx_label = np.append(labels, -1)[None, :].astype(np.float32)
        else:
            onnx_coord = points[None, ...]
            onnx_label = labels[None, :].astype(np.float32)
        coords = copy.deepcopy(onnx_coord).astype(np.float32)
        coords[..., 0] = coords[..., 0] * (resized_width / original_width)
        coords[..., 1] = coords[..., 1] * (resized_height / original_height)
        onnx_coord = coords.astype("float32")
        return onnx_coord, onnx_label

    def run_decoder(
        self,
        einput: SamOnnxEncodedInput,
        prompt: List[SamOnnxPrompt],
    ):
        """Run decoder"""
        # (N, 2), (N,)
        input_points, input_labels = self.get_input_points(prompt)

        onnx_coord, onnx_label = self.transform_point_labels(
            input_points,
            input_labels,
            einput.original_height,
            einput.original_width,
            einput.resized_height,
            einput.resized_width,
        )
        onnx_mask_input = np.zeros((1, 1, 256, 256), dtype=np.float32)
        onnx_has_mask_input = np.zeros(1, dtype=np.float32)

        decoder_inputs = {
            "image_embeddings": einput.image_embedding,
            "point_coords": onnx_coord,
            "point_labels": onnx_label,
            "mask_input": onnx_mask_input,
            "has_mask_input": onnx_has_mask_input,
            "orig_im_size": np.array(
                [einput.original_height, einput.original_width],
                dtype=np.float32,
            ),
        }
        masks, scores, logits = self.decoder.run(None, decoder_inputs)

        return self.decode(masks[0], scores[0])

    def encode(self, cv_image: NDArray):
        """
        Calculate embedding and metadata for a single image.
        """
        md5 = hashlib.md5(cv_image.tobytes()).hexdigest()
        res = self._cache.get(md5, None)
        if res is not None:
            return res

        h, w, c = cv_image.shape
        if h > w:
            nh = self.input_size[0]
            nw = int(self.input_size[0] / h * w)
        else:
            nw = self.input_size[1]
            nh = int(self.input_size[1] / w * h)
        cv_image = cv2.resize(cv_image, (nw, nh), interpolation=cv2.INTER_AREA)

        if nh < nw:
            cv_image = np.pad(cv_image, ((0, self.input_size[0] - nh), (0, 0), (0, 0)))
        else:
            cv_image = np.pad(cv_image, ((0, 0), (0, self.input_size[1] - nw), (0, 0)))

        mean = np.array([123.675, 116.28, 103.53])
        std = np.array([[58.395, 57.12, 57.375]])
        cv_image = (cv_image - mean) / std

        cv_image = np.transpose(cv_image, (2, 0, 1))[None, ...]
        image_embedding = self.run_encoder(cv_image)
        res = SamOnnxEncodedInput(image_embedding, h, w, nh, nw)
        self._cache[md5] = res
        return res

    def decode(self, masks: NDArray[np.float32], scores: NDArray[np.float32]):
        idx = np.argmax(scores[:-1])
        return SamOnnxResult((masks[idx] > 0).astype(np.uint8) * 255, scores[idx])

    def predict(self, img: NDArray, prompts: List[SamOnnxPrompt]):
        img_encoded = self.encode(cv_image=img)
        out = self.run_decoder(img_encoded, prompts)
        return out
