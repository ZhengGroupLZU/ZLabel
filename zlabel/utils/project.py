import hashlib
import uuid
from collections import OrderedDict
from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, NamedTuple

import pyqtgraph as pg
from pydantic import BaseModel, Field, field_validator

type IncEx = set[int] | set[str] | Mapping[int, "IncEx | bool"] | Mapping[str, "IncEx | bool"]


def id_uuid4(length: int = 9) -> str:
    return uuid.uuid4().hex[:length]


def id_md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


class ResultStep(NamedTuple):
    anno_id: str
    result: "Result"


# 1
class User(BaseModel):
    id: str
    name: str
    email: str = ""

    @staticmethod
    def default():
        return User(id=id_uuid4(), name="Default User", email="default@zlabel.com")

    @staticmethod
    def new(name: str, email: str = "", id_: str = ""):
        return User(
            id=id_ or id_uuid4(),
            name=name,
            email=email,
        )


# 1
class Label(BaseModel):
    id: str
    name: str
    color: str = "#000000"

    @staticmethod
    def default():
        return Label(id=id_uuid4(), name="UNKNOWN", color="#000000")

    @staticmethod
    def new(name: str, color: str = "#000000", id_: str = ""):
        return Label(
            id=id_ or id_uuid4(),
            name=name,
            color=color,
        )


# 1
class ResultType(Enum):
    POINT = 0
    RECTANGLE = 1
    POLYGON = 2


class GermStatus(Enum):
    """Germination status of a seed instance (per-frame instance attribute)."""

    NORMAL_SEED = "normal_seed"
    MOLDY_SEED = "moldy_seed"
    DEAD_SEED = "dead_seed"
    NORMAL_SEEDLING = "normal_seedling"
    ABNORMAL_SEEDLING = "abnormal_seedling"


# Seed-germination preset labels (part tags + special tags). Status is NOT a
# Label: it lives on Annotation.instances[instance_id].
GERM_PRESET_LABELS: dict[str, str] = {
    "Seed": "#e6194b",
    "Root": "#3cb44b",
    "Shoot": "#f58231",
    "Seedling": "#4363d8",
    "Dish": "#911eb4",
    "Timestamp": "#808080",
    "Number": "#b8860b",
}


def germ_preset_labels() -> OrderedDict[str, Label]:
    """One-click preset: part labels (seed/root/shoot/seedling) + dish/timestamp tags."""
    labels: OrderedDict[str, Label] = OrderedDict()
    for name, color in GERM_PRESET_LABELS.items():
        lbl = Label.new(name=name, color=color)
        labels[lbl.id] = lbl
    return labels


class Result(BaseModel):
    id: str
    type_id: ResultType
    origin: str = "manual"
    score: float = 0
    note: str = ""
    labels: list[Label]
    # `instance_id` is the cross-frame identity of a tracked object (seed /
    # seedling): the same instance number in different frames of a sequence
    # denotes the same physical object. Within one frame it also groups the
    # object's parts (Seed/Root/Seedling polygons share the instance id).

    @staticmethod
    def new(
        type_id: ResultType,
        labels: list[Label],
        origin: str = "manual",
        score: float = 0,
        id_=None,
    ):
        r = Result(
            id=id_ or id_uuid4(),
            type_id=type_id,
            labels=labels,
            origin=origin,
            score=score,
        )

        return r

    def getState(self) -> dict[str, Any]:
        raise NotImplementedError


class PointResult(Result):
    x: float = 0.0
    y: float = 0.0
    visible: int = 1  # COCO keypoint visibility: 0=not labeled, 1=labeled, 2=occluded
    category_id: int = 0  # COCO keypoint category index
    instance_id: int = 0  # groups keypoints of the same instance (0 = none)

    @field_validator("instance_id", mode="before")
    @classmethod
    def _coerce_instance_id(cls, v):
        if isinstance(v, str) and v.isdigit():
            return int(v)
        if isinstance(v, str):
            return 0  # legacy uuid strings are dropped
        return v

    @staticmethod
    def new(
        type_id: ResultType = ResultType.POINT,
        labels: list[Label] | None = None,
        origin: str = "manual",
        score: float = 0,
        id_=None,
        x: float = 0.0,
        y: float = 0.0,
        visible: int = 1,
        category_id: int = 0,
        instance_id: int = 0,
    ):
        r = PointResult(
            id=id_ or id_uuid4(),
            type_id=type_id,
            labels=labels or [],
            origin=origin,
            score=score,
            x=x,
            y=y,
            visible=visible,
            category_id=category_id,
            instance_id=instance_id,
        )

        return r

    def equal_v(self, r: "Result"):
        return (
            isinstance(r, PointResult)
            and self.type_id == r.type_id
            and self.labels == r.labels
            and self.origin == r.origin
            and self.score == r.score
            and self.x == r.x
            and self.y == r.y
            and self.visible == r.visible
            and self.category_id == r.category_id
            and self.instance_id == r.instance_id
        )

    def getState(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pos": pg.Point(self.x, self.y),
            "visible": self.visible,
            "instance_id": self.instance_id,
        }


class RectangleResult(Result):
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    rotation: float = 0
    text: str = ""  # OCR'ed timestamp / label text
    instance_id: int = 0  # instance this rect belongs to (0 = none)

    @field_validator("instance_id", mode="before")
    @classmethod
    def _coerce_instance_id(cls, v):
        if isinstance(v, str) and v.isdigit():
            return int(v)
        if isinstance(v, str):
            return 0  # legacy uuid strings are dropped
        return v

    @staticmethod
    def new(
        type_id: ResultType = ResultType.RECTANGLE,
        labels: list[Label] | None = None,
        origin: str = "manual",
        score: float = 0,
        id_=None,
        x: float = 0.0,
        y: float = 0.0,
        w: float = 0.0,
        h: float = 0.0,
        rotation: float = 0,
        text: str = "",
        instance_id: int = 0,
    ):
        r = RectangleResult(
            id=id_ or id_uuid4(),
            type_id=type_id,
            labels=labels or [],
            origin=origin,
            score=score,
            x=x,
            y=y,
            w=w,
            h=h,
            rotation=rotation,
            text=text,
            instance_id=instance_id,
        )

        return r

    def equal_v(self, r: "Result"):
        return (
            isinstance(r, RectangleResult)
            and self.type_id == r.type_id
            and self.labels == r.labels
            and self.origin == r.origin
            and self.score == r.score
            and self.x == r.x
            and self.y == r.y
            and self.w == r.w
            and self.h == r.h
            and self.rotation == r.rotation
            and self.text == r.text
            and self.instance_id == r.instance_id
        )

    def getState(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pos": pg.Point(self.x, self.y),
            "size": pg.Point(self.w, self.h),
            "angle": self.rotation,
        }


class PolygonResult(Result):
    x: float = 0.0
    y: float = 0.0
    w: float = 1.0
    h: float = 1.0
    rotation: float = 0
    closed: bool
    points: list[tuple[float, float]] = []
    instance_id: int = 0  # groups seed/root/seedling polygons of one seed (0 = none)

    @field_validator("instance_id", mode="before")
    @classmethod
    def _coerce_instance_id(cls, v):
        if isinstance(v, str) and v.isdigit():
            return int(v)
        if isinstance(v, str):
            return 0  # legacy uuid strings are dropped
        return v

    @staticmethod
    def new(
        type_id: ResultType = ResultType.POLYGON,
        labels: list[Label] | None = None,
        origin: str = "manual",
        score: float = 0,
        id_=None,
        x: float = 0.0,
        y: float = 0.0,
        w: float = 1.0,
        h: float = 1.0,
        rotation: float = 0,
        closed: bool = True,
        points: list[tuple[float, float]] | None = None,
        instance_id: int = 0,
    ):
        r = PolygonResult(
            id=id_ or id_uuid4(),
            type_id=type_id,
            labels=labels or [],
            origin=origin,
            score=score,
            x=x,
            y=y,
            w=w,
            h=h,
            rotation=rotation,
            closed=closed,
            points=points or [],
            instance_id=instance_id,
        )

        return r

    def equal_v(self, r: "Result"):
        return (
            isinstance(r, PolygonResult)
            and self.type_id == r.type_id
            and self.labels == r.labels
            and self.origin == r.origin
            and self.score == r.score
            and self.x == r.x
            and self.y == r.y
            and self.w == r.w
            and self.h == r.h
            and self.rotation == r.rotation
            and self.closed == r.closed
            and self.points == r.points
            and self.instance_id == r.instance_id
        )

    def getState(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pos": pg.Point(self.x, self.y),
            "size": pg.Point(self.w, self.h),
            "angle": self.rotation,
            "points": self.points,
            "closed": self.closed,
            "instance_id": self.instance_id,
        }


class Annotation(BaseModel):
    id: str
    created_by: User | None = None
    updated_by: User | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    image_path: str
    ground_truth: bool = False

    original_width: float
    original_height: float
    image_rotation: int = 0
    note: str = ""

    group: str = ""  # sequence group name (e.g. "species/dish01")
    day: int = 0  # D{n} day index within the sequence
    instances: dict[int, str] = {}  # instance_id -> GermStatus value (per frame)

    @field_validator("instances", mode="before")
    @classmethod
    def _coerce_instances(cls, v):
        if isinstance(v, dict):
            out: dict[int, str] = {}
            for k, val in v.items():
                try:
                    out[int(k)] = val
                except (TypeError, ValueError):
                    continue
            return out
        return v

    results: OrderedDict[str, PointResult | RectangleResult | PolygonResult] = OrderedDict()

    key_result: str | None = None

    def save_json(self, path: str):
        p = Path(path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

    def __eq__(self, v: "Annotation") -> bool:  # type: ignore[override]
        return (
            self.image_path == v.image_path
            and self.original_width == v.original_width
            and self.original_height == v.original_height
            and self.image_rotation == v.image_rotation
        )

    @property
    def crt_result(self):
        """Current Result"""
        if self.key_result is None:
            return None
        return self.results.get(self.key_result, None)

    def add_result(self, result: PointResult | RectangleResult | PolygonResult):
        self.results[result.id] = result
        self.key_result = result.id

    def remove_result(self, id_: str | None):
        if id_ is None or id_ not in self.results:
            return False
        last_keys = list(self.results.keys())
        idx = last_keys.index(id_)
        idx_new = min(idx - 1, idx + 1)
        new_key = last_keys[idx_new] if idx_new >= 0 else None

        self.results.pop(id_)
        self.key_result = new_key
        return True

    def reset_results(self):
        self.results.clear()
        self.key_result = None


class Task(BaseModel):
    id: int
    anno_id: str
    filename: str
    labels: list[str]
    finished: bool = False
    group: str = ""  # sequence group (e.g. "species/dish01")
    day: int = 0  # D{n} day index within the sequence

    anno: Annotation | None = Field(None, exclude=True)


# 1
class Project(BaseModel):
    id: str
    name: str = "defaultProject"
    description: str | None = "New Project"

    storage_mode: Literal["remote", "local"] = "remote"
    local_dir: str = ""

    key_task: str | None = None
    key_label: str | None = None

    draft: Annotation | None = None
    tasks: OrderedDict[str, Task] = OrderedDict()
    labels: OrderedDict[str, Label] = OrderedDict()
    groups: dict[str, list[str]] = {}  # manual sequence groups: name -> anno_ids
    instance_statuses: list[str] = Field(
        default_factory=lambda: [s.value for s in GermStatus] + ["dish", "text"]
    )  # editable per-instance status values (stored in Annotation.instances)

    # region functions
    def save_json(self, path: str | Path, include: IncEx | None = None, exclude: IncEx | None = None):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if exclude is None:
            exclude = {"tasks": True}
        # Save project metadata without tasks - tasks should come from remote server
        p.write_text(self.model_dump_json(ensure_ascii=False, indent=2, include=include, exclude=exclude))

    def reset_task_key(self):
        if len(self.tasks) > 0:
            self.key_task = list(self.tasks.keys())[0]
        else:
            self.key_task = None

    def add_task(self, task: Task):
        self.tasks[task.anno_id] = task
        self.key_task = task.anno_id

    def add_annotation(self, anno: Annotation):
        self.reconcile_result_labels(anno)
        self.tasks[anno.id].anno = anno
        self.key_task = anno.id

    def reconcile_result_labels(self, anno: Annotation):
        """Re-point result labels at this project's Label objects.

        Results saved by older versions / other projects may embed Label
        objects whose ``id`` differs from this project's labels (same
        name/color, different id). Id-based lookups then fail - e.g. the
        label show/hide eye buttons in the Labels dock can't find any item.
        Map each result label to the project label with the same id, falling
        back to the same name; unmatched labels are left untouched.
        """
        if not self.labels:
            return
        by_name: dict[str, Label] = {}
        for lbl in self.labels.values():
            by_name.setdefault(lbl.name, lbl)
        for r in anno.results.values():
            if not r.labels:
                continue
            for i, lbl in enumerate(r.labels):
                if lbl.id in self.labels:
                    continue
                match = by_name.get(lbl.name)
                if match is not None:
                    r.labels[i] = match

    def add_label(self, label: Label):
        self.labels[label.id] = label
        self.key_label = label.id

    def remove_label(self, id_: str):
        if id_ not in self.labels:
            return False
        last_keys = list(self.labels.keys())
        idx = last_keys.index(id_)
        idx_new = min(idx - 1, idx + 1)
        new_key = last_keys[idx_new] if idx_new >= 0 else None

        self.labels.pop(id_)
        self.key_label = new_key
        return True

    # endregion

    # region properties

    @property
    def crt_task(self) -> Task | None:
        if self.key_task is None:
            return None
        return self.tasks.get(self.key_task, None)

    @property
    def anno_id(self):
        return self.key_task

    @anno_id.setter
    def anno_id(self, id_: str):
        if id_ in self.tasks:
            self.key_task = id_

    @property
    def crt_anno(self) -> Annotation | None:
        if self.crt_task is None:
            return None
        return self.crt_task.anno

    @property
    def crt_label(self) -> Label | None:
        if self.key_label is None:
            return None
        return self.labels.get(self.key_label, None)

    @property
    def key_result(self):
        if self.crt_anno:
            return self.crt_anno.key_result
        return None

    @key_result.setter
    def key_result(self, id_: str):
        if self.crt_anno and id_ in self.crt_anno.results:
            self.crt_anno.key_result = id_
        else:
            raise KeyError(f"{id_=} not in results, ensure that you have created it!")

    @property
    def crt_result(self):
        if self.crt_anno:
            return self.crt_anno.crt_result
        return None

    # endregion
