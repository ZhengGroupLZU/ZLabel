from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtCore import Qt

from zlabel.utils import (
    Annotation,
    Label,
    PointResult,
    PolygonResult,
    RectangleResult,
)
from zlabel.widgets.dock_anno import ID_ROLE, ZDockAnnotationContent


@pytest.fixture
def dock(qtbot):
    d = ZDockAnnotationContent()
    qtbot.addWidget(d)
    d.resize(300, 400)
    d.show()
    d.set_instance_statuses(["normal_seed", "moldy_seed"])
    return d


def _anno() -> Annotation:
    lbl = Label.new("A", "#ff0000")
    anno = Annotation(id="a1", image_path="a.png", original_width=64, original_height=64)
    anno.add_result(RectangleResult.new(id_="r1", x=1, y=1, w=10, h=10, labels=[lbl]))
    anno.add_result(RectangleResult.new(id_="r2", x=20, y=20, w=10, h=10, labels=[lbl], instance_id=3))
    anno.add_result(PointResult.new(id_="p1", x=5, y=5, labels=[lbl], instance_id=3))
    return anno


def test_rebuild_tree_structure(dock):
    anno = _anno()
    dock.rebuild(anno)
    assert dock.listWidget.topLevelItemCount() == 2  # r1 + instance 3 branch
    r1 = dock.listWidget.topLevelItem(0)
    assert r1.data(0, ID_ROLE) == "r1"
    branch = dock.listWidget.topLevelItem(1)
    assert branch.text(0) == "instance 3"
    assert branch.childCount() == 2


def test_rebuild_emits_count(dock, qtbot):
    with qtbot.waitSignal(dock.sigItemCountChanged, timeout=1000) as blocker:
        dock.rebuild(_anno())
    assert blocker.args == [3]


def test_selected_result_ids_expand_branch(dock):
    dock.rebuild(_anno())
    branch = dock.listWidget.topLevelItem(1)
    branch.setSelected(True)
    ids = dock.selected_result_ids()
    assert set(ids) == {"r2", "p1"}


def test_set_selected_ids_and_row_by_text(dock):
    dock.rebuild(_anno())
    dock.set_selected_ids(["r2", "p1"])
    assert set(dock.selected_result_ids()) == {"r2", "p1"}
    dock.set_row_by_text("r1")
    assert dock.selected_result_ids() == ["r1"]


def test_remove_item_prunes_empty_branch(dock):
    dock.rebuild(_anno())
    dock.remove_item("r1")
    assert dock.listWidget.topLevelItemCount() == 1
    dock.remove_item("r2")
    # branch still has p1 -> stays
    assert dock.listWidget.topLevelItemCount() == 1
    dock.remove_item("p1")
    # branch empty -> pruned
    assert dock.listWidget.topLevelItemCount() == 0


def test_add_item_fallback_without_anno(dock):
    # no _anno context (e.g. undo of a removed result) -> plain top-level item
    dock.add_item("ghost")
    assert dock.listWidget.topLevelItemCount() == 1
    assert dock.listWidget.topLevelItem(0).data(0, ID_ROLE) == "ghost"


def test_add_item_uses_anno_context(dock):
    anno = _anno()
    dock._anno = anno
    dock.add_item("r1")
    dock.add_item("r2")
    assert dock.listWidget.topLevelItemCount() == 2  # r1 + instance 3 branch


def test_delete_key_emits_deleted(dock, qtbot):
    dock.rebuild(_anno())
    dock.set_selected_ids(["r1"])
    dock.listWidget.setFocus(Qt.FocusReason.OtherFocusReason)
    with qtbot.waitSignal(dock.sigItemDeleted, timeout=1000) as blocker:
        from PySide6.QtTest import QTest

        QTest.keyClick(dock.listWidget, Qt.Key.Key_Delete)
    assert blocker.args == [["r1"]]


def test_status_combo_emits_change(dock, qtbot):
    anno = _anno()
    dock.rebuild(anno)
    branch = dock.listWidget.topLevelItem(1)
    combo = dock.listWidget.itemWidget(branch, 1)
    assert combo is not None
    with qtbot.waitSignal(dock.sigInstanceStatusChanged, timeout=1000) as blocker:
        combo.setCurrentIndex(2)  # 0=None, 1=normal_seed, 2=moldy_seed
    assert blocker.args == [3, "moldy_seed"]


def test_auto_new_checkbox_emits(dock, qtbot):
    with qtbot.waitSignal(dock.sigAutoNewInstanceToggled, timeout=1000) as blocker:
        dock.chk_auto_new.setChecked(False)
    assert blocker.args == [False]


def test_default_instance_combo_populated_from_statuses(dock):
    # first item is None, then the statuses from project settings
    assert dock.cmbox_default_instance.count() == 1 + 2  # None + 2 statuses
    assert dock.cmbox_default_instance.itemText(0) == "None"
    assert dock.cmbox_default_instance.itemData(0) == ""
    assert dock.cmbox_default_instance.itemText(1) == "Normal seed"
    assert dock.cmbox_default_instance.itemData(1) == "normal_seed"
    assert dock.default_instance_status() == ""


def test_default_instance_combo_preserves_selection(dock):
    dock.cmbox_default_instance.setCurrentIndex(dock.cmbox_default_instance.findData("moldy_seed"))
    assert dock.default_instance_status() == "moldy_seed"
    # repopulating (e.g. project reload) keeps the selected status
    dock.set_instance_statuses(["normal_seed", "moldy_seed", "dead_seed"])
    assert dock.default_instance_status() == "moldy_seed"
    # a status that no longer exists falls back to None
    dock.set_instance_statuses(["normal_seed"])
    assert dock.default_instance_status() == ""


def test_clear_items(dock):
    dock.rebuild(_anno())
    dock.clear_items()
    assert dock.items == []
    assert dock.listWidget.topLevelItemCount() == 0
