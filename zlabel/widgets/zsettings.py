from collections import OrderedDict

from pydantic import BaseModel, field_validator

from zlabel.utils.enums import AnnotationType, FetchType, LogLevel
from zlabel.utils.project import Label


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

    cv_enabled: bool = False
    sam_enabled: bool = False

    project_name: str = "defaultProject"
    project_desc: str = "defaultProject"

    labels: OrderedDict[str, Label] = OrderedDict()

    @property
    def project_path(self):
        return f"{self.project_dir}/{self.project_name}.zproj"

    @property
    def project_dir(self):
        return f"{self.root_dir}/projects/{self.project_name}"

    @field_validator("host", mode="before")
    @classmethod
    def is_http(cls, value: str) -> str:
        if not value.startswith("http"):
            raise ValueError(f"{value} is not a http url")
        return value
