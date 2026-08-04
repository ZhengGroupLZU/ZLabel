from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel


class SamReturn(BaseModel):
    anno_id: str
    status: bool = False
    mode: str
    msg: str = ""
    # annotated data, rectangle, polygon and RLE-encoded mask str
    data: Sequence["Rect | Polygon | str"] | None = None


class Point(BaseModel):
    x: float
    y: float


class Rect(BaseModel):
    x: float
    y: float
    w: float
    h: float

    def to_list(self):
        return [self.x, self.y, self.w, self.h]

    def to_list_x1y1(self):
        return [self.x, self.y, self.x1, self.y1]

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.h


class Polygon(BaseModel):
    points: list[Point]

    # ref.: https://www.kaggle.com/stainsby/fast-tested-rle
    @staticmethod
    def rle_encode(img: np.ndarray):
        """
        img: numpy array, 1 - mask, 0 - background
        Returns run length as string formated
        """
        pixels = img.flatten()
        pixels = np.concatenate([[0], pixels, [0]])
        runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
        runs[1::2] -= runs[::2]
        return " ".join(str(x) for x in runs)

    @staticmethod
    def rle_decode(mask_rle: str, shape: tuple[int, int]) -> np.ndarray:
        """
        mask_rle: run-length as string formated (start length)
        shape: (height,width) of array to return
        Returns numpy array, 1 - mask, 0 - background
        """
        s = mask_rle.split()
        starts, lengths = [np.asarray(x, dtype=int) for x in (s[0:][::2], s[1:][::2])]
        starts -= 1
        ends = starts + lengths
        img = np.zeros(shape[0] * shape[1], dtype=np.uint8)
        for lo, hi in zip(starts, ends):
            img[lo:hi] = 1
        return img.reshape(shape)


@dataclass
class SamOnnxResult:
    mask: NDArray[np.float32]
    score: float


class PromptType(Enum):
    POINT = "point"
    RECTANGLE = "rectangle"


@dataclass
class SamOnnxPrompt:
    type_: PromptType
    # (x, y) for point, (x0, y0, x1, y1) for rectangle
    point: tuple[float, float] | tuple[float, float, float, float]
    label: float

    @staticmethod
    def new(p: Point | Rect | tuple[int, int] | tuple[int, int, int, int], label):
        match p:
            case Point():
                prompt = SamOnnxPrompt(PromptType.POINT, (p.x, p.y), label)
            case Rect():
                prompt = SamOnnxPrompt(
                    PromptType.RECTANGLE,
                    (p.x, p.y, p.x1, p.y1),
                    label,
                )
            case (x, y):
                prompt = SamOnnxPrompt(PromptType.POINT, (float(x), float(y)), label)
            case (x, y, w, h):
                prompt = SamOnnxPrompt(
                    PromptType.RECTANGLE,
                    (float(x), float(y), float(w), float(h)),
                    label,
                )
            case _:
                raise ValueError
        return prompt


@dataclass
class SamOnnxEncodedInput:
    image_embedding: NDArray[np.float32]
    original_height: int
    original_width: int
    resized_height: int
    resized_width: int
    high_res_feats_0: np.ndarray | None = None  # SAM2
    high_res_feats_1: np.ndarray | None = None  # SAM2
