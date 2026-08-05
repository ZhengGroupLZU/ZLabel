from enum import Flag, IntEnum, StrEnum


class AutoMode(Flag):
    SAM = 1
    CV = 2
    SAM_AND_CV = 1 & 2
    MANUAL = 3


class ReturnType(Flag):
    RECT = 1
    POLYGON = 2
    RLE = 3


class RgbMode(IntEnum):
    R = 1
    G = 2
    B = 3
    RGB = 4
    GRAY = 5


class StatusMode(IntEnum):
    VIEW = 0
    CREATE = 1
    EDIT = 2


class DrawMode(IntEnum):
    POINT = 0
    RECTANGLE = 1
    POLYGON = 2
    SAM_RECT = 3
    SAM_POLYGON = 4


class ClickMode(IntEnum):
    POSITIVE = 0
    NEGATIVE = 1


class MapMode(IntEnum):
    LABEL = 0
    SEMANTIC = 1
    INSTANCE = 2


class ContourMode(IntEnum):
    SAVE_MAX_ONLY = 0  # 只保留最多顶点的mask（一般为最大面积）
    SAVE_EXTERNAL = 1  # 只保留外轮廓
    SAVE_ALL = 2  # 保留所有轮廓


class AnnotationType(IntEnum):
    RECTANGLE = 0
    POLYGON = 1
    POINT = 2


class KeypointVisible(IntEnum):
    MISSING = 0  # not labeled
    VISIBLE = 1  # labeled and visible
    OCCLUDED = 2  # labeled but occluded


class FetchType(IntEnum):
    UNFINISHED = 0
    FINISHED = 1
    ALL = -1


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


class Language(StrEnum):
    ENGLISH = "en"
    CHINESE = "zh_CN"
