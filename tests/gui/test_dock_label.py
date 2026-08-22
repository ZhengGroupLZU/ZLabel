from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtCore import Qt

from zlabel.utils import Label
from zlabel.widgets.dock_label import ZDockLabelContent
from zlabel.widgets.zwidgets import ZLabelItemWidget


@pytest.fixture
def dock(qtbot):
    d = ZDockLabelContent()
    qtbot.addWidget(d)
    d.resize(300, 300)
    d.show()
    return d


def _labels() -> list[Label]:
    return [Label.new("A", "#ff0000"), Label.new("B", "#00ff00")]


def test_two_tabs_exist(dock):
    assert dock.tab_widget.count() == 2
    assert dock.tab_widget.tabText(0) == "Labels"
    assert dock.tab_widget.tabText(1) == "Instance"


def test_instance_statuses_populate_and_radio_emits(dock, qtbot):
    dock.set_instance_statuses(["normal_seed", "moldy_seed"], selected_status="moldy_seed")
    assert dock.listw_instances.count() == 2
    assert dock.default_instance_status() == "moldy_seed"

    widgets = list(dock._instance_widgets.values())
    with qtbot.waitSignal(dock.sigDefaultInstanceSelected, timeout=1000) as blocker:
        widgets[0].radio.setChecked(True)
    assert blocker.args == ["normal_seed"]
    assert dock.default_instance_status() == "normal_seed"


def test_instance_item_click_selects_radio(dock):
    dock.set_instance_statuses(["normal_seed", "moldy_seed"])
    dock.on_instance_item_clicked(dock.listw_instances.item(1))
    assert dock.default_instance_status() == "moldy_seed"


def test_instance_label_text_left_aligned(dock):
    dock.set_instance_statuses(["normal_seed"])
    widget = next(iter(dock._instance_widgets.values()))
    assert widget.label_text.alignment() & Qt.AlignmentFlag.AlignLeft


def test_instance_visibility_toggle_emits(dock, qtbot):
    dock.set_instance_statuses(["normal_seed"])
    widget = next(iter(dock._instance_widgets.values()))
    with qtbot.waitSignal(dock.sigInstanceVisibilityToggled, timeout=1000) as blocker:
        widget.btn_visible.click()
    assert blocker.args == ["normal_seed"]


def test_set_labels_populates(dock):
    labels = _labels()
    dock.set_labels(labels)
    assert dock.listw_labels.count() == 2
    row, item = dock.find_item_by_id(labels[0].id)
    assert row == 0


def test_set_labels_with_selection_emits(dock, qtbot):
    labels = _labels()
    with qtbot.waitSignal(dock.sigItemClicked, timeout=1000) as blocker:
        dock.set_labels(labels, selected_id=labels[1].id)
    assert blocker.args == [labels[1].id]
    assert dock.listw_labels.currentRow() == 1


def test_select_row_by_id_emits(dock, qtbot):
    labels = _labels()
    dock.set_labels(labels)
    with qtbot.waitSignal(dock.sigItemClicked, timeout=1000) as blocker:
        dock.select_row_by_id(labels[1].id)
    assert blocker.args == [labels[1].id]


def test_add_and_remove_label(dock):
    labels = _labels()
    dock.set_labels(labels)
    lbl = Label.new("C", "#0000ff")
    dock.add_label(lbl)
    assert dock.find_item_by_id(lbl.id)[0] == 2
    dock.remove_label(lbl.id)
    assert dock.find_item_by_id(lbl.id)[0] is None


def test_visibility_toggle_emits(dock, qtbot):
    labels = _labels()
    dock.set_labels(labels)
    row, item = dock.find_item_by_id(labels[0].id)
    widget = dock.listw_labels.itemWidget(item)
    assert isinstance(widget, ZLabelItemWidget)
    with qtbot.waitSignal(dock.sigItemVisibilityToggled, timeout=1000) as blocker:
        widget.btn_visible.click()
    assert blocker.args == [labels[0].id]


def test_visibility_state_styles(dock):
    labels = _labels()
    dock.set_labels(labels)
    row, item = dock.find_item_by_id(labels[0].id)
    widget = dock.listw_labels.itemWidget(item)
    widget.set_visible_state(False)
    assert "opacity" in widget.btn_visible.styleSheet()
    widget.set_visible_state(True)
    assert "opacity" not in widget.btn_visible.styleSheet()


def test_color_change_emits(dock, qtbot, mock_qt_dialogs):
    labels = _labels()
    dock.set_labels(labels)
    row, item = dock.find_item_by_id(labels[1].id)
    widget = dock.listw_labels.itemWidget(item)

    from pyqtgraph.Qt.QtGui import QColor

    mock_qt_dialogs.color_result = QColor("#123456")
    # ZLabelItemWidget opens QColorDialog.getColor — mock it directly
    import pytest
    from pyqtgraph.Qt.QtWidgets import QColorDialog

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(QColorDialog, "getColor", lambda *a, **k: QColor("#123456"))
    try:
        with qtbot.waitSignal(dock.sigItemColorChanged, timeout=1000) as blocker:
            widget.on_label_color_clicked()
    finally:
        monkeypatch.undo()
    assert blocker.args[0] == labels[1].id
    assert blocker.args[1].upper() == "#123456"
