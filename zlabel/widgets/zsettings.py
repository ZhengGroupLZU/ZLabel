from pathlib import Path
from typing import Any

from pydantic import BaseModel, PrivateAttr, field_validator

from zlabel.utils.enums import AnnotationType, FetchType, LogLevel
from zlabel.utils.project import Project, id_uuid4


class ZSettings(BaseModel):
    root_dir: str = "."
    annotation_type: AnnotationType = AnnotationType.RECTANGLE
    fetch_type: FetchType = FetchType.FINISHED
    fetch_num: int = 100
    host: str = ""
    log_level: LogLevel = LogLevel.INFO
    username: str = ""
    password: str = ""
    default_color: str = "#000000"
    alpha: float = 0.5

    cv_enabled: bool = False
    sam_enabled: bool = False

    project_root: str = "projects"
    project_name: str = ""
    _project: Project = PrivateAttr()

    @property
    def project(self) -> Project:
        return self._project

    @project.setter
    def project(self, value: Project):
        self._project = value

    @property
    def project_dir(self) -> Path:
        return self._project.project_dir

    @property
    def project_anno_dir(self) -> Path:
        return self.project_dir / "annos"

    def model_post_init(self, context: Any) -> None:
        projs = [
            p
            for p in Path(self.project_root).glob("*")
            if p.is_dir() and (p.name == self.project_name if self.project_name else True)
        ]
        if projs:
            path = projs[0] / f"{self.project_name}.json"
            self._project = Project.model_validate_json(path.read_text(), strict=True)
        else:
            self._project = Project(id=id_uuid4())
        self._project.key_label = list(self._project.labels.keys())[0]

    @field_validator("host", mode="before")
    @classmethod
    def is_http(cls, value: str) -> str:
        if not value.startswith("http"):
            raise ValueError(f"{value} is not a http url")
        return value

    def save_json(self, path: str):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(ensure_ascii=False, indent=4, exclude={}))
