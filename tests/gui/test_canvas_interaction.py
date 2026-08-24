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


def test_draw_polygon_double_click_finishes(populated_project, canvas_view, qtbot):
    """Left double-click finishes an in-progress polygon."""
    win, proj, anno, rebuild = populated_project
    win.on_action_polygon_triggered()
    canvas = win.canvas

    for pt in [(10, 10), (30, 10), (30, 25)]:
        canvas_view["click"](canvas, pt, qtbot)
    QTest.mouseDClick(
        canvas.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        canvas_view["to_view"](canvas, 10, 25),
    )
    qtbot.wait(20)

    assert len(anno.results) == 1
    r = next(iter(anno.results.values()))
    assert isinstance(r, PolygonResult)
    assert r.closed
    assert len(r.points) == 4
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


def test_edit_mode_fill_alpha(populated_project):
    """Entering EDIT mode uses 0.05 fill alpha; leaving restores the setting."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r1", x=10, y=10, w=20, h=20, labels=[proj.crt_label]))
    rebuild()

    item = win.canvas.showing_items["r1"]
    normal_alpha = win.canvas.alpha
    assert item.fill_color.alphaF() == pytest.approx(normal_alpha, abs=1e-3)

    win.canvas.set_status_mode(StatusMode.EDIT)
    assert item.fill_color.alphaF() == pytest.approx(0.05, abs=1e-3)

    win.canvas.set_status_mode(StatusMode.VIEW)
    assert item.fill_color.alphaF() == pytest.approx(normal_alpha, abs=1e-3)


def test_draw_fill_alpha_in_create_mode(populated_project):
    """Rectangles/polygons drawn in CREATE mode use 0.05 fill alpha."""
    win, proj, anno, rebuild = populated_project

    win.canvas.set_status_mode(StatusMode.CREATE)
    rect = win.canvas.new_rectangle(10, 10, 20, 20)
    assert rect.fill_color.alphaF() == pytest.approx(0.05, abs=1e-3)
    poly = win.canvas.new_polygon([(0, 0), (10, 0), (10, 10)])
    assert poly.fill_color.alphaF() == pytest.approx(0.05, abs=1e-3)

    win.canvas.set_status_mode(StatusMode.VIEW)
    rect2 = win.canvas.new_rectangle(0, 0, 5, 5)
    assert rect2.fill_color.alphaF() == pytest.approx(win.canvas.alpha, abs=1e-3)


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


def test_rapid_box_select_cleans_up(populated_project, canvas_view, qtbot):
    """Rapid repeated box selects must not leave a stale rubber-band item."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    for i in range(4):
        anno.add_result(RR.new(id_=f"r{i}", x=5 + i * 15, y=5 + i * 15, w=12, h=12, labels=[proj.crt_label]))
    rebuild()
    win.on_action_edit_triggered()

    for i in range(10):
        x0, y0, x1, y1 = (0, 0, 60, 60) if i % 2 == 0 else (60, 60, 0, 0)
        canvas_view["drag"](win.canvas, (x0, y0), (x1, y1), qtbot)
        assert win.canvas.selecting_item is None
        assert all(it.id_ in anno.results for it in win.canvas.selected_items)
        win.canvas.clear_selections()


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


def test_polygon_instance_bbox_union_and_label_updates(populated_project):
    """Instance-level polygon bbox: after grouping, one dashed bbox spans the
    union of all member polygons and its label shows the new instance id."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    anno.add_result(
        PR.new(
            id_="p1",
            points=[(5, 5), (25, 5), (25, 20), (5, 20)],
            closed=True,
            labels=[proj.crt_label],
            instance_id=1,
        )
    )
    anno.add_result(
        PR.new(
            id_="p2",
            points=[(30, 30), (45, 30), (45, 40), (30, 40)],
            closed=True,
            labels=[proj.crt_label],
            instance_id=2,
        )
    )
    rebuild()

    assert set(win.canvas._instance_bbox_items) == {1, 2}
    # individual polygon items do not render their own instance label anymore
    assert win.canvas.showing_items["p1"].label_text is None
    assert win.canvas.showing_items["p2"].label_text is None

    # hiding/showing the label removes/restores the instance bboxes
    win.on_label_visibility_toggled(proj.crt_label.id)
    assert win.canvas._instance_bbox_items == {}
    win.on_label_visibility_toggled(proj.crt_label.id)
    assert set(win.canvas._instance_bbox_items) == {1, 2}

    win.canvas.select_items(["p1", "p2"])
    win.on_group_instances()
    grouped_id = anno.results["p1"].instance_id
    assert grouped_id == anno.results["p2"].instance_id
    assert set(win.canvas._instance_bbox_items) == {grouped_id}
    bbox = win.canvas._instance_bbox_items[grouped_id]
    r = bbox.rect()
    assert (r.x(), r.y(), r.width(), r.height()) == (5.0, 5.0, 40.0, 35.0)
    assert bbox.label_text.text() == str(grouped_id)

    # splitting restores one bbox per polygon instance and updates their labels
    win.on_split_instances()
    ids = {anno.results["p1"].instance_id, anno.results["p2"].instance_id}
    assert len(ids) == 2
    assert set(win.canvas._instance_bbox_items) == ids
    for iid, item in win.canvas._instance_bbox_items.items():
        assert item.label_text.text() == str(iid)

    # undo restores the grouped instance and its single union bbox
    win.on_action_undo_triggered()
    assert set(win.canvas._instance_bbox_items) == {grouped_id}
    assert win.canvas._instance_bbox_items[grouped_id].label_text.text() == str(grouped_id)


def test_label_switch_refreshes_instance_bbox_color(populated_project):
    """Switching an instance's label refreshes bbox overlay + ID text color."""
    win, proj, anno, rebuild = populated_project
    from pyqtgraph.Qt.QtGui import QColor

    from zlabel.utils import Label
    from zlabel.utils import PolygonResult as PR

    lbl_a = proj.crt_label
    lbl_b = Label.new("B", "#00ff00")
    proj.labels[lbl_b.id] = lbl_b

    anno.add_result(
        PR.new(
            id_="p1",
            points=[(5, 5), (25, 5), (25, 20), (5, 20)],
            closed=True,
            labels=[lbl_a],
            instance_id=1,
        )
    )
    anno.add_result(
        PR.new(
            id_="p2",
            points=[(30, 30), (45, 30), (45, 40), (30, 40)],
            closed=True,
            labels=[lbl_a],
            instance_id=1,
        )
    )
    rebuild()

    bbox = win.canvas._instance_bbox_items[1]
    assert bbox.label_color == lbl_a.color

    win.canvas.select_items(["p1", "p2"])
    win.on_dock_label_item_double_clicked(lbl_b.id)

    bbox = win.canvas._instance_bbox_items[1]
    assert bbox.label_color == lbl_b.color
    assert bbox.label_text.brush().color().name().upper() == QColor(lbl_b.color).name().upper()
    assert win.canvas.showing_items["p1"].label_color == lbl_b.color
    assert win.canvas.showing_items["p2"].label_color == lbl_b.color


def test_rectangle_instance_label_updates_after_group(populated_project):
    """Rectangle instance numbers at the top-left update after group/split."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r0", x=5, y=5, w=10, h=10, labels=[proj.crt_label], instance_id=1))
    anno.add_result(RR.new(id_="r1", x=30, y=30, w=10, h=10, labels=[proj.crt_label], instance_id=2))
    rebuild()

    win.canvas.select_items(["r0", "r1"])
    win.on_group_instances()
    grouped_id = anno.results["r0"].instance_id
    assert grouped_id == anno.results["r1"].instance_id
    assert win.canvas.showing_items["r0"].label_text.text() == str(grouped_id)
    assert win.canvas.showing_items["r1"].label_text.text() == str(grouped_id)

    win.on_split_instances()
    assert win.canvas.showing_items["r0"].label_text.text() == str(anno.results["r0"].instance_id)
    assert win.canvas.showing_items["r1"].label_text.text() == str(anno.results["r1"].instance_id)


def test_group_instances_uses_min_instance_id(populated_project):
    """Merging keeps the smallest existing instance id as the merged id."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    anno.add_result(
        PR.new(
            id_="a",
            points=[(5, 5), (25, 5), (25, 20), (5, 20)],
            closed=True,
            labels=[proj.crt_label],
            instance_id=5,
        )
    )
    anno.add_result(
        PR.new(
            id_="b",
            points=[(30, 30), (45, 30), (45, 40), (30, 40)],
            closed=True,
            labels=[proj.crt_label],
            instance_id=2,
        )
    )
    anno.instances[2] = "moldy_seed"
    rebuild()

    win.canvas.select_items(["a", "b"])
    win.on_group_instances()
    assert anno.results["a"].instance_id == anno.results["b"].instance_id == 2
    assert 2 in anno.instances
    assert anno.instances[2] == "moldy_seed"
    assert 5 not in anno.instances


def test_group_keypoints_uses_min_instance_id(populated_project):
    """Grouping keypoints also keeps the smallest existing instance id."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PointResult as PR

    anno.add_result(PR.new(id_="p1", x=10, y=10, labels=[proj.crt_label], instance_id=7))
    anno.add_result(PR.new(id_="p2", x=20, y=10, labels=[proj.crt_label], instance_id=3))
    rebuild()

    win.canvas.select_items(["p1", "p2"])
    win.on_group_points()
    assert anno.results["p1"].instance_id == anno.results["p2"].instance_id == 3


def test_group_instances_syncs_canvas_once(populated_project, monkeypatch):
    """Merging many instances must rebuild tree/bboxes once, not per result."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    ids = []
    for i in range(5):
        rid = f"g{i}"
        anno.add_result(
            PR.new(
                id_=rid,
                points=[(5 + i * 5, 5), (25 + i * 5, 5), (25 + i * 5, 20), (5 + i * 5, 20)],
                closed=True,
                labels=[proj.crt_label],
                instance_id=i + 1,
            )
        )
        ids.append(rid)
    rebuild()

    calls = 0
    original = win._sync_canvas_instance_labels

    def counting(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(win, "_sync_canvas_instance_labels", counting)
    win.canvas.select_items(ids)
    win.on_group_instances()
    assert calls == 1


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


def test_polygon_vertex_handle_consumes_clicks(populated_project, canvas_view, qtbot):
    """Vertex handles accept left clicks so a click on a vertex does not deselect
    the polygon: the handle consumes the click instead of it falling through to
    the polygon's mouseClickEvent (which toggles the selection off)."""
    win, proj, anno, rebuild = populated_project
    from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
    from pyqtgraph.Qt.QtCore import QPointF, Qt

    from zlabel.utils import PolygonResult as PR

    pr = PR.new(id_="p1", points=[(10, 10), (20, 10), (20, 20), (10, 20)], closed=True, labels=[proj.crt_label])
    anno.add_result(pr)
    rebuild()
    win.on_action_edit_triggered()
    canvas_view["click"](win.canvas, (15, 15), qtbot)
    item = win.canvas.showing_items["p1"]
    assert item.isSelected()
    assert item.handles, "selected polygon must show vertex handles"

    handle = item.handles[0]["item"]
    # the handle must accept left-button clicks (regression: it used to be
    # NoButton, so clicks on a vertex fell through to the polygon)
    assert Qt.MouseButton.LeftButton in handle.acceptedMouseButtons() & Qt.MouseButton.LeftButton

    class _Press:
        def scenePos(self):
            return QPointF(0, 0)

        def screenPos(self):
            return QPointF(0, 0)

        def button(self):
            return Qt.MouseButton.LeftButton

        def buttons(self):
            return Qt.MouseButton.LeftButton

        def modifiers(self):
            return Qt.KeyboardModifier.NoModifier

    click = MouseClickEvent(_Press())
    handle.mouseClickEvent(click)
    assert click.isAccepted(), "vertex handle must consume the click (not propagate to the polygon)"


def test_large_image_downsampled_for_display(populated_project):
    """Images with a long edge > DISPLAY_MAX_SIDE are downsampled for display
    while the canvas coordinate space stays in full-resolution pixels."""
    import numpy as np

    win, proj, anno, rebuild = populated_project
    h, w = 6000, 4000
    big = np.random.default_rng(0).integers(0, 255, (h, w, 3), dtype=np.uint8)
    canvas = win.canvas
    canvas.update_image(big)

    # the display data is downsampled to the 2560 long edge
    dh, dw = canvas.image_item.image.shape[:2]
    assert max(dh, dw) <= 2560
    assert canvas._image_hw == (h, w)
    assert canvas._img_scale > 1.0

    # fit_view keeps the full-resolution data range (coordinate space unchanged)
    canvas.fit_view()
    rng = canvas.view_box.viewRange()
    assert rng[0][0] <= 0 and rng[0][1] >= 4000
    assert rng[1][0] <= 0 and rng[1][1] >= 6000

    # a full-res coordinate round-trips through the mouse mapping unchanged
    from pyqtgraph.Qt.QtCore import QPointF

    scene_pt = canvas.view_box.mapViewToScene(QPointF(2000, 3000))
    p = canvas.map_scene_to_view(scene_pt)
    assert p.x() == pytest.approx(2000, abs=1.0)
    assert p.y() == pytest.approx(3000, abs=1.0)


def test_polygon_vertex_handles_are_circles_and_edit_uses_arrow_cursor(populated_project, canvas_view, qtbot):
    """Vertex handles render as circles; edit mode uses the normal arrow cursor."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    pr = PR.new(id_="p1", points=[(10, 10), (20, 10), (20, 20), (10, 20)], closed=True, labels=[proj.crt_label])
    anno.add_result(pr)
    rebuild()

    win.on_action_edit_triggered()
    assert win.canvas._status_mode == StatusMode.EDIT
    assert win.canvas.cursor().shape() == Qt.CursorShape.ArrowCursor

    canvas_view["click"](win.canvas, (15, 15), qtbot)
    item = win.canvas.showing_items["p1"]
    handle = item.handles[0]["item"]
    # circle handle: type stays "f" (so pyqtgraph moves the free handle) but
    # sides==0 makes buildPath draw an ellipse instead of a diamond
    assert handle.typ == "f"
    assert handle.sides == 0


def test_circle_handle_drag_edits_vertex(populated_project, canvas_view, qtbot):
    """The circle vertex handle is hit-testable and a handle drag still moves
    the vertex and keeps the polygon selected."""
    win, proj, anno, rebuild = populated_project
    from pyqtgraph.Qt.QtCore import QPointF, Qt

    from zlabel.utils import PolygonResult as PR

    pr = PR.new(id_="p1", points=[(10, 10), (20, 10), (20, 20), (10, 20)], closed=True, labels=[proj.crt_label])
    anno.add_result(pr)
    rebuild()
    win.on_action_edit_triggered()
    canvas_view["click"](win.canvas, (15, 15), qtbot)
    item = win.canvas.showing_items["p1"]
    assert item.isSelected()

    handle = item.handles[0]["item"]
    assert handle.isVisible()
    assert not handle.shape().boundingRect().isEmpty()

    # simulate a real handle drag: move point (finish=False) then stateChangeFinished
    hp = item.mapToScene(handle.pos())
    item.movePoint(handle, hp + QPointF(5, 5), modifiers=Qt.KeyboardModifier.NoModifier, finish=False, coords="scene")
    item.stateChangeFinished()
    qtbot.wait(20)
    pts = item.getState()["points"]
    assert pts[0] != (10.0, 10.0), "dragged vertex must move"
    assert item.isSelected(), "selection must survive the vertex drag"


def test_polygon_handle_grab_near_vertex(populated_project, canvas_view, qtbot):
    """A press near (but not exactly on) a vertex handle grabs the handle, so no
    selection box starts; a drag still edits the vertex."""
    win, proj, anno, rebuild = populated_project
    from pyqtgraph.Qt.QtCore import QPointF, Qt

    from zlabel.utils import PolygonResult as PR

    pr = PR.new(id_="p1", points=[(10, 10), (20, 10), (20, 20), (10, 20)], closed=True, labels=[proj.crt_label])
    anno.add_result(pr)
    rebuild()
    win.on_action_edit_triggered()
    canvas_view["click"](win.canvas, (15, 15), qtbot)
    item = win.canvas.showing_items["p1"]
    assert item.isSelected()
    handle = item.handles[0]["item"]

    # item_at_point near the vertex (inside the grab disk, off the exact circle)
    hit = win.canvas.item_at_point(QPointF(10.5, 10.5))
    assert hit is handle, "press near a vertex must hit the handle, not the polygon/None"

    # drag edits the vertex and keeps selection
    hp = item.mapToScene(handle.pos())
    item.movePoint(handle, hp + QPointF(5, 5), modifiers=Qt.KeyboardModifier.NoModifier, finish=False, coords="scene")
    item.stateChangeFinished()
    qtbot.wait(20)
    pts = item.getState()["points"]
    assert pts[0] != (10.0, 10.0)
    assert item.isSelected()


def test_backspace_deletes_hovered_polygon_vertex(populated_project, qtbot):
    """Backspace in EDIT mode deletes the hovered polygon vertex."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    anno.add_result(
        PR.new(
            id_="g1",
            points=[(10, 10), (30, 10), (30, 25), (10, 25)],
            closed=True,
            labels=[proj.crt_label],
        )
    )
    rebuild()
    win.on_action_edit_triggered()
    win.canvas.select_items(["g1"])
    poly = win.canvas.showing_items["g1"]
    assert poly.handles

    handle = poly.handles[2]["item"]
    handle.hovered = True
    QTest.keyClick(win.canvas, Qt.Key.Key_Backspace)
    qtbot.wait(20)

    r = anno.results["g1"]
    assert len(r.points) == 3
    remaining = {tuple(round(v, 1) for v in p) for p in r.points}
    assert (30.0, 25.0) not in remaining


def test_backspace_ignored_without_hovered_polygon_vertex(populated_project, qtbot):
    """Backspace is ignored when no polygon vertex is hovered."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR

    anno.add_result(
        PR.new(
            id_="g1",
            points=[(10, 10), (30, 10), (30, 25), (10, 25)],
            closed=True,
            labels=[proj.crt_label],
        )
    )
    rebuild()
    win.on_action_edit_triggered()
    win.canvas.select_items(["g1"])
    poly = win.canvas.showing_items["g1"]
    assert poly.handles

    QTest.keyClick(win.canvas, Qt.Key.Key_Backspace)
    qtbot.wait(20)
    assert len(anno.results["g1"].points) == 4


def test_polygon_create_uses_dot_cursor(populated_project):
    """Polygon drawing uses the dot.svg custom cursor; other modes keep defaults."""
    win, proj, anno, rebuild = populated_project

    win.on_action_polygon_triggered()
    assert win.canvas.cursor().shape() == Qt.CursorShape.BlankCursor

    win.on_action_rectangle_triggered()
    assert win.canvas.cursor().shape() == Qt.CursorShape.CrossCursor

    win.on_action_edit_triggered()
    assert win.canvas.cursor().shape() == Qt.CursorShape.ArrowCursor
