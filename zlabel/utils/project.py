from datetime import datetime
from enum import Enum
from functools import cached_property
import hashlib
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, NamedTuple
from collections import OrderedDict
from uuid import uuid4
import uuid
from pydantic import BaseModel, PrivateAttr
from rich import print


def id_uuid4(length=9) -> str:
    return uuid.uuid4().hex[:length]


def id_md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:9]


class ResultStep(NamedTuple):
    anno_id: str
    result: "Result"


class Stack(object):
    def __init__(self, maxsize=10):
        self.stack = []
        self.maxsize = maxsize
        self._len = 0

    def __len__(self):
        return self._len

    def push(self, item):
        if self._len + 1 < self.maxsize:
            self.stack.append(item)
            self._len += 1
        else:
            del self.stack[0]
            self.stack.append(item)

    def pop(self):
        self._len -= 1
        return self.stack.pop()

    def __repr__(self) -> str:
        return str(self.stack)


# 1
class User(BaseModel):
    id: str
    name: str
    email: str = ""

    @staticmethod
    def default():
        return User(id=id_uuid4(), name="Default User", email="default@zlabel.com")


# 1
class Label(BaseModel):
    id: str
    name: str
    color: str = "#000000"

    @staticmethod
    def default():
        return Label(id=id_uuid4(), name="UNKNOWN", color="#000000")


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


class Annotation(BaseModel):
    id: str
    created_by: User | None = None
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime
    label_path: str
    image_path: str
    ground_truth: Optional[bool] = False
    original_width: float
    original_height: float
    image_rotation: Optional[int] = 0
    results: OrderedDict[str, Result] = OrderedDict()
    result_key: str = ""

    def save_json(self, path: str | None = None):
        path = path or self.label_path
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

    def __eq__(self, v: "Annotation") -> bool:
        return (
            self.label_path == v.label_path
            and self.image_path == v.image_path
            and self.original_width == v.original_width
            and self.original_height == v.original_height
            and self.image_rotation == v.image_rotation
        )

    def current_result(self):
        return self.results.get(self.result_key, None)

    def add_result(self, result: Result):
        self.results[result.id] = result
        self.result_key = result.id

    def remove_result(self, id_: str):
        if id_ not in self.results:
            return False
        last_keys = list(self.results.keys())
        idx = last_keys.index(id_)
        idx_new = min(idx - 1, idx + 1)
        new_key = last_keys[idx_new] if idx_new >= 0 else ""

        self.results.pop(id_)
        self.result_key = new_key
        print(f"Removed {id_=}")
        return True

    @staticmethod
    def new(
        image_path: str,
        width: float,
        height: float,
        create_user: User,
        id_: str | None = None,
        anno_suffix: str = "zlabel",
    ) -> "Annotation":
        path = Path(image_path)
        anno = Annotation(
            id=id_ or id_uuid4(),
            created_by=create_user,
            updated_by=create_user,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            label_path=f"{path.parent / path.name}.{anno_suffix}",
            image_path=image_path,
            original_width=width,
            original_height=height,
        )
        return anno


# 1
class Project(BaseModel):
    id: str
    name: str
    description: str | None = "New Project"

    default_user: ClassVar[User] = User.default()

    key_label: str = ""  # current label id
    key_anno: str = ""  # current annotation id
    key_user: str = ""  # current user id

    users: OrderedDict[str, User] = OrderedDict()
    labels: OrderedDict[str, Label] = OrderedDict()
    annotations: OrderedDict[str, Annotation] = OrderedDict()
    project_path: str

    # region functions
    @staticmethod
    def new(
        project_path: str,
        name: str = "New Project",
        description: str = "New Project",
        users: OrderedDict[str, User] | None = None,
        labels: OrderedDict[str, Label] | None = None,
        annotations: OrderedDict[str, Annotation] | None = None,
        id: str | None = None,
    ):
        proj = Project(
            id=id or id_uuid4(),
            name=name,
            project_path=project_path,
            description=description,
            users=users or OrderedDict(),
            labels=labels or OrderedDict(),
            annotations=annotations or OrderedDict(),
        )
        return proj

    def has_annotations(self):
        return len(self.annotations) != 0

    def set_current_result(self, r: Result):
        if self.current_annotation:
            self.annotations[self.key_anno].result_key = r.id
            self.annotations[self.key_anno].results[r.id] = r

    def save_json(self, path: str | None = None):
        path = path or f"{self.project_path}/{self.name}.zproj"
        with open(path, "w", encoding="utf-8") as f:
            _ = f.write(self.model_dump_json(indent=4, exclude={"annotations"}))

    # endregion

    # region add new
    def add_annotation(self, anno: Annotation):
        self.annotations[anno.id] = anno
        self.key_anno = anno.id

    def add_label(self, label: Label):
        self.labels[label.id] = label
        self.key_label = label.id

    def add_user(self, user: User):
        self.users[user.id] = user
        self.key_user = user.id

    def add_result(self, result: Result):
        if not self.current_annotation:
            return
        self.annotations[self.key_anno].add_result(result)

    def remove_result(self, key: str):
        if not self.current_annotation:
            return False
        r = self.annotations[self.key_anno].remove_result(key)
        return r

    # endregion

    # region properties
    @property
    def current_label(self) -> Label | None:
        return self.labels.get(self.key_label, None)

    @property
    def current_annotation(self) -> Annotation | None:
        return self.annotations.get(self.key_anno, None)

    @property
    def image_paths(self):
        return [anno.image_path for anno in self.annotations.values()]

    @property
    def current_image_path(self) -> str | None:
        return self.current_annotation.image_path if self.current_annotation else None

    @property
    def current_user(self) -> User:
        return self.users.get(self.key_user, self.default_user)

    @property
    def current_result(self) -> Result | None:
        anno = self.current_annotation
        if not anno:
            return None
        return anno.current_result()

    @property
    def current_image_idx(self) -> int:
        return self.image_paths.index(self.current_image_path) if self.current_image_path else -1

    @property
    def max_image_idx(self) -> int:
        return len(self.image_paths) - 1

    # endregion
