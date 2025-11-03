from qtpy.QtCore import QSettings
from zlabel.utils import SettingsKey


class ZSettings(QSettings):
    def __init__(self, path: str, format_=QSettings.Format.IniFormat):
        super().__init__(path, format_)
        self.root_dir = "."

    @property
    def host(self):
        return str(self.value(SettingsKey.HOST.value, type=str))

    @property
    def url_prefix(self):
        return str(self.value(SettingsKey.URL_PREFIX.value, type=str))

    @property
    def username(self) -> str:
        return self.value(SettingsKey.USER_NAME.value, type=str)  # type: ignore

    @property
    def password(self) -> str:
        return self.value(SettingsKey.USER_PWD.value, type=str)  # type: ignore

    @property
    def project_description(self):
        return str(self.value(SettingsKey.PROJ_DESCRIP.value, type=str))

    @property
    def project_name(self):
        return str(self.value(SettingsKey.PROJ_NAME.value, type=str))

    @property
    def project_path(self):
        return f"{self.project_dir}/{self.project_name}.zproj"

    @property
    def project_dir(self):
        return f"{self.root_dir}/projects/{self.project_name}"

    @property
    def log_level(self):
        return str(self.value(SettingsKey.LOGLEVEL.value, "INFO", type=str))

    @property
    def color(self):
        return str(self.value(SettingsKey.COLOR.value, "#000000", type=str))

    @property
    def fetch_num(self):
        return int(self.value(SettingsKey.FETCH_NUM.value, 100, type=int))  # type: ignore

    @fetch_num.setter
    def fetch_num(self, value: int):
        self.setValue(SettingsKey.FETCH_NUM.value, value)

    @property
    def fetch_finished(self):
        return int(self.value(SettingsKey.FETCH_FINISHED.value, 0, type=int))  # type: ignore

    @fetch_finished.setter
    def fetch_finished(self, value: int):
        self.setValue(SettingsKey.FETCH_FINISHED.value, value)

    @property
    def annotation_type(self):
        """0: rectangle, 1: polygon"""
        return int(self.value(SettingsKey.ANNOTATE_TYPE.value, 0, type=int))  # type: ignore

    @annotation_type.setter
    def annotation_type(self, value: int):
        """0: rectangle, 1: polygon"""
        self.setValue(SettingsKey.ANNOTATE_TYPE.value, value)

    def validate(self) -> bool:
        passed = True
        if not self.host.startswith("http") or self.username == "":
            passed = False
        return passed
