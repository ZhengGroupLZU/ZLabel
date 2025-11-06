import os

from pyqtgraph.Qt.QtCore import QSettings, Qt, Signal
from pyqtgraph.Qt.QtGui import QColor
from pyqtgraph.Qt.QtWidgets import QColorDialog, QDialog

from zlabel.utils import SettingsKey

from .ui import Ui_DialogSettings


class DialogSettings(QDialog, Ui_DialogSettings):
    sigSettingsChanged = Signal(QSettings)
    sigApplyClicked = Signal()
    sigCancelClicked = Signal()
    sigLoglevelChanged = Signal(str)
    sigColorChanged = Signal(str)

    def __init__(self, path: str = "zlabel.conf", parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self.path = path
        self.format = QSettings.Format.IniFormat
        self.settings = QSettings(path, self.format)
        if not os.path.exists(path):
            self.init_settings()
        else:
            self.load_settings()

        self.init_signals()

    def init_settings(self):
        self.settings.setValue(SettingsKey.HOST.value, "")
        self.settings.setValue(SettingsKey.URL_PREFIX.value, "")
        self.settings.setValue(SettingsKey.USER_NAME.value, "DefaultUser")
        self.settings.setValue(SettingsKey.USER_PWD.value, "")
        self.settings.setValue(SettingsKey.LOGLEVEL.value, "INFO")
        self.settings.setValue(SettingsKey.COLOR.value, "#000000")

        self.settings.setValue(SettingsKey.PROJ_NAME.value, "defaultProject")
        self.settings.setValue(SettingsKey.PROJ_DESCRIP.value, "defaultProject")

    def load_settings(self, path: str | None = None):
        path = path or self.path
        self.settings = QSettings(path, self.format)
        self.ledit_host.setText(str(self.settings.value(SettingsKey.HOST.value, "")))
        self.ledit_urlprefix.setText(str(self.settings.value(SettingsKey.URL_PREFIX.value, "")))
        self.ledit_username.setText(str(self.settings.value(SettingsKey.USER_NAME.value, "")))
        self.ledit_password.setText(str(self.settings.value(SettingsKey.USER_PWD.value, "")))

        self.ledit_projname.setText(str(self.settings.value(SettingsKey.PROJ_NAME.value, "")))
        self.ledit_prjdescrip.setText(str(self.settings.value(SettingsKey.PROJ_DESCRIP.value, "")))

        self.cmbox_loglevel.setCurrentText(
            self.settings.value(SettingsKey.LOGLEVEL.value, type=str)  # type: ignore
        )
        self.set_btn_select_color(str(self.settings.value(SettingsKey.COLOR.value)))

    def apply(self):
        self.sigSettingsChanged.emit(self.settings)
        self.sigApplyClicked.emit()

    def on_settings_changed(self, k: str, v: str | int | float):
        self.settings.setValue(k, v)
        if self.sender() == self.cmbox_loglevel:
            # os.environ["ZLABEL_LOGLEVEL"] = str(v)
            self.sigLoglevelChanged.emit(str(v))
        self.sigSettingsChanged.emit(self.settings)

    def set_btn_select_color(self, color: str):
        self.btn_select_color.setStyleSheet(f"QPushButton {{margin: 3px; background-color : {color};}}")

    def on_btn_select_color_clicked(self):
        _color = str(self.settings.value(SettingsKey.COLOR.value))
        color = QColorDialog.getColor(QColor(_color), self)
        self.on_settings_changed(SettingsKey.COLOR.value, color.name())

        self.set_btn_select_color(color.name())
        self.sigColorChanged.emit(color.name())

    def init_signals(self):
        self.ledit_host.textEdited.connect(lambda v: self.on_settings_changed(SettingsKey.HOST.value, v))
        self.ledit_urlprefix.textEdited.connect(
            lambda v: self.on_settings_changed(SettingsKey.URL_PREFIX.value, v)
        )
        self.ledit_username.textEdited.connect(
            lambda v: self.on_settings_changed(SettingsKey.USER_NAME.value, v)
        )
        self.ledit_password.textEdited.connect(
            lambda v: self.on_settings_changed(SettingsKey.USER_PWD.value, v)
        )

        self.ledit_projname.textEdited.connect(
            lambda v: self.on_settings_changed(SettingsKey.PROJ_NAME.value, v)
        )
        self.ledit_prjdescrip.textEdited.connect(
            lambda v: self.on_settings_changed(SettingsKey.PROJ_DESCRIP.value, v)
        )

        self.btn_select_color.clicked.connect(self.on_btn_select_color_clicked)

        self.btn_apply.clicked.connect(self.apply)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_cancel.clicked.connect(self.sigCancelClicked.emit)

        self.cmbox_loglevel.currentIndexChanged.connect(
            lambda idx: self.on_settings_changed(
                SettingsKey.LOGLEVEL.value, self.cmbox_loglevel.currentText()
            )
        )
