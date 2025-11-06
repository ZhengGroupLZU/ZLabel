from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtGui import QGuiApplication, QKeyEvent
from pyqtgraph.Qt.QtWidgets import QWidget

from zlabel.utils import Annotation
from zlabel.widgets import ZListWidgetItem

from .ui import Ui_ZDockAnnotationContent


class ZDockAnnotationContent(QWidget, Ui_ZDockAnnotationContent):
    sigItemDeleted = Signal(object)
    sigItemCountChanged = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.items: list[str] = []
        # self.sigItemCountChanged.connect(self.set_title)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            items: list[ZListWidgetItem] = self.listWidget.selectedItems()  # type: ignore
            self.sigItemDeleted.emit([it.id_ for it in items])
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            items: list[ZListWidgetItem] = self.listWidget.selectedItems()  # type: ignore
            QGuiApplication.clipboard().setText("\n".join([it.id_ for it in items]))
            print(QGuiApplication.clipboard().text())
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
                self.sigItemCountChanged.emit(self.listWidget.count())
                break

    def remove_items(self, ids: list[str]):
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
        self.sigItemCountChanged.emit(self.listWidget.count())

    def add_items(self, ids: list[str]):
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

    def set_title(self):
        count = self.listWidget.count()
        self.setWindowTitle(f"Annos ({count} items)")
