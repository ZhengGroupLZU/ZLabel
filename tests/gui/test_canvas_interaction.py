from __future__ import annotations

import pyqtgraph as pg
import pytest
from pyqtgraph.Qt.QtCore import Qt
from PySide6.QtTest import QTest

from zlabel.utils import (
    AnnotationType,
    DrawMode,
    KeypointVisible,
    PointResult,
    PolygonResult,
    RectangleResult,
    ResultType,
    StatusMode,
)
from zlabel.widgets import ResultUndoMode


# ---------------------------------------------------------------------------
# Drawing (CREATE mode)
# ---------------------------------------------------------------------------
def test_draw_rectangle_creates_result_and_undo(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    win.on_action_rectangle_triggered()
    assert win.canvas._status_mode == StatusMode.CREATE
    assert win.canvas._draw_mode == DrawMode.RECTANGLE

    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)

    assert len(anno.results) == 1
    r = next(iter(anno.results.values()))
    assert isinstance(r, RectangleResult)
    assert r.x == pytest.approx(10, abs=1.0)
    assert r.y == pytest.approx(10, abs=1.0)
    assert r.w == pytest.approx(20, abs=1.0)
    assert r.h == pytest.approx(15, abs=1.0)
    assert r.labels[0] is proj.crt_label
    assert win.undo_stack.count() == 1

    # Ctrl+Z removes it again
    win.on_action_undo_triggered()
    assert len(anno.results) == 0
    assert win.canvas.showing_items == {}


def test_draw_point_keypoint_mode(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    # switch annotation type to KeyPoint, then start drawing points
    win.cmbox_anno_type.setCurrentIndex(AnnotationType.POINT.value)
    win.on_action_point_triggered()
    assert win.canvas._draw_mode == DrawMode.POINT

    canvas_view["click"](win.canvas, (20, 20), qtbot)

    assert len(anno.results) == 1
    r = next(iter(anno.results.values()))
    assert isinstance(r, PointResult)
    assert r.x == pytest.approx(20, abs=1.0)
    assert r.y == pytest.approx(20, abs=1.0)
    assert r.visible == KeypointVisible.VISIBLE.value
    assert r.instance_id != 0  # auto-new instance


def test_draw_polygon_with_vertices_and_enter(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    win.on_action_polygon_triggered()

    canvas = win.canvas
    canvas.setFocus(Qt.FocusReason.OtherFocusReason)
    for pt in [(10, 10), (30, 10), (30, 25), (10, 25)]:
        canvas_view["click"](canvas, pt, qtbot)
    QTest.keyClick(canvas, Qt.Key.Key_Return)
    qtbot.wait(20)

    assert len(anno.results) == 1
    r = next(iter(anno.results.values()))
    assert isinstance(r, PolygonResult)
    assert r.closed
    assert len(r.points) == 4
    assert r.points[0] == pytest.approx((10, 10), abs=1.0)
    assert win.undo_stack.count() == 1


def test_polygon_drawing_undo_vertex_and_esc(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    win.on_action_polygon_triggered()
    canvas = win.canvas
    canvas.setFocus(Qt.FocusReason.OtherFocusReason)

    canvas_view["click"](canvas, (10, 10), qtbot)
    canvas_view["click"](canvas, (30, 10), qtbot)
    canvas_view["click"](canvas, (30, 25), qtbot)
    # backspace removes the last vertex
    QTest.keyClick(canvas, Qt.Key.Key_Backspace)
    qtbot.wait(10)
    assert len(canvas.polygon_points_committed) == 2

    # ESC cancels the whole drawing
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    qtbot.wait(10)
    assert canvas.current_item is None
    assert canvas.polygon_points_committed == []
    assert len(anno.results) == 0


def test_draw_rectangle_requires_label(populated_project, canvas_view, qtbot, mock_qt_dialogs):
    win, proj, anno, rebuild = populated_project
    proj.labels.clear()
    proj.key_label = None
    win.on_action_rectangle_triggered()

    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)

    assert len(anno.results) == 0
    assert any(kind == "warning" for kind, _ in mock_qt_dialogs.calls)


# ---------------------------------------------------------------------------
# Editing (EDIT mode)
# ---------------------------------------------------------------------------
def test_edit_move_rectangle_creates_modify_undo(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    r = RR.new(id_="r1", x=10, y=10, w=40, h=30, labels=[proj.crt_label], score=1.0)
    anno.add_result(r)
    rebuild()

    win.on_action_edit_triggered()
    assert win.canvas._status_mode == StatusMode.EDIT

    # click to select, then drag the body from its center (away from handles)
    canvas_view["click"](win.canvas, (30, 25), qtbot)
    canvas_view["drag"](win.canvas, (30, 25), (42, 33), qtbot)

    assert anno.results["r1"].x == pytest.approx(22, abs=2.0)
    assert anno.results["r1"].y == pytest.approx(18, abs=2.0)
    assert win.undo_stack.count() == 1

    win.on_action_undo_triggered()
    assert anno.results["r1"].x == pytest.approx(10, abs=1.0)
    assert anno.results["r1"].y == pytest.approx(10, abs=1.0)


def test_box_select_selects_visible_items(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    for i, (x, y) in enumerate([(5, 5), (30, 30)]):
        anno.add_result(RR.new(id_=f"r{i}", x=x, y=y, w=15, h=15, labels=[proj.crt_label], score=1.0))
    rebuild()

    win.on_action_edit_triggered()
    canvas_view["drag"](win.canvas, (0, 0), (40, 40), qtbot)

    ids = {i.id_ for i in win.canvas.selected_items}
    assert ids == {"r0", "r1"}


def test_box_select_inside_hidden_shape_does_not_pan(populated_project, canvas_view, qtbot):
    """Regression: pressing inside a hidden shape must draw a selection box,
    not pan the canvas or drag a visible item underneath."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import Label
    from zlabel.utils import RectangleResult as RR

    lbl_b = Label.new("B", "#00ff00")
    proj.labels[lbl_b.id] = lbl_b
    anno.add_result(RR.new(id_="ra", x=5, y=5, w=15, h=15, labels=[proj.crt_label], score=1.0))
    anno.add_result(RR.new(id_="rb", x=30, y=30, w=20, h=20, labels=[lbl_b], score=1.0))
    rebuild()
    win.canvas.showing_items["rb"].setVisible(False)

    win.on_action_edit_triggered()
    rng_before = [list(r) for r in win.canvas.view_box.viewRange()]
    canvas_view["drag"](win.canvas, (40, 40), (52, 52), qtbot)

    rng_after = [list(r) for r in win.canvas.view_box.viewRange()]
    assert rng_before == rng_after, "canvas must not pan"
    ra_pos = anno.results["ra"].getState()["pos"]
    rb_pos = anno.results["rb"].getState()["pos"]
    assert (ra_pos.x(), ra_pos.y()) == (5, 5), "visible rect must not move"
    assert (rb_pos.x(), rb_pos.y()) == (30, 30), "hidden rect must not move"


def test_delete_key_removes_and_undo_restores(populated_project, qtbot):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    for i in range(2):
        anno.add_result(RR.new(id_=f"r{i}", x=5 + i * 20, y=5 + i * 20, w=15, h=15, labels=[proj.crt_label], score=1.0))
    rebuild()

    win.on_action_edit_triggered()
    win.canvas.select_items(["r0", "r1"])
    win.canvas.setFocus(Qt.FocusReason.OtherFocusReason)
    QTest.keyClick(win.canvas, Qt.Key.Key_Delete)
    qtbot.wait(10)

    assert len(anno.results) == 0
    assert win.undo_stack.count() == 1

    win.on_action_undo_triggered()
    assert len(anno.results) == 2
    assert set(win.canvas.showing_items) == {"r0", "r1"}


def test_merge_rectangles(populated_project):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    for i, (x, y) in enumerate([(5, 5), (30, 30)]):
        anno.add_result(RR.new(id_=f"r{i}", x=x, y=y, w=15, h=15, labels=[proj.crt_label], score=1.0))
    rebuild()

    win.on_action_edit_triggered()
    win.canvas.select_items(["r0", "r1"])
    win.on_action_merge_triggered()

    assert len(anno.results) == 1
    merged = next(iter(anno.results.values()))
    assert isinstance(merged, RectangleResult)
    assert merged.x == pytest.approx(5, abs=1.0)
    assert merged.y == pytest.approx(5, abs=1.0)
    assert merged.w == pytest.approx(40, abs=1.0)
    assert merged.h == pytest.approx(40, abs=1.0)


# ---------------------------------------------------------------------------
# Keypoint operations
# ---------------------------------------------------------------------------
def _enter_keypoint_mode(win):
    win.cmbox_anno_type.setCurrentIndex(AnnotationType.POINT.value)
    assert win.settings.annotation_type == AnnotationType.POINT


def test_keypoint_visibility_shortcuts(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    _enter_keypoint_mode(win)
    win.on_action_point_triggered()
    canvas_view["click"](win.canvas, (20, 20), qtbot)
    win.on_action_edit_triggered()
    win.canvas.setFocus(Qt.FocusReason.OtherFocusReason)

    p = next(iter(anno.results.values()))
    assert isinstance(p, PointResult)
    assert p.visible == KeypointVisible.VISIBLE.value
    win.canvas.select_items([p.id])

    QTest.keyClick(win.canvas, Qt.Key.Key_L)
    qtbot.wait(10)
    QTest.keyClick(win.canvas, Qt.Key.Key_O)
    qtbot.wait(10)
    QTest.keyClick(win.canvas, Qt.Key.Key_X)
    qtbot.wait(10)
    assert anno.results[p.id].visible == KeypointVisible.MISSING.value

    win.on_action_undo_triggered()
    assert anno.results[p.id].visible == KeypointVisible.OCCLUDED.value


def test_group_and_ungroup_keypoints(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    _enter_keypoint_mode(win)
    win.on_action_point_triggered()
    for pt in [(10, 10), (20, 10), (30, 10)]:
        canvas_view["click"](win.canvas, pt, qtbot)

    ids = list(anno.results)
    assert len(ids) == 3
    assert {getattr(anno.results[i], "instance_id", 0) for i in ids} != {0}

    # group them into one instance (G / actionMerge on selected points)
    win.canvas.select_items(ids)
    win.on_action_merge_triggered()
    iids = {getattr(anno.results[i], "instance_id", 0) for i in ids}
    assert len(iids) == 1 and 0 not in iids

    # ungroup (U) — each keypoint becomes its own independent instance
    win.canvas.select_items(ids)
    QTest.keyClick(win.canvas, Qt.Key.Key_U)
    qtbot.wait(10)
    iids = {getattr(anno.results[i], "instance_id", 0) for i in ids}
    assert len(iids) == 3 and 0 not in iids


def test_polygon_instance_group_ctrl_g(populated_project):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    for i in range(2):
        anno.add_result(
            PR.new(id_=f"g{i}", points=[(5, 5), (25, 5), (25, 20), (5, 20)], closed=True, labels=[proj.crt_label])
        )
    rebuild()
    win.canvas.setFocus(Qt.FocusReason.OtherFocusReason)

    win.canvas.select_items(["g0", "g1"])
    win.on_group_instances()
    assert anno.results["g0"].instance_id == anno.results["g1"].instance_id != 0
    grouped_id = anno.results["g0"].instance_id
    assert grouped_id in anno.instances
    # the group carries a status; splitting must inherit it
    anno.instances[grouped_id] = "moldy_seed"

    win.on_split_instances()
    assert anno.results["g0"].instance_id != 0
    assert anno.results["g1"].instance_id != 0
    assert anno.results["g0"].instance_id != anno.results["g1"].instance_id
    assert anno.results["g0"].instance_id in anno.instances
    assert anno.results["g1"].instance_id in anno.instances
    assert grouped_id not in anno.instances, "the emptied group must be pruned"
    # each split instance inherits the original group's status
    assert anno.instances[anno.results["g0"].instance_id] == "moldy_seed"
    assert anno.instances[anno.results["g1"].instance_id] == "moldy_seed"

    # undo restores the original grouped instance
    win.on_action_undo_triggered()
    assert anno.results["g0"].instance_id == anno.results["g1"].instance_id == grouped_id
    assert grouped_id in anno.instances


def test_ctrl_g_toggles_group_and_split(populated_project, qtbot):
    """A single Ctrl+G shortcut groups a multi-selection into one instance and
    splits it back when the selection already forms one instance."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    for i, (x, y) in enumerate([(5, 5), (30, 30)]):
        anno.add_result(RR.new(id_=f"r{i}", x=x, y=y, w=15, h=15, labels=[proj.crt_label]))
    rebuild()

    # exactly one Ctrl+G shortcut, bound to the group/split toggle
    assert len(win._group_shortcuts) == 1
    win.canvas.setFocus(Qt.FocusReason.OtherFocusReason)

    # group via Ctrl+G
    win.canvas.select_items(["r0", "r1"])
    QTest.keyClick(win, Qt.Key.Key_G, Qt.KeyboardModifier.ControlModifier)
    qtbot.wait(20)
    assert anno.results["r0"].instance_id == anno.results["r1"].instance_id != 0

    # split again via the same Ctrl+G
    win.canvas.select_items(["r0", "r1"])
    QTest.keyClick(win, Qt.Key.Key_G, Qt.KeyboardModifier.ControlModifier)
    qtbot.wait(20)
    assert anno.results["r0"].instance_id != 0
    assert anno.results["r1"].instance_id != 0
    assert anno.results["r0"].instance_id != anno.results["r1"].instance_id


# ---------------------------------------------------------------------------
# View / canvas sync
# ---------------------------------------------------------------------------
def test_canvas_item_click_syncs_annos_and_label(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r1", x=10, y=10, w=20, h=15, labels=[proj.crt_label], score=1.0))
    rebuild()
    win.dockcnt_anno.rebuild(anno)

    win.on_action_edit_triggered()
    canvas_view["click"](win.canvas, (20, 17), qtbot)

    assert proj.key_result == "r1"
    assert proj.crt_result is anno.results["r1"]
    assert win.dockcnt_anno.selected_result_ids() == ["r1"]


def test_rotation_stays_in_image_space(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    win.spin_rotation.setValue(90)
    assert win.canvas._rotation == 90
    assert anno.image_rotation == 90

    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)
    r = next(iter(anno.results.values()))
    # Drawing rects are window-aligned: the drag covers a 15x20 window rect,
    # whose image-space anchor is the corner dragged first, mapped back through
    # the 90° view rotation. The stored coords stay in un-rotated image space.
    assert r.x == pytest.approx(10, abs=1.0)
    assert r.y == pytest.approx(25, abs=1.0)
    assert r.w == pytest.approx(15, abs=1.0)
    assert r.h == pytest.approx(20, abs=1.0)
    assert r.rotation == pytest.approx(-90, abs=0.01)
    # the drawn area is preserved (only the orientation changes)
    assert r.w * r.h == pytest.approx(15 * 20, rel=0.05)

    # rotating back to 0 leaves the stored coords untouched
    win.spin_rotation.setValue(0)
    assert anno.results[r.id].x == pytest.approx(10, abs=1.0)
    assert anno.results[r.id].y == pytest.approx(25, abs=1.0)


def test_rect_prompt_is_unrotated_bbox(populated_project, canvas_view, qtbot, monkeypatch):
    """Regression: with view rotation the rect prompt sent to the backend must
    be the axis-aligned bounding box of the drawn box in un-rotated image space,
    not the raw anchor + size (which is displaced under rotation)."""
    win, proj, anno, rebuild = populated_project

    captured: dict = {}

    class _FakeWorker:
        def __init__(self, **kw):
            captured.update(kw)

    monkeypatch.setattr(win, "run_sam_api_worker", lambda worker: None)
    monkeypatch.setattr("zlabel.widgets.mainwindow.ZSamPredictWorker", _FakeWorker)
    win.settings.sam_enabled = True

    # without rotation the prompt is the rect itself
    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (5, 5), (20, 20), qtbot)
    x, y, w, h = captured["rects"][0]
    assert x == pytest.approx(5, abs=1.0)
    assert y == pytest.approx(5, abs=1.0)
    assert w == pytest.approx(15, abs=1.0)
    assert h == pytest.approx(15, abs=1.0)

    # 90° view rotation: the drawn (10,10)-(30,25) window box is stored as
    # (10,25,15,20,rot=-90); its image-space bbox is (10,10)-(30,25) => (10,10,20,15).
    # (tolerance 2: the rotated drag drifts ~1-2px offscreen)
    captured.clear()
    win.spin_rotation.setValue(90)
    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)
    x, y, w, h = captured["rects"][0]
    assert x == pytest.approx(10, abs=2.0)
    assert y == pytest.approx(10, abs=2.0)
    assert w == pytest.approx(20, abs=2.0)
    assert h == pytest.approx(15, abs=2.0)


def test_undo_redo_keeps_canvas_synced(populated_project, canvas_view, qtbot):
    win, proj, anno, rebuild = populated_project
    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)
    r_id = next(iter(anno.results))
    assert isinstance(anno.results[r_id], RectangleResult)

    win.on_action_edit_triggered()
    canvas_view["click"](win.canvas, (20, 17), qtbot)
    canvas_view["drag"](win.canvas, (20, 17), (32, 29), qtbot)
    moved = (anno.results[r_id].x, anno.results[r_id].y)
    assert moved != (10, 10)

    win.on_action_undo_triggered()  # undo move
    assert (anno.results[r_id].x, anno.results[r_id].y) == pytest.approx((10, 10), abs=1.0)
    item = win.canvas.showing_items[r_id]
    item_pos = (item.getState()["pos"].x(), item.getState()["pos"].y())
    assert item_pos == pytest.approx((10, 10), abs=1.0)

    win.on_action_redo_triggered()  # redo move
    assert (anno.results[r_id].x, anno.results[r_id].y) == pytest.approx(moved, abs=1.0)
    item_pos = (item.getState()["pos"].x(), item.getState()["pos"].y())
    assert item_pos == pytest.approx(moved, abs=1.0)


def test_polygon_body_drag_is_1to1_and_persisted(populated_project, canvas_view, qtbot):
    """Regression: polygon body drag must move 1:1 with the mouse and keep the
    display in sync with the stored points after release."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    pts = [(10, 10), (40, 10), (40, 30), (10, 30)]
    anno.add_result(PR.new(id_="g1", points=pts, closed=True, labels=[proj.crt_label]))
    rebuild()

    win.on_action_edit_triggered()
    canvas_view["click"](win.canvas, (25, 20), qtbot)
    canvas_view["drag"](win.canvas, (25, 20), (35, 30), qtbot)

    item = win.canvas.showing_items["g1"]
    st = item.getState()
    assert tuple(st["points"][0]) == pytest.approx(tuple(anno.results["g1"].points[0]), abs=1.0)
    assert anno.results["g1"].points[0] != pytest.approx((10, 10), abs=0.1), "polygon should have moved"


def test_new_instances_get_default_status(populated_project, canvas_view, qtbot):
    """Drawing an annotation creates a new instance whose status comes from
    the Annos dock default-instance combo."""
    win, proj, anno, rebuild = populated_project
    proj.instance_statuses = ["normal_seed", "moldy_seed", "dead_seed"]
    win.dockcnt_anno.set_instance_statuses(proj.instance_statuses)
    # select a default type other than None
    combo = win.dockcnt_anno.cmbox_default_instance
    combo.setCurrentIndex(combo.findData("moldy_seed"))
    assert win.dockcnt_anno.default_instance_status() == "moldy_seed"

    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)

    r = next(iter(anno.results.values()))
    assert r.instance_id != 0
    assert anno.instances[r.instance_id] == "moldy_seed"

    # with None selected, new instances start without a status
    combo.setCurrentIndex(combo.findData(""))
    win.cmbox_anno_type.setCurrentIndex(AnnotationType.POINT.value)
    win.on_action_point_triggered()
    canvas_view["click"](win.canvas, (40, 20), qtbot)
    from zlabel.utils import PointResult

    p = next(r for r in anno.results.values() if isinstance(r, PointResult))
    assert anno.instances[p.instance_id] == ""


def test_sam_prompt_does_not_consume_instance_id(populated_project, canvas_view, qtbot, monkeypatch):
    """Regression: a SAM prompt rect must not allocate an instance id, so each
    SAM batch gets the next sequential id (1, 2, 3...) instead of 2, 4, 6..."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import AutoMode, PolygonResult
    from zlabel.widgets.zworker import SamWorkerResult

    win.settings.sam_enabled = True
    # don't run the real worker: the prompt flow must not allocate instances
    monkeypatch.setattr(win, "run_sam_api_worker", lambda worker: None)
    win.on_action_rectangle_triggered()

    ids = []
    for i, y in enumerate([5, 25, 45]):
        before = dict(anno.instances)
        canvas_view["drag"](win.canvas, (5, y), (20, y + 15), qtbot)
        assert anno.instances == before, f"prompt {i} must not create an instance"
        wr = [
            SamWorkerResult(
                anno_id="a",
                result=PolygonResult.new(
                    labels=[proj.crt_label],
                    points=[(1, 1), (5, 1), (5, 5), (1, 5)],
                    closed=True,
                    origin="SAM",
                ),
            )
        ]
        win.on_sam_worker_finished(wr)
        r = list(anno.results.values())[-1]
        ids.append(r.instance_id)

    assert ids == [1, 2, 3]


def test_draw_rect_reuses_hidden_item_without_corruption(populated_project, canvas_view, qtbot):
    """Drawing a new rect while an invisible rect exists reuses the hidden item
    without corrupting its annotation or pushing a spurious undo command."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import Label
    from zlabel.utils import RectangleResult as RR

    lbl_b = Label.new("B", "#00ff00")
    proj.labels[lbl_b.id] = lbl_b
    hid = RR.new(id_="hid", x=40, y=40, w=10, h=10, labels=[lbl_b])
    anno.add_result(hid)
    rebuild()
    win.canvas.showing_items["hid"].setVisible(False)

    undo_before = win.undo_stack.count()
    win.on_action_rectangle_triggered()
    canvas_view["drag"](win.canvas, (10, 10), (30, 25), qtbot)

    # the hidden annotation keeps its geometry, and only the ADD command is pushed
    assert anno.results["hid"].x == 40 and anno.results["hid"].y == 40
    assert win.undo_stack.count() == undo_before + 1
    new_id = next(i for i in anno.results if i != "hid")
    item = win.canvas.showing_items[new_id]
    assert item.isVisible()
    assert item.scene() is not None
    # the reused canvas item is now keyed under the new result id
    assert "hid" not in win.canvas.showing_items
    assert win.canvas.showing_items[new_id].id_ == new_id


def test_new_instance_id_fills_gaps(populated_project):
    """New instance ids fill the smallest unused positive id (gaps first),
    then increment past the max."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    anno.instances[1] = ""
    anno.instances[3] = ""
    assert win._new_instance_id() == 2  # gap between 1 and 3

    anno.instances[2] = ""
    assert win._new_instance_id() == 4  # no gaps below max -> max + 1

    # results also reserve ids (orphan instance removed)
    anno.instances.pop(1, None)
    anno.instances.pop(2, None)
    anno.instances.pop(3, None)
    anno.add_result(
        PR.new(
            id_="g",
            points=[(1, 1), (5, 1), (5, 5), (1, 5)],
            closed=True,
            labels=[proj.crt_label],
            instance_id=1,
        )
    )
    anno.instances[5] = ""
    assert win._new_instance_id() == 2


def test_new_individual_instances_fill_gaps(populated_project):
    """Splitting allocates each result a distinct gap-filling id (skipping used ids)."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    anno.instances[1] = "normal_seed"
    anno.instances[3] = "moldy_seed"
    g1 = PR.new(id_="g1", points=[(1, 1), (5, 1), (5, 5), (1, 5)], closed=True, labels=[proj.crt_label], instance_id=3)
    g2 = PR.new(id_="g2", points=[(1, 1), (5, 1), (5, 5), (1, 5)], closed=True, labels=[proj.crt_label], instance_id=1)
    anno.add_result(g1)
    anno.add_result(g2)

    result_new, inherited = win._new_individual_instances([g1, g2])
    ids = [r.instance_id for r in result_new]
    # used ids are {1, 3}; free: 2, 4 -> the two results get 2 and 4 (distinct)
    assert sorted(ids) == [2, 4]
    # each inherits its original group's status
    assert inherited[2] == "moldy_seed"
    assert inherited[4] == "normal_seed"
