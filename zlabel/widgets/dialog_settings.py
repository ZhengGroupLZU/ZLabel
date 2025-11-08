from collections import OrderedDict

from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtGui import QColor, QIcon, QStandardItem
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

        self.ledit_projname.setText(str(self.settings.project_name))
        self.ledit_prjdesc.setText(str(self.settings.project_desc))

        self.cmbox_loglevel.setCurrentIndex(self.settings.log_level.value)

        self.set_labels(self.settings.labels)

    def apply(self):
        self.sigSettingsChanged.emit()
        self.sigApplyClicked.emit()

    def init_signals(self):
        # here the k passed to on_settings_changed is the attribute name in ZSettings
        self.ledit_host.textEdited.connect(lambda v: self.on_settings_changed("host", v))
        self.ledit_username.textEdited.connect(lambda v: self.on_settings_changed("username", v))
        self.ledit_password.textEdited.connect(lambda v: self.on_settings_changed("password", v))

        self.ledit_projname.textEdited.connect(
            lambda v: self.on_settings_changed("project_name", v)
        )
        self.ledit_prjdesc.textEdited.connect(lambda v: self.on_settings_changed("project_desc", v))

        # Track edits in the labels table
        self.table_labels.itemChanged.connect(self.on_table_labels_item_changed)

        self.btn_apply.clicked.connect(self.apply)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_cancel.clicked.connect(self.sigCancelClicked.emit)

        self.cmbox_loglevel.currentIndexChanged.connect(
            lambda idx: self.on_settings_changed("log_level", idx)
        )

    def on_settings_changed(self, k: str, v: str | int | float):
        assert self.settings is not None
        if k == "host":
            self.settings.host = str(v)
        elif k == "username":
            self.settings.username = str(v)
        elif k == "password":
            self.settings.password = str(v)
        elif k == "project_name":
            self.settings.project_name = str(v)
        elif k == "project_desc":
            self.settings.project_desc = str(v)
        elif k == "log_level":
            loglevel = LogLevel(int(v))
            self.settings.log_level = loglevel
        else:
            raise ValueError(f"Unknown setting key: {k}")
        self.sigSettingsChanged.emit()

    def on_table_labels_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            # ID
            label_id = item.text()
            label_name = self.table_labels.item(item.row(), 1).text()
            self.settings.labels[label_id].name = label_name

    def set_labels(self, labels: dict[str, Label]):
        self.table_labels.setRowCount(0)
        for idx, label in enumerate(labels.values()):
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
            self.table_labels.setCellWidget(idx, 2, btn_select_color)

            # delete
            btn_delete = QPushButton("Delete")
            btn_delete.setIcon(QIcon(":/icon/icons/delete-3.svg"))
            self.table_labels.setCellWidget(idx, 3, btn_delete)
