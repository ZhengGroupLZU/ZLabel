from enum import Enum, Flag


class AutoMode(Flag):
    SAM = 1
    CV = 2
    SAM_AND_CV = 1 & 2
    MANUAL = 3


class RgbMode(Enum):
    R = 1
    G = 2
    B = 3
    RGB = 4
    GRAY = 5


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
    HOST = "global/host"
    URL_PREFIX = "global/urlprefix"
    USER_NAME = "global/username"
    USER_PWD = "global/userpwd"
    ALPHA = "global/alpha"
    MODEL_API = "global/modelapi"
    ENCODER = "global/onnxencoder"
    DECODER = "global/onnxdecoder"
    LOGLEVEL = "global/loglevel"
    COLOR = "global/color"

    TASKS = "project/tasks"
    PROJ_NAME = "project/name"
    PROJ_DESCRIP = "project/description"
    PROJ_SAM = "project/samEnabled"
    PROJ_CV = "project/cvEnabled"
