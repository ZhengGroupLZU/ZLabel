"""Annos dock: two-level tree of annotations and their instance groups.

Top-level rows are either independent annotations (``instance_id == 0``) or
instance branches ("instance N"). An instance branch groups the annotations
merged into it (any labels) and carries the germination-status combo; the
group lives in ``Annotation.instances[iid]``.
"""

from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtGui import QBrush, QColor, QGuiApplication, QKeyEvent
from pyqtgraph.Qt.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QHeaderView, QTreeWidgetItem, QWidget

from zlabel.utils import Annotation

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

ID_ROLE = Qt.ItemDataRole.UserRole
INST_ROLE = Qt.ItemDataRole.UserRole + 1


def humanize_status(value: str) -> str:
    words = value.replace("-", " ").split("_")
    if not words:
        return value
    head = words[0].capitalize()
    return head + ((" " + " ".join(words[1:])) if len(words) > 1 else "")


class ZDockAnnotationContent(QWidget, Ui_ZDockAnnotationContent):
    sigItemDeleted = Signal(object)
    sigItemCountChanged = Signal(int)
    sigInstanceStatusChanged = Signal(int, str)
    sigAutoNewInstanceToggled = Signal(bool)
    sigDefaultInstanceStatusChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.listWidget.setColumnCount(2)
        self.listWidget.header().hide()
        self.listWidget.setTextElideMode(Qt.TextElideMode.ElideNone)
        header = self.listWidget.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        # header row: default-instance-status combo + auto-new-instance checkbox
        self.cmbox_default_instance = QComboBox()
        self.cmbox_default_instance.setToolTip(
            self.tr("Default germination status assigned to newly created instances")
        )
        self.chk_auto_new = QCheckBox(self.tr("New instance"))
        self.chk_auto_new.setChecked(True)
        self.chk_auto_new.setToolTip(
            self.tr(
                "Always create a new instance for each annotation; "
                "uncheck to add annotations to the currently selected instance"
            )
        )
        header_lay = QHBoxLayout()
        header_lay.addWidget(self.cmbox_default_instance)
        header_lay.addWidget(self.chk_auto_new)
        header_lay.addStretch()
        self.verticalLayout.insertLayout(0, header_lay)
        self.chk_auto_new.toggled.connect(self.sigAutoNewInstanceToggled.emit)
        self.cmbox_default_instance.currentIndexChanged.connect(self._on_default_instance_changed)

        self._statuses: list[str] = []

        self.items: list[str] = []
        self._anno: Annotation | None = None
        self._instance_colors: dict[int, QColor] = {}
        self._palette_idx = 0
        self.sigItemCountChanged.connect(self.set_title)

    def _on_default_instance_changed(self):
        self.sigDefaultInstanceStatusChanged.emit(self.default_instance_status())

    def set_instance_statuses(self, statuses: list[str] | None):
        self._statuses = list(statuses or [])
        # repopulate the default-instance combo, preserving the current choice
        current = self.cmbox_default_instance.currentData()
        self.cmbox_default_instance.blockSignals(True)
        self.cmbox_default_instance.clear()
        self.cmbox_default_instance.addItem("None", "")
        for val in self._statuses:
            self.cmbox_default_instance.addItem(humanize_status(val), val)
        idx = self.cmbox_default_instance.findData(current)
        self.cmbox_default_instance.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmbox_default_instance.blockSignals(False)

    def default_instance_status(self) -> str:
        """Germination status assigned to newly created instances ("" = None)."""
        return self.cmbox_default_instance.currentData() or ""

    def _color_for_instance(self, instance_id: int) -> QColor:
        if instance_id not in self._instance_colors:
            color = QColor(INSTANCE_PALETTE[self._palette_idx % len(INSTANCE_PALETTE)])
            color.setAlphaF(0.35)
            self._instance_colors[instance_id] = color
            self._palette_idx += 1
        return self._instance_colors[instance_id]

    def _make_branch(self, instance_id: int) -> QTreeWidgetItem:
        item = QTreeWidgetItem([f"instance {instance_id}"])
        item.setData(0, ID_ROLE, None)
        item.setData(0, INST_ROLE, instance_id)
        color = self._color_for_instance(instance_id)
        item.setBackground(0, QBrush(color))
        item.setBackground(1, QBrush(color))
        item.setExpanded(True)
        return item

    def _branch_combo(self, instance_id: int) -> QComboBox:
        """Germination-status combo for an instance branch."""
        combo = QComboBox()
        combo.addItem("None", "")
        for val in self._statuses:
            combo.addItem(humanize_status(val), val)
        status = self._anno.instances.get(instance_id, "") if self._anno else ""
        idx = combo.findData(status)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda *_, c=combo, i=instance_id: self._on_status(i, c))
        return combo

    def _on_status(self, instance_id: int, combo: QComboBox):
        self.sigInstanceStatusChanged.emit(instance_id, combo.currentData())

    def _make_result_item(self, result) -> QTreeWidgetItem:
        label = result.labels[0] if result.labels else None
        text = f"{label.name} {result.id}" if label else result.id
        item = QTreeWidgetItem([text])
        item.setData(0, ID_ROLE, result.id)
        item.setData(0, INST_ROLE, getattr(result, "instance_id", 0))
        base = QColor(label.color if label else "#888888")
        item.setBackground(0, QBrush(base.lighter(100)))
        item.setBackground(1, QBrush(base.lighter(100)))
        return item

    def _find_branch(self, instance_id: int) -> QTreeWidgetItem | None:
        for i in range(self.listWidget.topLevelItemCount()):
            top = self.listWidget.topLevelItem(i)
            if top.data(0, ID_ROLE) is None and top.data(0, INST_ROLE) == instance_id:
                return top
        return None

    def rebuild(self, anno: Annotation | None):
        """Rebuild the two-level tree: independent annotations + instance branches."""
        self.listWidget.clear()
        self.items.clear()
        self._anno = anno
        self._instance_colors.clear()
        self._palette_idx = 0
        if anno is None:
            self.sigItemCountChanged.emit(0)
            return
        branches: dict[int, QTreeWidgetItem] = {}
        for result in anno.results.values():
            iid = getattr(result, "instance_id", 0)
            item = self._make_result_item(result)
            if iid:
                branch = branches.get(iid)
                if branch is None:
                    branch = self._make_branch(iid)
                    branches[iid] = branch
                    self.listWidget.addTopLevelItem(branch)
                    self.listWidget.setItemWidget(branch, 1, self._branch_combo(iid))
                branch.addChild(item)
            else:
                self.listWidget.addTopLevelItem(item)
            self.items.append(result.id)
        self.sigItemCountChanged.emit(len(self.items))

    def add_items_by_anno(self, anno: Annotation | None):
        self.rebuild(anno)

    def update_instance_colors(self, anno: Annotation | None):
        """Re-group the tree after grouping/splitting changed instance ids."""
        self.rebuild(anno)

    # region selection helpers
    def selected_result_ids(self, expand_branches: bool = True) -> list[str]:
        """Result ids of the selected rows; branches expand to their members."""
        out: list[str] = []
        for it in self.listWidget.selectedItems():
            rid = it.data(0, ID_ROLE)
            if rid:
                out.append(rid)
            elif expand_branches:
                for i in range(it.childCount()):
                    rid = it.child(i).data(0, ID_ROLE)
                    if rid:
                        out.append(rid)
        return out

    def selected_instance_id(self) -> int:
        """Instance id of the single selected row (branch or member), else 0."""
        items = self.listWidget.selectedItems()
        if len(items) == 1:
            iid = items[0].data(0, INST_ROLE)
            if isinstance(iid, int):
                return iid
        return 0

    def set_selected_ids(self, ids: list[str]):
        id_set = set(ids)
        self.listWidget.clearSelection()
        for i in range(self.listWidget.topLevelItemCount()):
            top = self.listWidget.topLevelItem(i)
            if top.data(0, ID_ROLE) in id_set:
                top.setSelected(True)
            for j in range(top.childCount()):
                child = top.child(j)
                if child.data(0, ID_ROLE) in id_set:
                    child.setSelected(True)

    # endregion

    def _find_item(self, id_: str) -> QTreeWidgetItem | None:
        def walk(item: QTreeWidgetItem | None) -> QTreeWidgetItem | None:
            if item is None:
                return None
            if item.data(0, ID_ROLE) == id_:
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
        if parent is not None:
            parent.removeChild(item)
            # prune the instance branch once it has no members left
            if parent.childCount() == 0:
                self.listWidget.takeTopLevelItem(self.listWidget.indexOfTopLevelItem(parent))
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
        if self._anno is None or id_ not in self._anno.results:
            # no anno context (e.g. undo of a removed result): fall back to top-level
            item = QTreeWidgetItem([id_])
            item.setData(0, ID_ROLE, id_)
            self.listWidget.addTopLevelItem(item)
            self.listWidget.setCurrentItem(item)
            self.items.append(id_)
            self.sigItemCountChanged.emit(len(self.items))
            return
        result = self._anno.results[id_]
        item = self._make_result_item(result)
        iid = getattr(result, "instance_id", 0)
        if iid:
            branch = self._find_branch(iid)
            if branch is None:
                branch = self._make_branch(iid)
                self.listWidget.addTopLevelItem(branch)
                self.listWidget.setItemWidget(branch, 1, self._branch_combo(iid))
            branch.addChild(item)
        else:
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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            items: list[QTreeWidgetItem] = self.listWidget.selectedItems()  # type: ignore
            self.sigItemDeleted.emit([it.data(0, ID_ROLE) for it in items if it.data(0, ID_ROLE)])
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            items: list[QTreeWidgetItem] = self.listWidget.selectedItems()  # type: ignore
            QGuiApplication.clipboard().setText("\n".join(it.data(0, ID_ROLE) for it in items if it.data(0, ID_ROLE)))
            print(QGuiApplication.clipboard().text())
        return super().keyPressEvent(event)

    def set_title(self):
        count = len(self.items)
        self.setWindowTitle(self.tr(f"Annos ({count} items)"))
