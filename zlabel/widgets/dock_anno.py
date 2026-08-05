from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtGui import QBrush, QColor, QGuiApplication, QKeyEvent
from pyqtgraph.Qt.QtWidgets import QTreeWidgetItem, QWidget

from zlabel.utils import Annotation, PointResult

from .ui import Ui_ZDockAnnotationContent

INSTANCE_PALETTE = [
    "#ffd54f",
    "#81c784",
    "#64b5f6",
    "#f48fb1",
    "#ce93d8",
    "#ff8a65",
    "#4dd0e1",
    "#aed581",
]

_ID_ROLE = Qt.ItemDataRole.UserRole


class ZDockAnnotationContent(QWidget, Ui_ZDockAnnotationContent):
    sigItemDeleted = Signal(object)
    sigItemCountChanged = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.items: list[str] = []
        self._instance_colors: dict[str, QColor] = {}
        self._palette_idx = 0
        self.sigItemCountChanged.connect(self.set_title)

    def _make_item(self, id_: str, text: str | None = None) -> QTreeWidgetItem:
        item = QTreeWidgetItem([text or id_])
        item.setData(0, _ID_ROLE, id_)
        return item

    def _color_for_instance(self, instance_id: str) -> QColor | None:
        if not instance_id:
            return None
        if instance_id not in self._instance_colors:
            color = QColor(INSTANCE_PALETTE[self._palette_idx % len(INSTANCE_PALETTE)])
            color.setAlphaF(0.35)
            self._instance_colors[instance_id] = color
            self._palette_idx += 1
        return self._instance_colors[instance_id]

    def _find_item(self, id_: str) -> QTreeWidgetItem | None:
        def walk(item: QTreeWidgetItem | None) -> QTreeWidgetItem | None:
            if item is None:
                return None
            if item.data(0, _ID_ROLE) == id_:
                return item
            for i in range(item.childCount()):
                r = walk(item.child(i))
                if r is not None:
                    return r
            return None

        for i in range(self.listWidget.topLevelItemCount()):
            r = walk(self.listWidget.topLevelItem(i))
            if r is not None:
                return r
        return None

    def _find_item_by_id(self, id_: str) -> QTreeWidgetItem | None:
        return self._find_item(id_)

    def rebuild(self, anno: Annotation | None):
        """Rebuild the tree: keypoints sharing an instance_id live under one
        collapsed group item (placed on top, colored with the instance color);
        independent results are top-level items below."""
        self.listWidget.clear()
        self.items.clear()
        self._instance_colors.clear()
        self._palette_idx = 0
        if anno is None:
            self.sigItemCountChanged.emit(0)
            return
        groups: dict[str, QTreeWidgetItem] = {}
        independents: list[QTreeWidgetItem] = []
        for r in anno.results.values():
            color = self._color_for_instance(r.instance_id) if isinstance(r, PointResult) else None
            if isinstance(r, PointResult) and r.instance_id:
                parent = groups.get(r.instance_id)
                if parent is None:
                    parent = QTreeWidgetItem([f"instance {r.instance_id[:8]}"])
                    parent.setData(0, _ID_ROLE, None)
                    groups[r.instance_id] = parent
                item = self._make_item(r.id)
                parent.addChild(item)
            else:
                item = self._make_item(r.id)
                independents.append(item)
            if color is not None:
                item.setBackground(0, QBrush(color))
            self.items.append(r.id)
        # groups on top, collapsed, with the instance color on the group row
        for gid, parent in groups.items():
            self.listWidget.addTopLevelItem(parent)
            parent.setExpanded(False)  # collapsed after grouping
            color = self._color_for_instance(gid)
            if color is not None:
                parent.setBackground(0, QBrush(color))
        for item in independents:
            self.listWidget.addTopLevelItem(item)
        self.sigItemCountChanged.emit(len(self.items))

    def add_items_by_anno(self, anno: Annotation | None):
        self.rebuild(anno)

    def update_instance_colors(self, anno: Annotation | None):
        """Re-group the tree after keypoints were grouped/ungrouped."""
        self.rebuild(anno)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            items: list[QTreeWidgetItem] = self.listWidget.selectedItems()  # type: ignore
            self.sigItemDeleted.emit([it.data(0, _ID_ROLE) for it in items if it.data(0, _ID_ROLE)])
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            items: list[QTreeWidgetItem] = self.listWidget.selectedItems()  # type: ignore
            QGuiApplication.clipboard().setText(
                "\n".join(it.data(0, _ID_ROLE) for it in items if it.data(0, _ID_ROLE))
            )
            print(QGuiApplication.clipboard().text())
        return super().keyPressEvent(event)

    def set_row_by_text(self, s: str | None):
        if s is None:
            return
        item = self._find_item(s)
        if item is not None:
            self.listWidget.setCurrentItem(item)
            self.listWidget.scrollToItem(item)

    def remove_item(self, id_: str):
        item = self._find_item(id_)
        if item is None:
            return
        parent = item.parent()
        if parent is not None and parent.childCount() == 1:
            self.listWidget.takeTopLevelItem(self.listWidget.indexOfTopLevelItem(parent))
        else:
            if parent is not None:
                parent.removeChild(item)
            else:
                self.listWidget.takeTopLevelItem(self.listWidget.indexOfTopLevelItem(item))
        if id_ in self.items:
            self.items.remove(id_)
        self.sigItemCountChanged.emit(len(self.items))

    def remove_items(self, ids: list[str]):
        for id_ in ids:
            self.remove_item(id_)

    def add_item(self, id_: str):
        if id_ in self.items:
            return
        item = self._make_item(id_)
        self.listWidget.addTopLevelItem(item)
        self.listWidget.setCurrentItem(item)
        self.items.append(id_)
        self.sigItemCountChanged.emit(len(self.items))

    def add_items(self, ids: list[str]):
        for id_ in ids:
            self.add_item(id_)

    def clear_items(self):
        self.items.clear()
        self.listWidget.clear()
        self.listWidget.setCurrentItem(None)

    def set_title(self):
        count = self.listWidget.topLevelItemCount()
        self.setWindowTitle(self.tr(f"Annos ({count} items)"))
