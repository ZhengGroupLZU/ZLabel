from functools import partial

from pyqtgraph.Qt.QtCore import Signal
from pyqtgraph.Qt.QtWidgets import QWidget

from zlabel.utils import Label
from zlabel.widgets.zwidgets import ZLabelItemWidget, ZListWidgetItem

from .ui import Ui_ZDockLabelContent


class ZDockLabelContent(QWidget, Ui_ZDockLabelContent):
    sigItemColorChanged = Signal(str, str)
    sigItemClicked = Signal(str)  # id
    sigItemDoubleClicked = Signal(str)  # id

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setupUi(self)

        self.listw_labels.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.listw_labels.itemClicked.connect(self.on_item_clicked)

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

    def add_label(self, label: Label | None, index: int | None = None):
        if label is None:
            return
        btn_text = str(index + 1) if isinstance(index, int) else ""
        item = ZListWidgetItem(label.id, "", self.listw_labels)
        item_widget = ZLabelItemWidget(label.id, label.name, label.color, btn_text=btn_text)
        item_widget.sigColorChanged.connect(self.on_item_color_changed)
        item_widget.sigSelected.connect(partial(self.select_row_by_id, label.id))
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
