import functools
import re
import sys
from typing import List, Optional, TypeAlias, TypeVar, NewType

from qtpy.QtWidgets import (
    QCheckBox,
    QWidget,
    QListWidgetItem,
    QHBoxLayout,
    QLabel,
    QDockWidget,
)
from qtpy.QtGui import QIntValidator, QColor, QMouseEvent
from qtpy.QtCore import Slot, Qt, Signal

from zlabel.utils import ZLogger, Task, id_md5
from zlabel.widgets import ZListWidget, ZListWidgetItem, ZTableWidgetItem

from .ui import Ui_ZDockFileContent


class ZDockFileContent(QWidget, Ui_ZDockFileContent):
    sigItemClicked = Signal(str)
    sigFetchTasks = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.logger = ZLogger("ZDockFileContent")
        self.ledit_jump.setValidator(QIntValidator(1, 999999, self.ledit_jump))
        self.table_files.itemClicked.connect(lambda it: self.set_qlabels())
        self.table_files.itemClicked.connect(lambda it: self.sigItemClicked.emit(it.id_))
        self.ledit_jump.editingFinished.connect(self.on_ledit_jump_changed)
        self.btn_fetch.clicked.connect(self.on_btn_fetch_clicked)

    def on_btn_fetch_clicked(self):
        fetch_finished = 0
        try:
            if self.cbox_fetch_num.currentIndex() == self.cbox_fetch_num.count() - 1:
                num = 0x3f3f3f
            else:
                num = int(self.cbox_fetch_num.currentText())
            if self.ckbox_finished.checkState() == Qt.CheckState.Checked:
                fetch_finished = 1
            elif self.ckbox_finished.checkState() == Qt.CheckState.PartiallyChecked:
                fetch_finished = -1
        except Exception as e:
            num = 100
            self.logger.warning(f"fetch num error: {e}, using default: {num}")
        self.sigFetchTasks.emit(num, fetch_finished)

    def on_ledit_jump_changed(self):
        try:
            s = self.ledit_jump.text()
            row = int(s) - 1
            item = self.table_files.item(row, 1)
            self.table_files.setCurrentCell(row, 0)
            self.sigItemClicked.emit(item)
        except Exception as e:
            ...

    def get_row_txt(self, row: int):
        if row < 0 or row >= self.table_files.rowCount():
            return
        return self.table_files.item(row, 1).text()

    def set_row_by_txt(self, s: str | None):
        if s is None:
            return
        for row in range(self.table_files.rowCount()):
            item: ZTableWidgetItem = self.table_files.item(row, 1)  # type: ignore
            if item.id_ == s:
                self.table_files.setCurrentCell(row, 0)
                return

    def set_file_list(self, tasks: List[Task] | None = None):
        if tasks is None:
            return
        self.table_files.clear()
        self.table_files.setHorizontalHeaderLabels(["id", "name"])
        self.table_files.setRowCount(len(tasks))
        row = 0
        for task in tasks:
            self.table_files.setItem(
                row,
                0,
                ZTableWidgetItem(task.anno_id, task.anno_id, finished=task.finished),
            )
            self.table_files.setItem(
                row,
                1,
                ZTableWidgetItem(task.anno_id, task.filename, finished=task.finished),
            )
            row += 1

        self.table_files.setCurrentCell(0, 0)
        self.set_qlabels()

    def set_item_finished(self, task: Task):
        if task is None:
            return
        for row in range(self.table_files.rowCount()):
            item: ZTableWidgetItem = self.table_files.item(row, 1)  # type: ignore
            if item.id_ == task.anno_id:
                item.set_finished()
                self.table_files.item(row, 0).set_finished()  # type: ignore
                return

    def set_item_unfinished(self, task: Task):
        if task is None:
            return
        for row in range(self.table_files.rowCount()):
            item: ZTableWidgetItem = self.table_files.item(row, 1)  # type: ignore
            if item.id_ == task.anno_id:
                item.set_unfinished()
                self.table_files.item(row, 0).set_unfinished()  # type: ignore
                return

    def set_qlabels(self):
        row = self.table_files.currentRow()
        self.label_all.setText(f"{self.table_files.rowCount()}")
        self.label_current.setText(f"{row+1}")
        self.ledit_jump.setText(f"{row+1}")

    def currentRow(self):
        return self.table_files.currentRow()

    def count(self):
        return self.table_files.rowCount()

    def setCurrentRow(self, row: int):
        self.table_files.setCurrentCell(row, 0)

    def getItem(self, row: int) -> ZTableWidgetItem:
        return self.table_files.item(row, 1)  # type: ignore

    def get_current_task_name(self) -> str:
        row = self.currentRow()
        if row < 0 or row >= self.table_files.rowCount():
            return ""
        item: ZTableWidgetItem = self.table_files.item(row, 1)  # type: ignore
        return item.text()

    def get_current_task_id(self) -> str:
        row = self.currentRow()
        if row < 0 or row >= self.table_files.rowCount():
            return ""
        item: ZTableWidgetItem = self.table_files.item(row, 0)  # type: ignore
        return item.text()
