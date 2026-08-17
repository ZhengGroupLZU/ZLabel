"""Image preprocessing for the local MNN models (SAM/EdgeSAM/SAM2 and SAM3)."""

from __future__ import annotations

import cv2
import numpy as np

SAM_MEAN = np.array([123.675, 116.28, 103.53])
SAM_STD = np.array([[58.395, 57.12, 57.375]])


def preprocess_sam(image_bgr: np.ndarray, img_size: int = 1024) -> np.ndarray:
    """SAM / EdgeSAM / SAM2 encoder input: stretch to img_size square, mean/std normalize.

    Mirrors the reference SamOnnxModel.preprocess_image. Returns (1,3,H,W) fp32.
    """
    im = cv2.resize(image_bgr, (img_size, img_size), interpolation=cv2.INTER_LINEAR)
    im = im[..., ::-1].copy()  # BGR -> RGB
    im = im.astype(np.float32)
    im = (im - SAM_MEAN) / SAM_STD
    im = im.transpose(2, 0, 1)[None].astype(np.float32)
    return im


def preprocess_sam_pad(image_bgr: np.ndarray, img_size: int = 1024) -> tuple[np.ndarray, float]:
    """SlimSAM / SAM2 encoder input: aspect-preserving letterbox + bottom/right pad.

    Same SAM mean/std normalize as ``preprocess_sam`` but rescales by the min ratio
    and pads to the square, which is what the SlimSAM / SAM2 checkpoints expect
    (stretching displaces the mask vertically by 2x). Returns (1,3,H,W) fp32 and ratio.
    """
    h, w = image_bgr.shape[:2]
    r = min(img_size / h, img_size / w)
    new_unpad = (round(w * r), round(h * r))
    im = cv2.resize(image_bgr, new_unpad, interpolation=cv2.INTER_LINEAR)
    dw, dh = img_size - new_unpad[0], img_size - new_unpad[1]
    im = cv2.copyMakeBorder(im, 0, round(dh + 0.1), 0, round(dw + 0.1), cv2.BORDER_CONSTANT, value=(114,) * 3)
    im = im[..., ::-1].copy()  # BGR -> RGB
    im = im.astype(np.float32)
    im = (im - SAM_MEAN) / SAM_STD
    return im.transpose(2, 0, 1)[None].astype(np.float32), r


def preprocess_sam3(image_bgr: np.ndarray, target: int = 1008, pad: bool = False) -> np.ndarray:
    """SAM3 encoder input: stretch (PCS) or letterbox (PVS), normalized to [-1,1].

    Mirrors sam3_runner.preprocess / preprocess_pad. Returns (1,3,target,target) fp32.
    """
    h, w = image_bgr.shape[:2]
    if pad:
        r = min(target / h, target / w)
        new_unpad = (round(w * r), round(h * r))
        im = cv2.resize(image_bgr, new_unpad, interpolation=cv2.INTER_LINEAR)
        dw, dh = target - new_unpad[0], target - new_unpad[1]
        im = cv2.copyMakeBorder(im, 0, round(dh + 0.1), 0, round(dw + 0.1), cv2.BORDER_CONSTANT, value=(114,) * 3)
    else:
        im = cv2.resize(image_bgr, (target, target), interpolation=cv2.INTER_LINEAR)
    im = im[..., ::-1].copy()  # BGR -> RGB
    im = im.astype(np.float32)
    im = (im - 127.5) / 127.5
    im = im.transpose(2, 0, 1)[None].astype(np.float32)
    return im
