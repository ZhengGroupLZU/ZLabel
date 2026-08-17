from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtCore import Qt

from zlabel.utils import Task
from zlabel.widgets.dock_file import ZDockFileContent


@pytest.fixture
def dock(qtbot):
    d = ZDockFileContent()
    qtbot.addWidget(d)
    d.resize(400, 400)
    d.show()
    return d


def _tasks() -> list[Task]:
    return [
        Task(id=1, filename="a.png", anno_id="a1", labels=[]),
        Task(id=2, filename="b.png", anno_id="b2", labels=[]),
    ]


def test_set_file_list_populates_table(dock):
    dock.set_file_list(_tasks())
    assert dock.count() == 2
    assert dock.get_row_txt(0) == "a.png"
    assert dock.get_row_txt(1) == "b.png"
    assert dock.get_current_task_id() == "a1"


def test_set_row_by_txt(dock):
    dock.set_file_list(_tasks())
    dock.set_row_by_txt("b2")
    assert dock.currentRow() == 1
    dock.set_row_by_txt("missing")
    assert dock.currentRow() == 1  # not found -> selection untouched


def test_set_fetch_num_idx(dock):
    dock.set_fetch_num_idx_by_value(10)
    assert dock.cbox_fetch_num.currentText() == "10"
    dock.set_fetch_num_idx_by_value(999)
    # no match -> fall back to the last ("All") entry
    assert dock.cbox_fetch_num.currentIndex() == dock.cbox_fetch_num.count() - 1


def test_item_finished_coloring(dock):
    dock.set_file_list(_tasks())
    dock.set_item_finished(_tasks()[0])
    item = dock.getItem(0)
    assert "24bfa5" in item.background().color().name()
    dock.set_item_unfinished(_tasks()[0])
    assert "fd394c" in dock.getItem(0).background().color().name()


def test_fetch_button_emits_signal(dock, qtbot):
    dock.cmbox_project.addItem("proj")
    dock.cbox_fetch_num.setCurrentIndex(0)
    with qtbot.waitSignal(dock.sigFetchTasks, timeout=1000) as blocker:
        dock.btn_fetch.click()
    project_id, num, finished = blocker.args
    assert project_id == 0
    assert num == int(dock.cbox_fetch_num.currentText())


def test_jump_emits_item_clicked(dock, qtbot):
    dock.set_file_list(_tasks())
    dock.ledit_jump.setText("2")
    with qtbot.waitSignal(dock.sigItemClicked, timeout=1000) as blocker:
        dock.ledit_jump.editingFinished.emit()
    assert blocker.args == ["b2"]


def test_storage_combo_emits_signal(dock, qtbot):
    with qtbot.waitSignal(dock.sigStorageChanged, timeout=1000) as blocker:
        dock.cmbox_storage.setCurrentIndex(1)
    assert blocker.args == ["local"]
    assert dock.ledit_local_dir.isVisible()


def test_local_dir_browse_emits_signal(dock, qtbot, mock_qt_dialogs):
    mock_qt_dialogs.directory_result = "C:/imgs"
    with qtbot.waitSignal(dock.sigLocalDirChanged, timeout=1000) as blocker:
        dock.btn_local_dir.click()
    assert blocker.args == ["C:/imgs"]
    assert dock.ledit_local_dir.text() == "C:/imgs"


def test_finished_checkbox_tristate(dock):
    # default: Unchecked ("Unfinished"); tri-state cycles
    # Unchecked -> PartiallyChecked -> Checked -> Unchecked
    assert dock.ckbox_finished.checkState() == Qt.CheckState.Unchecked
    dock.ckbox_finished.click()
    assert dock.ckbox_finished.checkState() == Qt.CheckState.PartiallyChecked
    assert dock.ckbox_finished.text() == "All"
    dock.ckbox_finished.click()
    assert dock.ckbox_finished.checkState() == Qt.CheckState.Checked
    assert dock.ckbox_finished.text() == "Finished"
    dock.ckbox_finished.click()
    assert dock.ckbox_finished.checkState() == Qt.CheckState.Unchecked
    assert dock.ckbox_finished.text() == "Unfinished"
