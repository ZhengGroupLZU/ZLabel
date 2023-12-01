# -*- coding: utf-8 -*-

from typing import List, Tuple
from qtpy.QtCore import Qt, QSize, Signal, Slot
from qtpy.QtWidgets import QWidget

from zlabel.widgets.zwidgets import ZLabelItemWidget, ZListWidgetItem
from .ui import Ui_ZDockLabelContent
from ..utils.project import Label


class ZDockLabelContent(QWidget, Ui_ZDockLabelContent):
    sigBtnDeleteClicked = Signal(str)
    sigItemColorChanged = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def find_item_by_id(
        self,
        id_: str,
    ) -> Tuple[int, ZListWidgetItem] | Tuple[None, None]:
        for row in range(self.listw_labels.count()):
            item: ZListWidgetItem = self.listw_labels.item(row)  # type: ignore
            if item.id_ == id_:
                return row, item
        return None, None

    def on_btn_delete_clicked(self, id_: str):
        """
        TODO: check if the label is used
        """
        self.sigBtnDeleteClicked.emit(id_)

    def on_item_color_changed(self, id_: str):
        row, item = self.find_item_by_id(id_)
        if row is not None and item is not None:
            widget: ZLabelItemWidget = self.listw_labels.itemWidget(item)  # type: ignore
            self.sigItemColorChanged.emit(id_, widget.color)

    def add_label(self, label: Label):
        item = ZListWidgetItem(label.id, "", self.listw_labels)
        item_widget = ZLabelItemWidget(label.id, label.name, label.color)
        item_widget.sigBtnDeleteClicked.connect(self.on_btn_delete_clicked)
        item_widget.sigColorChanged.connect(self.on_item_color_changed)
        self.listw_labels.addItem(item)
        self.listw_labels.setItemWidget(item, item_widget)
        self.ledit_add_label.clear()

    def remove_label(self, row: int | None = None):
        row = row or self.listw_labels.currentRow()
        if row < 0 or row > self.listw_labels.count():
            return
        self.listw_labels.takeItem(row)

    def set_labels(self, labels: List[Label], selected_id: str | None = None):
        self.listw_labels.clear()
        if len(labels) == 0:
            return
        selected_id = selected_id or labels[0].id
        row = 0
        for i, label in enumerate(labels):
            self.add_label(label)
            if label.id == selected_id:
                row = i
        self.listw_labels.setCurrentRow(row)
