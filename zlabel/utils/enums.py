from enum import Enum, Flag


class AutoMode(Flag):
    SAM = 1
    CV = 2
    SAM_AND_CV = 1 & 2
    SAM_OR_CV = 1 | 2
    MANUAL = 3


class StatusMode(Enum):
    VIEW = 0
    CREATE = 1
    EDIT = 2


class DrawMode(Enum):
    POINT = 0
    RECTANGLE = 1
    POLYGON = 2
    SAM_RECT = 3
    SAM_POLYGON = 4


class ClickMode(Enum):
    POSITIVE = 0
    NEGATIVE = 1


class MapMode(Enum):
    LABEL = 0
    SEMANTIC = 1
    INSTANCE = 2


class ContourMode(Enum):
    SAVE_MAX_ONLY = 0  # 只保留最多顶点的mask（一般为最大面积）
    SAVE_EXTERNAL = 1  # 只保留外轮廓
    SAVE_ALL = 2  # 保留所有轮廓


class SettingsKey(Enum):
    PROJECT_PATH = "project/path"
    PROJECT_FILE = "project/file"