from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtGui import QIntValidator
from pyqtgraph.Qt.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from zlabel.utils import Task, ZLogger
from zlabel.widgets.zwidgets import ZTableWidgetItem

from .ui import Ui_ZDockFileContent


class ZDockFileContent(QWidget, Ui_ZDockFileContent):
    sigItemClicked = Signal(str)
    sigFetchTasks = Signal(int, int, int)  # project_id, fetch_num, fetch_finished
    sigStorageChanged = Signal(str)  # "remote" or "local"
    sigLocalDirChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.logger = ZLogger("ZDockFileContent")

        self.ledit_jump.setValidator(QIntValidator(1, 999999, self.ledit_jump))
        self.ledit_jump.editingFinished.connect(self.on_ledit_jump_changed)

        self.table_files.itemClicked.connect(lambda it: self.set_qlabels())
        self.table_files.itemClicked.connect(lambda it: self.sigItemClicked.emit(it.id_))
        self.table_files.setWordWrap(True)
        self.table_files.setTextElideMode(Qt.TextElideMode.ElideLeft)

        self.btn_fetch.clicked.connect(self.on_btn_fetch_clicked)

        self.ckbox_finished.checkStateChanged.connect(self.on_ckbox_finished_state_changed)

        self.cmbox_storage = QComboBox(self)
        self.cmbox_storage.addItems(["Remote", "Local"])
        self.cmbox_storage.setToolTip("Storage backend for the current project")
        self.cmbox_storage.currentTextChanged.connect(self.on_cmbox_storage_changed)

        self.ledit_local_dir = QLineEdit(self)
        self.ledit_local_dir.setPlaceholderText("Local images folder (optional)")
        self.btn_local_dir = QPushButton(self.tr("Browse..."), self)
        self.btn_local_dir.clicked.connect(self.on_btn_local_dir_clicked)

        hbox_storage = QHBoxLayout()
        hbox_storage.addWidget(QLabel(self.tr("Storage:")))
        hbox_storage.addWidget(self.cmbox_storage)
        hbox_local_dir = QHBoxLayout()
        hbox_local_dir.addWidget(self.ledit_local_dir, 1)
        hbox_local_dir.addWidget(self.btn_local_dir)
        vbox_storage = QVBoxLayout()
        vbox_storage.addLayout(hbox_storage)
        vbox_storage.addLayout(hbox_local_dir)
        self.gridLayout.addLayout(vbox_storage, 2, 0, 1, 3)
        self.update_local_dir_visible()

    def set_cmbox_projects(self, list_projects: list[str]):
        self.cmbox_project.clear()
        self.cmbox_project.addItems(list_projects)

    def set_storage_mode(self, mode: str):
        idx = 0 if mode == "remote" else 1
        if self.cmbox_storage.currentIndex() != idx:
            self.cmbox_storage.setCurrentIndex(idx)
        self.update_local_dir_visible()

    def on_cmbox_storage_changed(self, text: str):
        self.update_local_dir_visible()
        self.sigStorageChanged.emit(text.lower())

    def update_local_dir_visible(self):
        is_local = self.cmbox_storage.currentIndex() == 1
        self.ledit_local_dir.setVisible(is_local)
        self.btn_local_dir.setVisible(is_local)

    def set_local_dir(self, path: str):
        self.ledit_local_dir.setText(path)

    def on_btn_local_dir_clicked(self):
        d = QFileDialog.getExistingDirectory(self, self.tr("Select local images folder"))
        if not d:
            return
        self.ledit_local_dir.setText(d)
        self.sigLocalDirChanged.emit(d)

    def on_ckbox_finished_state_changed(self, state: Qt.CheckState):
        if state == Qt.CheckState.Checked:
            self.ckbox_finished.setText("Finished")
        elif state == Qt.CheckState.Unchecked:
            self.ckbox_finished.setText("Unfinished")
        elif state == Qt.CheckState.PartiallyChecked:
            self.ckbox_finished.setText("All")
        else:
            ...

    def on_btn_fetch_clicked(self):
        project_id = -1
        if self.cmbox_project.count() > 0:
            project_id = self.cmbox_project.currentIndex()
        fetch_finished = 0
        try:
            if self.cbox_fetch_num.currentIndex() == self.cbox_fetch_num.count() - 1:
                num = 0x3F3F3F
            else:
                num = int(self.cbox_fetch_num.currentText())
            if self.ckbox_finished.checkState() == Qt.CheckState.Checked:
                fetch_finished = 1
            elif self.ckbox_finished.checkState() == Qt.CheckState.PartiallyChecked:
                fetch_finished = -1
        except Exception as e:
            num = 100
            self.logger.warning(f"fetch num error: {e}, using default: {num}")
        self.sigFetchTasks.emit(project_id, num, fetch_finished)

    def on_ledit_jump_changed(self):
        try:
            s = self.ledit_jump.text()
            row = int(s) - 1
            item: ZTableWidgetItem = self.table_files.item(row, 1)  # type: ignore
            self.table_files.setCurrentCell(row, 0)
            self.sigItemClicked.emit(item.id_)
        except Exception:
            ...

    def get_row_txt(self, row: int):
        if row < 0 or row >= self.table_files.rowCount():
            return
        item = self.table_files.item(row, 1)
        if item:
            return item.text()

    def set_row_by_txt(self, s: str | None):
        if s is None:
            return
        for row in range(self.table_files.rowCount()):
            item: ZTableWidgetItem = self.table_files.item(row, 1)  # type: ignore
            if item.id_ == s:
                self.table_files.setCurrentCell(row, 0)
                return

    def set_file_list(self, tasks: list[Task] | None = None):
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
            filename = task.filename.split("/")[-1]
            self.table_files.setItem(
                row,
                1,
                ZTableWidgetItem(task.anno_id, filename, finished=task.finished),
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
        self.label_current.setText(f"{row + 1}")
        self.ledit_jump.setText(f"{row + 1}")

    def currentRow(self):
        return self.table_files.currentRow()

    def count(self):
        return self.table_files.rowCount()

    def setCurrentRow(self, row: int):
        self.table_files.setCurrentCell(row, 0)

    def getItem(self, row: int) -> ZTableWidgetItem:
        return self.table_files.item(row, 1)  # type: ignore

    def get_current_task_id(self) -> str:
        row = self.currentRow()
        if row < 0 or row >= self.table_files.rowCount():
            return ""
        item: ZTableWidgetItem = self.table_files.item(row, 0)  # type: ignore
        return item.text()

    def set_fetch_num_idx_by_value(self, num: int):
        for i in range(self.cbox_fetch_num.count()):
            text = self.cbox_fetch_num.itemText(i).lower()
            if text == str(num) or text == "all":
                self.cbox_fetch_num.setCurrentIndex(i)
                return
