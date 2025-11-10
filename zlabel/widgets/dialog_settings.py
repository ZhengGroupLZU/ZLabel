from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtGui import QColor, QIcon
from pyqtgraph.Qt.QtWidgets import QColorDialog, QDialog, QPushButton, QTableWidgetItem

from zlabel.utils import id_uuid4
from zlabel.utils.enums import LogLevel
from zlabel.utils.project import Label
from zlabel.widgets.zsettings import ZSettings

from .ui import Ui_DialogSettings


class DialogSettings(QDialog, Ui_DialogSettings):
    sigSettingsChanged = Signal()
    sigApplyClicked = Signal()
    sigCancelClicked = Signal()

    def __init__(
        self,
        settings: ZSettings | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self.settings: ZSettings | None = settings
        self.table_labels.setHorizontalHeaderLabels(["ID", "Name", "Color", "Delete"])
        self.table_labels.setRowCount(0)

        if self.settings:
            self.load_settings()
        self.init_signals()

    def load_settings(self, settings: ZSettings | None = None):
        self.settings = settings or self.settings
        assert self.settings is not None

        self.ledit_host.setText(str(self.settings.host))
        self.ledit_username.setText(str(self.settings.username))
        self.ledit_password.setText(str(self.settings.password))
        self.dspbox_alpha.setValue(self.settings.alpha)

        self.cmbox_loglevel.setCurrentIndex(self.settings.log_level.value)

        self.set_labels(self.settings.project.labels)
        self.ledit_projname.setText(str(self.settings.project.name))
        self.ledit_prjdesc.setText(str(self.settings.project.description))

    def init_signals(self):
        # here the k passed to on_settings_changed is the attribute name in ZSettings
        self.ledit_host.textEdited.connect(lambda v: self.on_settings_changed("host", v))
        self.ledit_username.textEdited.connect(lambda v: self.on_settings_changed("username", v))
        self.ledit_password.textEdited.connect(lambda v: self.on_settings_changed("password", v))
        self.dspbox_alpha.valueChanged.connect(lambda v: self.on_settings_changed("alpha", v))

        self.ledit_projname.textEdited.connect(lambda v: self.on_settings_changed("project_name", v))
        self.ledit_prjdesc.textEdited.connect(lambda v: self.on_settings_changed("project_desc", v))

        # Track edits in the labels table
        self.table_labels.itemChanged.connect(self.on_table_labels_item_changed)

        self.btn_apply.clicked.connect(self.sigSettingsChanged.emit)
        self.btn_apply.clicked.connect(self.sigApplyClicked.emit)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_cancel.clicked.connect(self.sigCancelClicked.emit)

        self.btn_add_label.clicked.connect(self.on_btn_label_add_clicked)
        self.btn_delete_label.clicked.connect(self.on_btn_label_delete_clicked)
        self.btn_clear.clicked.connect(self.on_btn_label_clear_clicked)

        self.cmbox_loglevel.currentIndexChanged.connect(lambda idx: self.on_settings_changed("log_level", idx))

    def on_settings_changed(self, k: str, v: str | int | float):
        assert self.settings is not None
        if k == "host":
            self.settings.host = str(v)
        elif k == "username":
            self.settings.username = str(v)
        elif k == "password":
            self.settings.password = str(v)
        elif k == "alpha":
            self.settings.alpha = float(v)
        elif k == "project_name":
            self.settings.project.name = str(v)
            self.settings.project_name = str(v)
        elif k == "project_desc":
            self.settings.project.description = str(v)
        elif k == "log_level":
            self.settings.log_level = LogLevel(int(v))
        else:
            raise ValueError(f"Unknown setting key: {k}")
        self.sigSettingsChanged.emit()

    def on_table_labels_item_changed(self, item: QTableWidgetItem):
        if self.settings is None or item.column() == 0:
            return
        # ID
        item_id = self.table_labels.item(item.row(), 0)
        label_id = item_id.text().strip() if item_id else ""
        if not label_id:
            return

        # Name
        if item.column() == 1:
            label_name = item.text().strip()
            self.settings.project.labels[label_id].name = label_name
        # Color
        elif item.column() == 2:
            color = QColor(item.background().color())
            self.settings.project.labels[label_id].color = color.name()

    def on_btn_label_add_clicked(self):
        if self.settings is None:
            return

        label_id = id_uuid4()
        self.settings.project.labels[label_id] = Label(id=label_id, name="")
        self.add_row(self.settings.project.labels[label_id])

    def on_btn_label_delete_clicked(self):
        if self.settings is None:
            return

        selected_items = self.table_labels.selectedItems()
        selected_rows = list({item.row() for item in selected_items})
        selected_rows.sort(reverse=True)
        for row in selected_rows:
            self.table_labels.removeRow(row)
            label_item = self.table_labels.item(row, 0)
            if label_item:
                label_id = label_item.text().strip()
                self.settings.project.labels.pop(label_id, None)

    def on_btn_label_clear_clicked(self):
        if self.settings is None:
            return

        self.settings.project.labels.clear()
        self.table_labels.setRowCount(0)

    def add_row(self, label: Label, row: int | None = None):
        def btn_item_select_color_clicked(btn: QPushButton, label_id: str):
            color = QColorDialog.getColor()
            if color.isValid():
                btn.setStyleSheet(f"background-color: {color.name()}")
                btn.setText(color.name().upper())
                if self.settings is not None:
                    self.settings.project.labels[label_id].color = color.name()

        def btn_item_delete_clicked(label_id: str):
            if self.settings is None:
                return

            self.settings.project.labels.pop(label_id, None)
            for row in range(self.table_labels.rowCount()):
                item = self.table_labels.item(row, 0)
                if item and item.text().strip() == label_id:
                    self.table_labels.removeRow(row)
                    break

        idx = row or self.table_labels.rowCount()
        self.table_labels.insertRow(idx)

        # ID
        self.table_labels.setItem(idx, 0, QTableWidgetItem(label.id))
        item = self.table_labels.item(idx, 0)
        if item:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # name
        self.table_labels.setItem(idx, 1, QTableWidgetItem(label.name))

        # color
        btn_select_color = QPushButton("Select Color")
        btn_select_color.setStyleSheet(f"background-color: {label.color}")
        btn_select_color.setText(label.color.upper())
        btn_select_color.clicked.connect(lambda: btn_item_select_color_clicked(btn_select_color, label.id))
        self.table_labels.setCellWidget(idx, 2, btn_select_color)

        # delete
        btn_delete = QPushButton("Delete")
        btn_delete.setIcon(QIcon(":/icon/icons/delete-3.svg"))
        btn_delete.clicked.connect(lambda: btn_item_delete_clicked(label.id))
        self.table_labels.setCellWidget(idx, 3, btn_delete)

    def set_labels(self, labels: dict[str, Label]):
        self.table_labels.setRowCount(0)
        for idx, label in enumerate(labels.values()):
            self.add_row(label, idx)
