from pathlib import Path
import os
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from .ui import Ui_DialogNewProject


class DialogNewProject(QDialog, Ui_DialogNewProject):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self._default_proj_path: str | None = None

        self.btn_select_path.clicked.connect(self.on_btn_select_path_clicked)
        self.btn_reset_proj_name.clicked.connect(lambda: self.ledit_proj_name.setText("NewProject"))
        self.btn_reset_proj_descrip.clicked.connect(lambda: self.ledit_descrip.setText("NewProject"))
        self.btn_reset_user_name.clicked.connect(lambda: self.ledit_user_name.setText("DefaultUser"))
        self.btn_reset_user_email.clicked.connect(lambda: self.ledit_user_email.setText("DefaultUser@zlabel.group"))

        self.ledit_path.textChanged.connect(self.on_ledit_path_text_changed)

        self.btn_ok = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel)

    def on_ledit_path_text_changed(self):
        text = self.ledit_path.text()
        path = Path(text)
        if not path.exists():
            path.mkdir(parents=True)

        self.ledit_proj_name.setText(path.name)
        self.ledit_descrip.setText(path.name)

    def on_btn_select_path_clicked(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Open Directory",
            ".",
        )
        path = Path(directory)
        if path.exists():
            self.ledit_path.setText(directory)

    @property
    def proj_name(self):
        return self.ledit_proj_name.text() or "NewProject"

    @property
    def proj_path(self):
        path = Path(self.ledit_path.text())
        assert path.exists()
        return self.ledit_path.text()

    @property
    def proj_description(self):
        return self.ledit_descrip.text() or "NewProject"

    @property
    def proj_user_name(self):
        return self.ledit_user_name.text() or "DefaultUser"

    @property
    def proj_user_email(self):
        return self.ledit_user_email.text() or "DefaultUser@zlabel.group"

    @property
    def default_proj_path(self):
        return self._default_proj_path

    @default_proj_path.setter
    def default_proj_path(self, path: str | None):
        self._default_proj_path = path
        self.ledit_path.setText(path)
