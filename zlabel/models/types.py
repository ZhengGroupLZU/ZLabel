from enum import Enum
from typing import List, Tuple
from pydantic import BaseModel
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class SamOnnxResult(object):
    mask:NDArray[np.float32]
    score: float


class PromptType(Enum):
    POINT = "point"
    RECTANGLE = "rectangle"


@dataclass
class SamOnnxPrompt(object):
    type_: PromptType
    # (x, y) for point, (x0, y0, x1, y1) for rectangle
    point: Tuple[float, float] | Tuple[float, float, float, float]
    label: float

    @staticmethod
    def new(p, label):
        match len(p):
            case 2:
                p = SamOnnxPrompt(PromptType.POINT, p, label)
            case 4:
                p = SamOnnxPrompt(PromptType.RECTANGLE, p, label)
            case _:
                raise ValueError
        return p


@dataclass
class SamOnnxEncodedInput(object):
    image_embedding: NDArray[np.float32]
    original_height: int
    original_width: int
    resized_height: int
    resized_width: int
