"""Shared data / result types for the local MNN inference backend."""

from collections.abc import Sequence
from dataclasses import dataclass

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
        pixels = img.flatten()
        pixels = np.concatenate([[0], pixels, [0]])
        runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
        runs[1::2] -= runs[::2]
        return " ".join(str(x) for x in runs)

    @staticmethod
    def rle_decode(mask_rle: str, shape: tuple[int, int]) -> np.ndarray:
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
    """One predicted object: binary mask (H,W) + score + optional xyxy box (px)."""

    mask: NDArray[np.float32]
    score: float
    box: tuple[float, float, float, float] | None = None


@dataclass
class PvsResult:
    """Interactive (points/box) single-object result, SAM3 PVS path."""

    mask: NDArray[np.uint8]  # (H, W) binary in original image space
    score: float
    box: NDArray[np.float32]  # (4,) xyxy in original pixel coords
