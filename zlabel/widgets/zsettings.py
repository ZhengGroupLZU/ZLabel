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

    projects: list[tuple[int, str]] = []
    project_root: str = "projects"
    project_idx: int = -1
    _project: Project = PrivateAttr()

    @property
    def project_id(self) -> int:
        if self.project_idx < 0 or self.project_idx >= len(self.projects):
            return -1
        return self.projects[self.project_idx][0]

    @property
    def project_name(self) -> str:
        if self.project_idx < 0 or self.project_idx >= len(self.projects):
            return ""
        return self.projects[self.project_idx][1]

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

    def reload_project(self):
        projs = [
            p
            for p in Path(self.project_root).glob("*")
            if p.is_dir() and (p.name == self.project_name if self.project_name else True)
        ]
        self._project = Project(id=id_uuid4())
        if projs:
            path = projs[0] / f"{self.project_name}.json"
            if path.exists() and path.is_file():
                self._project = Project.model_validate_json(path.read_text(), strict=True)
        else:
            project_dir = Path(self.project_root) / self.project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            self._project.name = self.project_name
            self._project.save_json(project_dir / f"{self.project_name}.json")
        labels = list(self._project.labels.keys())
        if labels:
            self._project.key_label = labels[0]

    def model_post_init(self, context: Any) -> None:
        self.reload_project()

    @field_validator("host", mode="before")
    @classmethod
    def is_http(cls, value: str) -> str:
        # Allow empty host so users can configure it later in Settings.
        # When non-empty, it must be a valid http(s) URL.
        if not value:
            return value
        if not str(value).startswith("http"):
            raise ValueError(f"{value} is not a http url")
        return str(value)

    def save_json(self, path: str):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(ensure_ascii=False, indent=4, exclude={}))
