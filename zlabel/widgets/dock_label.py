from functools import partial

from pyqtgraph.Qt.QtCore import Signal
from pyqtgraph.Qt.QtWidgets import QButtonGroup, QTabWidget, QVBoxLayout, QWidget

from zlabel.utils import Label
from zlabel.widgets.dock_anno import humanize_status
from zlabel.widgets.zwidgets import ZInstanceItemWidget, ZLabelItemWidget, ZListWidget, ZListWidgetItem

from .ui import Ui_ZDockLabelContent


class ZDockLabelContent(QWidget, Ui_ZDockLabelContent):
    sigItemColorChanged = Signal(str, str)
    sigItemClicked = Signal(str)  # id
    sigItemDoubleClicked = Signal(str)  # id
    sigItemVisibilityToggled = Signal(str)  # id
    sigInstanceVisibilityToggled = Signal(str)  # instance status
    sigDefaultInstanceSelected = Signal(str)  # instance status

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setupUi(self)

        self.listw_labels.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.listw_labels.itemClicked.connect(self.on_item_clicked)

        # Labels panel -> two tabs: Labels (all labels) / Instance (statuses)
        self.tab_widget = QTabWidget()
        self.tab_labels = QWidget()
        self.tab_instance = QWidget()
        lay_labels = QVBoxLayout(self.tab_labels)
        lay_labels.setContentsMargins(0, 0, 0, 0)
        lay_labels.addWidget(self.listw_labels)
        self.listw_instances = ZListWidget()
        self.listw_instances.itemClicked.connect(self.on_instance_item_clicked)
        lay_instance = QVBoxLayout(self.tab_instance)
        lay_instance.setContentsMargins(0, 0, 0, 0)
        lay_instance.addWidget(self.listw_instances)
        self.tab_widget.addTab(self.tab_labels, self.tr("Labels"))
        self.tab_widget.addTab(self.tab_instance, self.tr("Instance"))
        self.verticalLayout.removeWidget(self.listw_labels)
        self.verticalLayout.addWidget(self.tab_widget)

        self._instance_visibility: dict[str, bool] = {}
        self._instance_widgets: dict[str, ZInstanceItemWidget] = {}
        self._radio_group = QButtonGroup(self)
        self._radio_group.setExclusive(True)

    def on_item_clicked(self, item: ZListWidgetItem):
        self.sigItemClicked.emit(item.id_)

    def find_item_by_id(
        self,
        id_: str,
    ) -> tuple[int, ZListWidgetItem] | tuple[None, None]:
        for row in range(self.listw_labels.count()):
            item = self.listw_labels.item(row)
            if isinstance(item, ZListWidgetItem) and item.id_ == id_:
                return row, item
        return None, None

    def on_item_double_clicked(self, item: ZListWidgetItem):
        self.sigItemDoubleClicked.emit(item.id_)

    def set_color(self, color: str):
        for row in range(self.listw_labels.count()):
            item = self.listw_labels.item(row)
            if not isinstance(item, ZListWidgetItem):
                continue
            widget = self.listw_labels.itemWidget(item)
            if isinstance(widget, ZLabelItemWidget):
                widget.set_label_color(color)

    def on_item_color_changed(self, id_: str):
        row, item = self.find_item_by_id(id_)
        if row is not None and item is not None:
            widget = self.listw_labels.itemWidget(item)
            if isinstance(widget, ZLabelItemWidget):
                self.sigItemColorChanged.emit(id_, widget.color)

    def on_instance_item_clicked(self, item):
        """Clicking an Instance-tab row selects its radio button."""
        if not isinstance(item, ZListWidgetItem):
            return
        widget = self.listw_instances.itemWidget(item)
        if isinstance(widget, ZInstanceItemWidget):
            widget.radio.setChecked(True)

    def set_instance_statuses(self, statuses: list[str] | None, selected_status: str = ""):
        """Populate the Instance tab with one row per instance status."""
        self.listw_instances.clear()
        self._instance_widgets.clear()
        self._radio_group = QButtonGroup(self)
        self._radio_group.setExclusive(True)
        for val in statuses or []:
            item = ZListWidgetItem(val, "", self.listw_instances)
            widget = ZInstanceItemWidget(val, humanize_status(val))
            widget.set_visible_state(self._instance_visibility.get(val, True))
            widget.sigVisibilityToggled.connect(self.sigInstanceVisibilityToggled.emit)
            widget.sigDefaultSelected.connect(self.sigDefaultInstanceSelected.emit)
            self._radio_group.addButton(widget.radio)
            self.listw_instances.addItem(item)
            self.listw_instances.setItemWidget(item, widget)
            self._instance_widgets[val] = widget
            if val == selected_status:
                widget.radio.setChecked(True)

    def set_default_instance_status(self, status: str):
        """Check the radio of the given instance status ('' unchecks all)."""
        for val, widget in self._instance_widgets.items():
            widget.radio.blockSignals(True)
            widget.radio.setChecked(val == status)
            widget.radio.blockSignals(False)

    def default_instance_status(self) -> str:
        for val, widget in self._instance_widgets.items():
            if widget.radio.isChecked():
                return val
        return ""

    def set_instance_visibility_state(self, status: str, visible: bool):
        widget = self._instance_widgets.get(status)
        if widget is not None:
            widget.set_visible_state(visible)

    def update_instance_visibility_buttons(self, visibility: dict[str, bool] | None = None):
        if visibility is not None:
            self._instance_visibility = dict(visibility)
        for val, widget in self._instance_widgets.items():
            widget.set_visible_state(self._instance_visibility.get(val, True))

    def add_label(self, label: Label | None, index: int | None = None):
        if label is None:
            return
        btn_text = str(index + 1) if isinstance(index, int) else ""
        item = ZListWidgetItem(label.id, "", self.listw_labels)
        item_widget = ZLabelItemWidget(label.id, label.name, label.color, btn_text=btn_text)
        item_widget.sigColorChanged.connect(self.on_item_color_changed)
        item_widget.sigSelected.connect(partial(self.select_row_by_id, label.id))
        item_widget.sigVisibilityToggled.connect(self.sigItemVisibilityToggled.emit)
        if index is None:
            self.listw_labels.addItem(item)
        else:
            self.listw_labels.insertItem(index, item)
        self.listw_labels.setItemWidget(item, item_widget)

    def remove_label(self, row: int | str | None = None):
        if isinstance(row, str):
            row, _ = self.find_item_by_id(row)
        if row is None:
            return
        row = row or self.listw_labels.currentRow()
        if row < 0 or row > self.listw_labels.count():
            return
        self.listw_labels.takeItem(row)

    def set_labels(self, labels: list[Label] | None, selected_id: str | None = None):
        if labels is None:
            return
        self.listw_labels.clear()
        if len(labels) == 0:
            return
        row = -1
        for i, label in enumerate(labels):
            self.add_label(label, i)
            if label.id == selected_id:
                row = i
        if row >= 0:
            self.listw_labels.setCurrentRow(row)
            item = self.listw_labels.currentItem()
            if isinstance(item, ZListWidgetItem):
                self.sigItemClicked.emit(item.id_)

    def select_row_by_id(self, id_: str):
        row, item = self.find_item_by_id(id_)
        if row is not None:
            self.listw_labels.setCurrentRow(row)
            if isinstance(item, ZListWidgetItem):
                self.sigItemClicked.emit(item.id_)
        else:
            self.listw_labels.setCurrentRow(-1)

    def select_row(self, row: int):
        if row < 0 or row >= self.listw_labels.count():
            return
        self.listw_labels.setCurrentRow(row)
        item = self.listw_labels.item(row)
        if isinstance(item, ZListWidgetItem):
            self.sigItemClicked.emit(item.id_)
