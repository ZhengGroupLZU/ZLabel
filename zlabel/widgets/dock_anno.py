from collections import OrderedDict
import copy
import functools
import re
from typing import List, Optional, TypeAlias, TypeVar, NewType

from qtpy.QtWidgets import (
    QCheckBox,
    QWidget,
    QListWidgetItem,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QDockWidget,
)
from qtpy.QtCore import Slot, Qt, QSize, QPoint, QRectF, Signal

from qtpy.QtGui import QKeyEvent

from zlabel.utils.project import Annotation, Project, Result
from zlabel.widgets.zwidgets import ZListWidgetItem

from .ui import Ui_ZDockAnnotationContent


class ZDockAnnotationContent(QWidget, Ui_ZDockAnnotationContent):
    sigItemDeleted = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.items: List[str] = []

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            items: List[ZListWidgetItem] = self.listWidget.selectedItems()  # type: ignore
            self.sigItemDeleted.emit([it.id_ for it in items])
        return super().keyPressEvent(event)

    def set_row_by_text(self, s: str | None):
        if s is None:
            return
        for row in range(self.listWidget.count()):
            if self.listWidget.item(row).text() == s:
                self.listWidget.setCurrentRow(row)
                return

    def remove_item(self, id_: str):
        for row in range(self.listWidget.count()):
            if self.listWidget.item(row).text() == id_:
                self.listWidget.takeItem(row)
                self.listWidget.setCurrentRow(row - 1)
                break

    def remove_items(self, ids: List[str]):
        for row in range(self.listWidget.count()):
            if self.listWidget.item(row).id_ in ids:  # type: ignore
                self.listWidget.takeItem(row)
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)

    def add_item(self, id_: str):
        if id_ in self.items:
            return
        item = ZListWidgetItem(id_, id_, self.listWidget)
        item.setSelected(False)
        self.listWidget.addItem(item)
        self.listWidget.clearSelection()
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        self.items.append(id_)

    def add_items(self, ids: List[str]):
        for id_ in ids:
            self.add_item(id_)

    def clear_items(self):
        self.items.clear()
        self.listWidget.clear()
        self.listWidget.setCurrentRow(-1)

    def add_items_by_anno(self, anno: Annotation | None):
        if anno is None:
            return
        self.clear_items()
        self.add_items(list(anno.results.keys()))
