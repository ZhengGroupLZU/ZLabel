import functools
import re
from typing import List, Optional, TypeAlias, TypeVar, NewType

from qtpy.QtWidgets import (
    QCheckBox,
    QWidget,
    QListWidgetItem,
    QHBoxLayout,
    QLabel,
    QDockWidget,
)
from qtpy.QtGui import QIntValidator
from qtpy.QtCore import Slot, Qt, Signal

from zlabel.utils.logger import ZLogger
from zlabel.widgets.zwidgets import ZListWidgetItem

from .ui import Ui_ZDockFileContent
from ..utils.project import Project, id_md5


class ZDockFileContent(QWidget, Ui_ZDockFileContent):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.logger = ZLogger("ZDockFileContent")
        self.ledit_jump.setValidator(QIntValidator(1, 999999, self.ledit_jump))
        self.listw_files.itemClicked.connect(lambda it: self.update_labels())

    def get_row_txt(self, row: int):
        if row < 0 or row >= self.listw_files.count():
            return
        return self.listw_files.item(row).text()

    def update_file_list(self, paths: List[str]|None=None):
        if paths is None:
            return
        self.listw_files.clear()
        for p in paths:
            self.listw_files.addItem(ZListWidgetItem(id_md5(p), p, self.listw_files))
        self.listw_files.setCurrentRow(0)
        self.update_labels()

    def update_labels(self):
        row = self.listw_files.currentRow()
        self.label_all.setText(f"{self.listw_files.count()}")
        self.label_current.setText(f"{row+1}")
        self.ledit_jump.setText(f"{row+1}")

