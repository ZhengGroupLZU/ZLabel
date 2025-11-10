from pyqtgraph.Qt.QtCore import Signal
from pyqtgraph.Qt.QtWidgets import QWidget

from zlabel.utils import Label
from zlabel.utils.project import id_uuid4
from zlabel.widgets.zwidgets import ZLabelItemWidget, ZListWidgetItem

from .ui import Ui_ZDockLabelContent


class ZDockLabelContent(QWidget, Ui_ZDockLabelContent):
    sigBtnIncreaseClicked = Signal(object)  # Label instance
    SigBtnDecreaseClicked = Signal(str)  # label id
    sigBtnDeleteClicked = Signal(str)
    sigItemColorChanged = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.btn_increase.clicked.connect(self.on_btn_increase_clicked)
        self.btn_decrease.clicked.connect(self.on_btn_decrease_clicked)

    def find_item_by_id(
        self,
        id_: str,
    ) -> tuple[int, ZListWidgetItem] | tuple[None, None]:
        for row in range(self.listw_labels.count()):
            item: ZListWidgetItem = self.listw_labels.item(row)  # type: ignore
            if item.id_ == id_:
                return row, item
        return None, None

    def set_color(self, color: str):
        for row in range(self.listw_labels.count()):
            item: ZListWidgetItem = self.listw_labels.item(row)  # type: ignore
            widget: ZLabelItemWidget = self.listw_labels.itemWidget(item)  # type: ignore
            widget.set_label_color(color)

    def on_btn_increase_clicked(self):
        txt = self.ledit_add_label.text()
        if not txt:
            return
        label = Label(id=id_uuid4(), name=txt)
        self.add_label(label)
        self.sigBtnIncreaseClicked.emit(label)

    def on_btn_decrease_clicked(self):
        row = self.listw_labels.currentRow()
        self.remove_label(row)
        item: ZListWidgetItem = self.listw_labels.item(row)  # type: ignore
        self.SigBtnDecreaseClicked.emit(item.id_)

    def on_btn_delete_clicked(self, id_: str):
        """
        TODO: check if the label is used
        """
        row, item = self.find_item_by_id(id_)
        if row is not None:
            self.listw_labels.takeItem(row)
        self.sigBtnDeleteClicked.emit(id_)

    def on_item_color_changed(self, id_: str):
        row, item = self.find_item_by_id(id_)
        if row is not None and item is not None:
            widget: ZLabelItemWidget = self.listw_labels.itemWidget(item)  # type: ignore
            self.sigItemColorChanged.emit(id_, widget.color)

    def add_label(self, label: Label | None):
        if label is None:
            return
        item = ZListWidgetItem(label.id, "", self.listw_labels)
        item_widget = ZLabelItemWidget(label.id, label.name, label.color)
        item_widget.sigBtnDeleteClicked.connect(self.on_btn_delete_clicked)
        item_widget.sigColorChanged.connect(self.on_item_color_changed)
        self.listw_labels.addItem(item)
        self.listw_labels.setItemWidget(item, item_widget)
        self.listw_labels.setCurrentItem(item)
        self.ledit_add_label.clear()

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
        selected_id = selected_id or labels[0].id
        row = 0
        for i, label in enumerate(labels):
            self.add_label(label)
            if label.id == selected_id:
                row = i
        self.listw_labels.setCurrentRow(row)
        self.listw_labels.itemClicked.emit(self.listw_labels.currentItem())
