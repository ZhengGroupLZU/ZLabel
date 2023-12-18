from datetime import datetime
from enum import Enum
from functools import cached_property
import hashlib
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, NamedTuple
from collections import OrderedDict
from typing_extensions import Literal
from uuid import uuid4
import uuid
from pydantic import BaseModel, Field, PrivateAttr
from rich import print


def id_uuid4(length=9) -> str:
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


class Result(BaseModel):
    id: str
    type_id: ResultType
    origin: str = "manual"
    score: float = 0
    note: str = ""
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    rotation: float = 0
    labels: List[Label]

    @staticmethod
    def new(
        type_id: ResultType,
        labels: List[Label],
        x: float = 0,
        y: float = 0,
        w: float = 0,
        h: float = 0,
        origin: str = "manual",
        score: float = 0,
        rotation: float = 0,
        id_=None,
    ):
        r = Result(
            id=id_ or id_uuid4(),
            type_id=type_id,
            labels=labels,
            x=x,
            y=y,
            w=w,
            h=h,
            origin=origin,
            score=score,
            rotation=rotation,
        )

        return r

    def equal_v(self, r: "Result"):
        return (
            self.x == r.x
            and self.y == r.y
            and self.w == r.w
            and self.h == r.h
            and self.rotation == r.rotation
            and self.type_id == r.type_id
        )


class Annotation(BaseModel):
    id: str
    created_by: User | None = None
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime

    image_path: str
    ground_truth: Optional[bool] = False

    original_width: float
    original_height: float
    image_rotation: Optional[int] = 0

    results: OrderedDict[str, Result] = OrderedDict()
    labels: OrderedDict[str, Label] = OrderedDict()

    key_result: str | None = None
    key_label: str | None = None

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

    def add_result(self, result: Result):
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

    @property
    def crt_label(self) -> Label | None:
        if self.key_label is None:
            return None
        return self.labels.get(self.key_label, None)

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

    def set_color(self, color: str):
        for k in self.results:
            for label in self.results[k].labels:
                label.color = color

    @staticmethod
    def new(
        image_path: str,
        width: float,
        height: float,
        create_user: User | None,
        id_: str,
        labels: OrderedDict[str, Label],
    ) -> "Annotation":
        anno = Annotation(
            id=id_,
            created_by=create_user,
            updated_by=create_user,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            image_path=image_path,
            original_width=width,
            original_height=height,
            labels=labels,
        )
        return anno


class Task(BaseModel):
    id: int
    anno_id: str
    filename: str
    labels: List[str]
    finished: bool = False

    anno: Annotation | None = Field(None, exclude=True)


# 1
class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = "New Project"

    key_task: str | None = None

    draft: Annotation | None = None
    tasks: OrderedDict[str, Task] = OrderedDict()

    # region functions
    @staticmethod
    def new(
        name: str = "New Project",
        description: str = "New Project",
        tasks: OrderedDict[str, Task] = OrderedDict(),
        draft: Annotation | None = None,
        id: str | None = None,
    ):
        proj = Project(
            id=id or id_uuid4(),
            name=name,
            description=description,
            tasks=tasks,
            draft=draft,
        )
        return proj

    def save_json(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4, exclude={}))

    def reset_task_key(self):
        if len(self.tasks) > 0:
            self.key_task = list(self.tasks.keys())[0]
        else:
            self.key_task = None

    def add_task(self, task: Task):
        self.tasks[task.anno_id] = task
        self.key_task = task.anno_id

    def add_annotation(self, anno: Annotation):
        self.tasks[anno.id].anno = anno
        self.key_task = anno.id

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
    def label_id(self):
        if self.crt_anno is None:
            return None
        return self.crt_anno.key_label

    @label_id.setter
    def label_id(self, id_: str):
        if self.crt_anno is None:
            return
        self.crt_anno.key_label = id_

    @property
    def labels(self):
        if self.crt_anno:
            return list(self.crt_anno.labels.values())
        return []

    @property
    def crt_label(self) -> Label | None:
        if self.crt_anno is None:
            return None
        return self.crt_anno.crt_label

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
