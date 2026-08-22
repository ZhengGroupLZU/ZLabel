from __future__ import annotations

from pathlib import Path

import pytest
from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtWidgets import QMessageBox
from PySide6.QtTest import QTest

from zlabel.utils import AnnotationType, DrawMode, RgbMode, StatusMode


# ---------------------------------------------------------------------------
# Construction / structure
# ---------------------------------------------------------------------------
def test_menu_actions_exist(main_window):
    win = main_window
    for name in (
        "actionUndo",
        "actionRedo",
        "actionSave",
        "actionFinish",
        "actionCancel",
        "actionNext",
        "actionPrev",
        "actionZoom_in",
        "actionZoom_out",
        "actionFit_wiondow",
        "actionVisible",
        "actionMove",
        "actionEdit",
        "actionRectangle",
        "actionPoint",
        "actionPolygon",
        "actionMerge",
        "actionGroup",
        "actionSettings",
        "actionExport",
        "action_import_task",
        "actionEnglish",
        "actionChinese",
    ):
        assert getattr(win, name, None) is not None, name


def test_undo_redo_actions_guard_empty_stack(main_window):
    win = main_window
    win.on_action_undo_triggered()  # no-op, must not raise
    win.on_action_redo_triggered()  # no-op, must not raise
    assert win.undo_stack.count() == 0


# ---------------------------------------------------------------------------
# Mode switching
# ---------------------------------------------------------------------------
def test_switch_draw_modes(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_rectangle_triggered()
    assert win.canvas._status_mode == StatusMode.CREATE
    assert win.canvas._draw_mode == DrawMode.RECTANGLE
    # the active mode action is disabled, the others re-enabled
    assert not win.actionRectangle.isEnabled()
    assert win.actionEdit.isEnabled()

    win.on_action_polygon_triggered()
    assert win.canvas._draw_mode == DrawMode.POLYGON
    assert not win.actionPolygon.isEnabled()
    assert win.actionRectangle.isEnabled()

    win.on_action_point_triggered()
    assert win.canvas._draw_mode == DrawMode.POINT

    win.on_action_edit_triggered()
    assert win.canvas._status_mode == StatusMode.EDIT
    assert not win.actionEdit.isEnabled()

    win.on_action_move_triggered()
    assert win.canvas._status_mode == StatusMode.VIEW
    assert not win.actionMove.isEnabled()


def test_keypoint_mode_disables_rect_polygon(populated_project):
    win, proj, anno, rebuild = populated_project
    win.cmbox_anno_type.setCurrentIndex(AnnotationType.POINT.value)
    assert win.settings.annotation_type == AnnotationType.POINT
    assert not win.actionRectangle.isEnabled()
    assert not win.actionPolygon.isEnabled()
    assert win.canvas._status_mode == StatusMode.VIEW  # forced out of CREATE
    # L/O/X shortcuts become active
    assert all(sc.isEnabled() for sc in win._point_visible_shortcuts)

    win.cmbox_anno_type.setCurrentIndex(AnnotationType.RECTANGLE.value)
    assert win.actionRectangle.isEnabled()
    assert win.actionPolygon.isEnabled()
    assert not win._point_visible_shortcuts[0].isEnabled()


def test_anno_type_combo_updates_settings(populated_project):
    win, proj, anno, rebuild = populated_project
    win.cmbox_anno_type.setCurrentIndex(AnnotationType.POLYGON.value)
    assert win.settings.annotation_type == AnnotationType.POLYGON


def test_rgb_combo_updates_canvas(populated_project):
    win, proj, anno, rebuild = populated_project
    win.cmbox_rgb.setCurrentIndex(0)  # Gray
    assert win.rgb_mode == RgbMode.GRAY
    win.cmbox_rgb.setCurrentIndex(3)  # B
    assert win.rgb_mode == RgbMode.B
    win.cmbox_rgb.setCurrentIndex(4)  # RGB
    assert win.rgb_mode == RgbMode.RGB


def test_threshold_slider(populated_project):
    win, proj, anno, rebuild = populated_project
    win.slider_threshold.setValue(150)
    assert win.threshold == 150


def test_rotation_spinbox_updates_anno(populated_project):
    win, proj, anno, rebuild = populated_project
    win.spin_rotation.setValue(180)
    assert win.canvas._rotation == 180
    assert anno.image_rotation == 180


# ---------------------------------------------------------------------------
# View actions
# ---------------------------------------------------------------------------
def test_zoom_and_fit(populated_project):
    win, proj, anno, rebuild = populated_project
    rng_before = [list(r) for r in win.canvas.view_box.viewRange()]
    win.on_action_zoom_in_triggered()
    rng_zoomed = [list(r) for r in win.canvas.view_box.viewRange()]
    assert rng_zoomed != rng_before
    win.on_action_fit_window_triggered()
    rng_fit = [list(r) for r in win.canvas.view_box.viewRange()]
    # after fit, the image bounds [0,64]^2 are visible (y padded for aspect)
    assert rng_fit[0][0] <= 0 and rng_fit[0][1] >= 64


def test_visible_toggle_clears_canvas(populated_project):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r1", x=10, y=10, w=20, h=15, labels=[proj.crt_label]))
    rebuild()
    assert len(win.canvas.showing_items) == 1

    win.actionVisible.setChecked(False)
    win.on_action_visible_triggered()
    assert len(win.canvas.showing_items) == 0

    win.actionVisible.setChecked(True)
    win.on_action_visible_triggered()
    assert set(win.canvas.showing_items) == {"r1"}


def test_dock_toggle_actions(populated_project):
    win, proj, anno, rebuild = populated_project
    win.actionAnnotations.setChecked(False)
    win.on_action_annotations_triggered()
    assert not win.dock_annos.isVisible()
    win.actionAnnotations.setChecked(True)
    win.on_action_annotations_triggered()
    assert win.dock_annos.isVisible()

    win.dock_infos.hide()
    win.on_action_restore_triggered()
    assert win.dock_infos.isVisible()
    assert win.dock_files.isVisible()
    assert win.dock_labels.isVisible()
    assert win.dock_annos.isVisible()


def test_dock_visibility_syncs_action(populated_project):
    win, proj, anno, rebuild = populated_project
    win.dock_labels.hide()
    assert not win.actionLabels.isChecked()
    win.dock_labels.show()
    assert win.actionLabels.isChecked()


# ---------------------------------------------------------------------------
# Undo / redo integration
# ---------------------------------------------------------------------------
def test_draw_then_undo_redo_actions(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)
    assert win.undo_stack.canUndo()
    assert not win.undo_stack.canRedo()

    win.on_action_undo_triggered()
    assert len(anno.results) == 0
    assert win.undo_stack.canRedo()

    win.on_action_redo_triggered()
    assert len(anno.results) == 1
    assert not win.undo_stack.canRedo()


def test_undo_removes_and_restores_canvas_item(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)
    r_id = next(iter(anno.results))

    win.on_action_undo_triggered()
    assert r_id not in win.canvas.showing_items
    win.on_action_redo_triggered()
    assert r_id in win.canvas.showing_items


# ---------------------------------------------------------------------------
# Save / finish / cancel
# ---------------------------------------------------------------------------
def test_save_writes_project_and_anno_files(populated_project):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r1", x=10, y=10, w=20, h=15, labels=[proj.crt_label]))
    win._save_current()

    assert win.settings.project_path.exists()
    anno_path = win.backend.anno_dir / f"{anno.id}.{win.anno_suffix}"
    assert anno_path.exists(), f"{anno_path} missing"
    content = anno_path.read_text(encoding="utf-8")
    assert '"r1"' in content


def test_finish_marks_task_done(populated_project):
    win, proj, anno, rebuild = populated_project
    win.actionFinish.trigger()  # sender() == actionFinish
    assert proj.crt_task.finished is True


def test_cancel_confirmed_resets_annotation(populated_project, mock_qt_dialogs):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r1", x=10, y=10, w=20, h=15, labels=[proj.crt_label]))
    rebuild()

    mock_qt_dialogs.question_result = QMessageBox.StandardButton.Yes
    win.on_action_cancel_triggered()
    assert len(anno.results) == 0
    assert win.canvas.showing_items == {}
    assert proj.crt_task.finished is False


def test_cancel_declined_keeps_annotation(populated_project, mock_qt_dialogs):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r1", x=10, y=10, w=20, h=15, labels=[proj.crt_label]))
    rebuild()
    mock_qt_dialogs.question_result = QMessageBox.StandardButton.No
    win.on_action_cancel_triggered()
    assert len(anno.results) == 1


# ---------------------------------------------------------------------------
# Prev / Next
# ---------------------------------------------------------------------------
def test_next_prev_switches_tasks(main_window, monkeypatch):
    win = main_window
    from zlabel.utils import Annotation, Label, Task

    proj = win.proj
    proj.name = "proj"
    proj.storage_mode = "local"
    lbl = Label.new("A", "#ff0000")
    proj.labels = {lbl.id: lbl}
    proj.key_label = lbl.id
    for i in range(2):
        t = Task(id=i + 1, filename=f"a{i}.png", anno_id=f"a{i}", labels=[])
        proj.tasks[t.anno_id] = t
        proj.add_task(t)
    proj.key_task = "a0"
    for t in proj.tasks.values():
        proj.tasks[t.anno_id].anno = Annotation(
            id=t.anno_id, image_path=t.filename, original_width=64, original_height=64
        )

    # patch the task-click slot to track navigation (avoids image loading paths)
    clicked = []
    monkeypatch.setattr(win, "on_dock_files_item_clicked", lambda task_id: clicked.append(task_id))
    win.dockcnt_files.set_file_list(list(proj.tasks.values()))

    win.actionNext.trigger()
    assert clicked == ["a1"]
    win.actionPrev.trigger()
    assert clicked == ["a1", "a0"]


# ---------------------------------------------------------------------------
# Language
# ---------------------------------------------------------------------------
def test_switch_language_zh_cn(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_chinese_triggered()
    assert win._translator is not None
    assert win.settings.language == "zh_CN"
    # action text translated
    assert win.actionSave.text() != "Save"


def test_switch_language_back_to_english(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_chinese_triggered()
    win.on_action_english_triggered()
    assert win._translator is None
    assert win.settings.language == "en"
    assert win.actionSave.text() == "Save"


# ---------------------------------------------------------------------------
# Import / Export
# ---------------------------------------------------------------------------
def test_export_action_opens_dialog(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_export_triggered()
    from zlabel.widgets.dialog_export import DialogExport

    dialog = win.findChild(DialogExport)
    assert dialog is not None
    dialog.close()


def test_import_task_with_mocked_file(populated_project, mock_qt_dialogs, tmp_path):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import Project

    # the imported project must already be known in settings.projects
    win.settings.projects = [(1, "other")]
    p2 = Project(id="p2", name="other")
    path = tmp_path / "other.json"
    p2.save_json(path)
    mock_qt_dialogs.file_result = (str(path), "*.json")
    win.on_action_import_task_triggered()
    assert win.settings.project_name == "other"
    assert win.proj.name == "other"


def test_settings_dialog_shows(populated_project):
    win, proj, anno, rebuild = populated_project
    win.dialog_settings.show()
    assert win.dialog_settings.isVisible()
    win.dialog_settings.close()


def test_shortcut_dialog_shows(populated_project):
    win, proj, anno, rebuild = populated_project
    win.dialog_shortcut.show()
    assert win.dialog_shortcut.isVisible()
    win.dialog_shortcut.close()


def test_save_shortcut_triggered(populated_project, qtbot, monkeypatch):
    win, proj, anno, rebuild = populated_project
    saved = []
    monkeypatch.setattr(win, "on_action_save_triggered", lambda: saved.append(1))
    QTest.keyClick(win, Qt.Key.Key_S)
    qtbot.wait(10)
    assert saved


def test_dish_crop_box(main_window):
    """_dish_crop_box returns the dish bbox (polygon or rotated rect) or None."""
    win = main_window
    proj = win.proj
    from zlabel.utils import Annotation, Label, PolygonResult, RectangleResult, Task

    lbl_dish = Label.new("Dish", "#911eb4")
    lbl_seed = Label.new("Seed", "#ff0000")
    proj.labels = {lbl_dish.id: lbl_dish, lbl_seed.id: lbl_seed}
    t = Task(id=1, filename="a.png", anno_id="a", labels=[])
    proj.tasks = {t.anno_id: t}
    proj.add_annotation(Annotation(id="a", image_path="a.png", original_width=64, original_height=64))
    anno = proj.crt_anno

    # no dish yet
    assert win._dish_crop_box() is None

    # dish polygon -> bbox of its points
    anno.add_result(
        PolygonResult.new(id_="d", points=[(10, 10), (30, 10), (30, 20), (10, 20)], closed=True, labels=[lbl_dish])
    )
    assert win._dish_crop_box() == (10, 10, 30, 20)

    # a rotated dish rectangle -> bbox covering the rotated content
    anno.results.clear()
    anno.add_result(RectangleResult.new(id_="d2", x=40, y=40, w=8, h=8, rotation=90, labels=[lbl_dish]))
    assert win._dish_crop_box() == (32, 40, 40, 48)


def test_image_cache_is_lru_bounded(main_window):
    """The decoded-frame cache is LRU-bounded so a session doesn't keep every
    visited full-resolution photo in memory."""
    from PIL import Image as _Image

    from zlabel.widgets.mainwindow import _IMAGE_CACHE_SIZE

    win = main_window
    for i in range(_IMAGE_CACHE_SIZE + 3):
        win._image_cache[f"f{i}.png"] = _Image.new("RGB", (4, 4), "black")
    assert len(win._image_cache) == _IMAGE_CACHE_SIZE
    assert "f0.png" not in win._image_cache  # oldest evicted
    assert f"f{_IMAGE_CACHE_SIZE + 2}.png" in win._image_cache  # newest kept


def test_timeline_image_prefers_cache(main_window):
    """_timeline_image returns the in-memory (decoded) image when cached."""
    from PIL import Image as _Image

    win = main_window
    img = _Image.new("RGB", (8, 8), "red")
    win._image_cache["a.png"] = img
    assert win._timeline_image("a.png") is img


def test_label_switch_does_not_change_default_status_combo(main_window):
    """Selecting a label no longer touches the Annos default-status combo."""
    win = main_window
    proj = win.proj
    from zlabel.utils import Annotation, Label, Task

    lbl_seed = Label.new("Seed", "#ff0000")
    lbl_seedling = Label.new("Seedling", "#00ff00")
    lbl_dish = Label.new("Dish", "#0000ff")
    proj.labels = {label.id: label for label in (lbl_seed, lbl_seedling, lbl_dish)}
    t = Task(id=1, filename="a.png", anno_id="a", labels=[])
    proj.tasks = {t.anno_id: t}
    proj.add_annotation(Annotation(id="a", image_path="a.png", original_width=64, original_height=64))
    proj.key_label = lbl_seed.id
    win.dockcnt_labels.set_labels(list(proj.labels.values()), proj.key_label)
    win.dockcnt_anno.set_instance_statuses(["normal_seed", "normal_seedling", "moldy_seed"])
    combo = win.dockcnt_anno.cmbox_default_instance
    idx = combo.findData("moldy_seed")
    combo.setCurrentIndex(idx)

    # Labels panel click / shortcut must not change the combo
    win.dockcnt_labels.select_row(0)  # Seed
    assert combo.currentData() == "moldy_seed"
    win.dockcnt_labels.select_row(1)  # Seedling
    assert combo.currentData() == "moldy_seed"
    win.on_shortcut_select_label_number(3)  # Dish
    assert combo.currentData() == "moldy_seed"


def test_instance_radio_syncs_annos_default_combo(populated_project):
    """Instance-tab radio selection updates the Annos default-status combo and
    vice versa."""
    win, proj, anno, rebuild = populated_project
    win.dockcnt_anno.set_instance_statuses(["normal_seed", "moldy_seed"])
    win._sync_instance_tab()

    # radio -> Annos combo
    win.dockcnt_labels._instance_widgets["normal_seed"].radio.setChecked(True)
    assert win.dockcnt_anno.cmbox_default_instance.currentData() == "normal_seed"

    # Annos combo -> radio
    idx = win.dockcnt_anno.cmbox_default_instance.findData("moldy_seed")
    win.dockcnt_anno.cmbox_default_instance.setCurrentIndex(idx)
    assert win.dockcnt_labels.default_instance_status() == "moldy_seed"
