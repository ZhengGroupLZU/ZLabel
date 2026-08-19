from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtCore import QMimeData, QPointF, Qt
from pyqtgraph.Qt.QtGui import QDragMoveEvent, QDropEvent

from zlabel.utils import (
    Annotation,
    AnnotationType,
    Label,
    PolygonResult,
    RectangleResult,
    Task,
)
from zlabel.utils.geometry import rotate_point
from zlabel.widgets.dock_timeline import INSTANCE_MIME, ZDockTimelineContent
from zlabel.widgets.mainwindow import CopyOptions


def _seed_label(proj) -> Label:
    from zlabel.utils import Label

    lbl = Label.new("Seed", "#ff0000")
    proj.labels[lbl.id] = lbl
    return lbl


def _dish_label(proj) -> Label:
    from zlabel.utils import Label

    lbl = Label.new("Dish", "#911eb4")
    proj.labels[lbl.id] = lbl
    return lbl


def _group(proj, n=2, group="g"):
    """Two frames D1/D2 in the group ``g``; returns (tasks, annos)."""
    tasks, annos = [], []
    for i in range(1, n + 1):
        t = Task(id=i, filename=f"D{i}.png", anno_id=f"d{i}", labels=[], group=group, day=i)
        proj.tasks[t.anno_id] = t
        a = Annotation(id=t.anno_id, image_path=t.filename, original_width=64, original_height=64)
        t.anno = a
        tasks.append(t)
        annos.append(a)
    return tasks, annos


def test_neighbor_task_prev_next(main_window):
    win = main_window
    tasks, _ = _group(win.proj, n=3)
    d1, d2, d3 = tasks
    assert win._prev_task_for_copy(d2) is d1
    assert win._next_task_for_copy(d2) is d3
    assert win._neighbor_task_for_copy(d2, -1) is d1
    assert win._neighbor_task_for_copy(d2, 1) is d3
    assert win._prev_task_for_copy(d1) is None
    assert win._next_task_for_copy(d3) is None


def test_copy_from_prev_keeps_instance_identity(main_window):
    """Copying keeps the source instance_id (the cross-frame identity)."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    lbl_dish = _dish_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    win.proj.key_task = "d1"

    a1.add_result(
        PolygonResult.new(
            id_="dish",
            points=[(20, 20), (44, 20), (44, 44), (20, 44), (32, 18)],
            closed=True,
            labels=[lbl_dish],
        )
    )
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(25, 25), (30, 25), (30, 30), (25, 30), (27, 24)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a1.add_result(
        PolygonResult.new(
            id_="r1",
            points=[(35, 35), (40, 35), (40, 40), (35, 40), (37, 34)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a1.instances[1] = "normal_seed"

    win.proj.key_task = "d2"
    win._copy_from_frame(
        d1,
        CopyOptions(
            direction=-1,
            opts={"dish", "time", "parts"},
            angle=90.0,
            scale=1.0,
            src_center=(32, 32),
            tgt_center=(32, 32),
        ),
    )
    seeds = [
        r
        for r in a2.results.values()
        if isinstance(r, PolygonResult) and (r.labels[0].name if r.labels else "") == "Seed"
    ]
    assert len(seeds) == 2
    # same cross-frame instance id as the source frame
    assert {r.instance_id for r in seeds} == {1}
    # status carried over
    assert a2.instances[1] == "normal_seed"
    # geometry rotated 90 deg around (32,32)
    assert seeds[0].points[0] == rotate_point((25, 25), 90.0, (32, 32))
    # dish copied but not an instance
    dish = next(
        r
        for r in a2.results.values()
        if isinstance(r, PolygonResult) and (r.labels[0].name if r.labels else "") == "Dish"
    )
    assert dish.instance_id == 0


def test_copy_from_next(main_window):
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a2.add_result(
        PolygonResult.new(
            id_="s", points=[(5, 5), (9, 5), (9, 9), (5, 9), (7, 4)], closed=True, labels=[lbl_seed], instance_id=1
        )
    )
    a2.instances[1] = "moldy_seed"
    win.proj.key_task = "d1"
    win._copy_from_frame(
        d2,
        CopyOptions(direction=1, opts={"parts"}, angle=0.0, scale=1.0, src_center=(0, 0), tgt_center=(0, 0)),
    )
    copied = next(iter(a1.results.values()))
    assert copied.instance_id == 1
    assert a1.instances[copied.instance_id] == "moldy_seed"


def test_new_instance_id_is_per_frame(main_window):
    """Instance ids are allocated per frame: each image starts at 1."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    for i in (1, 2, 3):
        a1.add_result(
            PolygonResult.new(
                id_=f"s{i}",
                points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
                closed=True,
                labels=[lbl_seed],
                instance_id=i,
            )
        )
        a1.instances[i] = "normal_seed"

    # d1's next free id is 4 (fills the gap upward in this frame only)
    proj.key_task = "d1"
    assert win._new_instance_id() == 4
    # d2 has no instances yet -> starts at 1, not at the group's max
    proj.key_task = "d2"
    assert win._new_instance_id() == 1
    # per-frame gap filling: after claiming 1 in d2 the next id is 2
    a2.add_result(
        PolygonResult.new(
            id_="t", points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)], closed=True, labels=[lbl_seed], instance_id=1
        )
    )
    assert win._new_instance_id() == 2


def test_copy_from_prev_skips_colliding_instance(main_window):
    """Copying a frame whose instance id already exists in the target skips it."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    lbl_dish = _dish_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="dish",
            points=[(20, 20), (44, 20), (44, 44), (20, 44), (32, 18)],
            closed=True,
            labels=[lbl_dish],
        )
    )
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(25, 25), (30, 25), (30, 30), (25, 30), (27, 24)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a1.instances[1] = "normal_seed"
    # d2 already has its own instance 1 (a different seed)
    a2.add_result(
        PolygonResult.new(
            id_="s1x",
            points=[(5, 5), (9, 5), (9, 9), (5, 9), (7, 4)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a2.instances[1] = "moldy_seed"

    win.proj.key_task = "d2"
    win._copy_from_frame(
        d1,
        CopyOptions(
            direction=-1,
            opts={"dish", "time", "parts"},
            angle=0.0,
            scale=1.0,
            src_center=(0, 0),
            tgt_center=(0, 0),
        ),
    )
    # the colliding seed instance is skipped, but the dish (no instance) is copied
    seeds = [
        r
        for r in a2.results.values()
        if isinstance(r, PolygonResult) and (r.labels[0].name if r.labels else "") == "Seed"
    ]
    assert [r.id for r in seeds] == ["s1x"]
    assert [r.instance_id for r in seeds] == [1]
    dishes = [
        r
        for r in a2.results.values()
        if isinstance(r, PolygonResult) and (r.labels[0].name if r.labels else "") == "Dish"
    ]
    assert len(dishes) == 1
    assert a2.instances == {1: "moldy_seed"}


def test_timeline_rows_instances_and_cells(main_window):
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a1.instances[1] = "normal_seed"
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    a2.instances[2] = "moldy_seed"

    dock = ZDockTimelineContent(win._load_anno_for_task, lambda name: None)
    dock.set_group(proj, "g", tasks)
    assert dock.table.rowCount() == 3  # instances 1 and 2 + trailing empty row
    assert dock.table.columnCount() == 3  # index + D1 + D2
    assert dock.table.horizontalHeaderItem(1).text() == "D1"
    assert dock.table.horizontalHeaderItem(2).text() == "D2"
    # rows sorted by instance id; index cell colored by the label
    assert dock.table.item(0, 0).text() == "1"
    assert dock.table.item(0, 0).background().color().name() == "#ff0000"
    assert dock.table.item(0, 1).text().startswith("1")  # D1 contains instance 1
    assert dock.table.item(0, 2).text() == "·"  # absent in D2
    assert dock.table.item(1, 2).text().startswith("2")
    # the trailing row is blank and inert
    assert dock.table.item(2, 0).text() == ""
    assert dock.table.item(2, 1).text() == ""

    opened = []
    dock.sigOpenInstance.connect(lambda anno_id, iid: opened.append((anno_id, iid)))
    dock.table.itemClicked.emit(dock.table.item(0, 1))
    assert opened == [("d1", 1)]


def test_timeline_gap_rows(main_window):
    """Rows always run 1..max instance id; gaps in the middle are empty rows."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a1.add_result(
        PolygonResult.new(
            id_="s3",
            points=[(6, 6), (9, 6), (9, 9), (6, 9), (7, 5)],
            closed=True,
            labels=[lbl_seed],
            instance_id=3,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s3b",
            points=[(6, 6), (9, 6), (9, 9), (6, 9), (7, 5)],
            closed=True,
            labels=[lbl_seed],
            instance_id=3,
        )
    )

    dock = ZDockTimelineContent(win._load_anno_for_task, lambda name: None)
    dock.set_group(proj, "g", tasks)
    # instances 1 and 3 -> rows 1..3, row 2 is the gap, plus a trailing empty row
    assert dock.table.rowCount() == 4
    assert dock.table.item(0, 0).text() == "1"
    assert dock.table.item(1, 0).text() == "2"
    assert dock.table.item(2, 0).text() == "3"
    # filled rows: D1 has 1 and 3, D2 has 3
    assert dock.table.item(0, 1).text().startswith("1")
    assert dock.table.item(2, 1).text().startswith("3")
    assert dock.table.item(2, 2).text().startswith("3")
    # gap row 2: all frame cells are dim and inert (no jump)
    assert dock.table.item(1, 1).text() == "·"
    assert dock.table.item(1, 2).text() == "·"
    # trailing empty row is blank and inert
    assert dock.table.item(3, 0).text() == ""
    assert dock.table.item(3, 1).text() == ""
    assert dock.table.item(3, 2).text() == ""
    opened = []
    dock.sigOpenInstance.connect(lambda anno_id, iid: opened.append((anno_id, iid)))
    dock.table.itemClicked.emit(dock.table.item(1, 1))
    assert opened == []  # gap row does nothing
    # index cell of a gap row is also inert
    dock.table.itemClicked.emit(dock.table.item(1, 0))
    assert opened == []
    # clicking the trailing empty row does nothing either
    dock.table.itemClicked.emit(dock.table.item(3, 1))
    assert opened == []


def test_timeline_cell_move_signal(main_window):
    """Dragging a cell emits a cell-move request carrying only (anno, iid, target row)."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    dock = ZDockTimelineContent(win._load_anno_for_task, lambda name: None)
    dock.set_group(proj, "g", tasks)
    moved = []
    dock.sigCellMoved.connect(lambda a, i, r: moved.append((a, i, r)))
    # drop column is ignored: only (src anno, src iid, target row) is emitted
    dock.table.sigCellMoved.emit("d2", 2, 3)
    assert moved == [("d2", 2, 3)]


def test_timeline_drag_move_and_drop_accepted(main_window, qtbot):
    """Drag moves/drops over an instance cell are accepted (no forbidden cursor),
    and the drop emits the cell-move request for the target row."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    dock = ZDockTimelineContent(win._load_anno_for_task, lambda name: None)
    dock.set_group(proj, "g", tasks)
    table = dock.table
    dock.resize(400, 200)
    dock.show()
    qtbot.wait(30)

    moved = []
    dock.sigCellMoved.connect(lambda a, i, r: moved.append((a, i, r)))
    item = table.item(1, 2)  # instance 2 in the D2 column
    mime = QMimeData()
    mime.setData(INSTANCE_MIME, b"d2|2")
    pos = table.visualItemRect(item).center()

    # without the dragMoveEvent override the view rejects the move (forbidden
    # cursor) because the items lack ItemIsDropEnabled
    ev_move = QDragMoveEvent(
        pos, Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    )
    table.dragMoveEvent(ev_move)
    assert ev_move.isAccepted()

    ev_drop = QDropEvent(pos, Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    table.dropEvent(ev_drop)
    assert ev_drop.isAccepted()
    assert moved == [("d2", 2, 2)]  # target id = displayed row number (row()+1)


def test_cell_move_renumber(main_window):
    """Dragging to an empty row in the source frame renumbers the instance there."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    a2.instances[2] = "moldy_seed"
    proj.key_task = "d2"
    # row 1 is empty in d2 -> instance 2 becomes instance 1
    win.on_cell_moved("d2", 2, 1)
    assert {r.instance_id for r in a2.results.values()} == {1}
    assert a2.instances == {1: "moldy_seed"}
    # d1 untouched
    assert {r.instance_id for r in a1.results.values()} == {1}


def test_cell_move_swap(main_window):
    """Dragging onto an occupied row in the source frame swaps the two instances."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s3",
            points=[(6, 6), (9, 6), (9, 9), (6, 9), (7, 5)],
            closed=True,
            labels=[lbl_seed],
            instance_id=3,
        )
    )
    a2.instances[2] = "normal_seed"
    a2.instances[3] = "moldy_seed"
    proj.key_task = "d2"
    # row 3 occupied in d2 -> swap ids (and statuses) of instances 2 and 3
    win.on_cell_moved("d2", 2, 3)
    assert a2.results["s2"].instance_id == 3
    assert a2.results["s3"].instance_id == 2
    assert a2.instances[2] == "moldy_seed"
    assert a2.instances[3] == "normal_seed"


def test_cell_move_undo_restores_id_and_status(main_window):
    """Renumber/swap support undo/redo, restoring both ids and statuses."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    a2.instances[2] = "moldy_seed"
    proj.key_task = "d2"

    win.on_cell_moved("d2", 2, 1)
    assert {r.instance_id for r in a2.results.values()} == {1}
    assert a2.instances == {1: "moldy_seed"}

    win.undo_stack.undo()
    assert {r.instance_id for r in a2.results.values()} == {2}
    assert a2.instances == {2: "moldy_seed"}

    win.undo_stack.redo()
    assert {r.instance_id for r in a2.results.values()} == {1}
    assert a2.instances == {1: "moldy_seed"}


def test_cell_move_noncurrent_frame(main_window):
    """Renumbering a cell in a non-current frame only changes that frame."""
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    a2.instances[2] = "moldy_seed"
    proj.key_task = "d1"  # current frame is d1; we edit d2's cell
    win.on_cell_moved("d2", 2, 1)
    assert {r.instance_id for r in a2.results.values()} == {1}
    assert a2.instances == {1: "moldy_seed"}
    # d1's instance 1 is its own (per-frame numbering), untouched by d2's edit
    assert a1.results["s1"].instance_id == 1
    # undo restores d2 even though it is not the current frame
    win.undo_stack.undo()
    assert {r.instance_id for r in a2.results.values()} == {2}
    assert a2.instances == {2: "moldy_seed"}


def test_on_instance_open_jumps_and_selects(main_window):
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a2.add_result(
        PolygonResult.new(
            id_="s2",
            points=[(1, 1), (5, 1), (5, 5), (1, 5), (3, 0)],
            closed=True,
            labels=[lbl_seed],
            instance_id=2,
        )
    )
    a2.instances[2] = "moldy_seed"
    proj.key_task = "d1"  # current frame is d1 (empty); crt_anno is a1

    # open instance 2 in d2
    win._skip_copy_anno = ""
    win.on_instance_open("d2", 2)
    assert proj.key_task == "d2"
    selected = {i.id_ for i in win.canvas.selected_items}
    assert "s2" in selected


def test_estimate_copy_alignment_from_dish_and_number(main_window):
    """The dish+Number references fully determine the similarity transform."""
    win = main_window
    proj = win.proj
    lbl_dish = _dish_label(proj)

    tasks, annos = _group(proj)
    a1, a2 = annos
    # source: dish centered at (10,10), number at (30,10) -> vector (20, 0)
    a1.add_result(
        PolygonResult.new(
            id_="dish",
            points=[(5, 5), (10, 4), (15, 5), (15, 15), (10, 16), (5, 15)],
            closed=True,
            labels=[lbl_dish],
        )
    )
    a1.add_result(RectangleResult.new(id_="num", x=28, y=8, w=4, h=4, labels=[Label.new("Number")]))
    # target: dish half the size centered at (30,30), number at (20,30) -> vector (-10, 0)
    # => rotation 180 deg, scale = 10/20 = 0.5, center shift (10,10)->(30,30)
    a2.add_result(
        PolygonResult.new(
            id_="dish",
            points=[(27.5, 27.5), (30, 27), (32.5, 27.5), (32.5, 32.5), (30, 33), (27.5, 32.5)],
            closed=True,
            labels=[lbl_dish],
        )
    )
    a2.add_result(RectangleResult.new(id_="num", x=18, y=28, w=4, h=4, labels=[Label.new("Number")]))

    angle, scale, src_c, tgt_c, ang_rel, scale_rel = win._estimate_copy_alignment(a1, a2)
    assert ang_rel and scale_rel
    assert angle == pytest.approx(180, abs=1.0)
    assert scale == pytest.approx(0.5, abs=0.1)
    assert src_c == pytest.approx((10, 10), abs=1.0)
    assert tgt_c == pytest.approx((30, 30), abs=1.0)


def test_copy_from_prev_with_scale_and_center_shift(main_window):
    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    a1.add_result(
        PolygonResult.new(
            id_="s1",
            points=[(25, 25), (30, 25), (30, 30), (25, 30), (27, 24)],
            closed=True,
            labels=[lbl_seed],
            instance_id=1,
        )
    )
    a1.instances[1] = "normal_seed"
    win.proj.key_task = "d2"

    # scale 1.5 around source center (20,20) mapped to target center (50,50)
    win._copy_from_frame(
        d1,
        CopyOptions(
            direction=-1,
            opts={"parts"},
            angle=0.0,
            scale=1.5,
            src_center=(20, 20),
            tgt_center=(50, 50),
        ),
    )
    seed = next(iter(a2.results.values()))
    # p=(25,25): (p-src)=(5,5) *1.5 = (7.5,7.5) + tgt = (57.5, 57.5)
    assert seed.points[0] == pytest.approx((57.5, 57.5), abs=1e-6)
    assert seed.instance_id == 1
    assert a2.instances[seed.instance_id] == "normal_seed"


def test_timeline_dock_at_bottom(main_window):
    """The Timeline panel is a bottom timeline dock titled 'Timeline'."""
    win = main_window

    assert win.dock_timeline.windowTitle() == "Timeline"
    assert win.actionTimeline.text() == "Timeline"
    assert win.dockWidgetArea(win.dock_timeline) == Qt.DockWidgetArea.BottomDockWidgetArea


def test_new_instance_refreshes_timeline(main_window):
    """Creating a new annotation instance updates the timeline immediately."""
    import numpy as np
    from PIL import Image as _Image

    win = main_window
    proj = win.proj
    lbl_seed = _seed_label(proj)
    proj.key_label = lbl_seed.id
    tasks, annos = _group(proj)
    d1, d2 = tasks
    a1, a2 = annos
    proj.key_task = "d1"
    win._image_cache["D1.png"] = _Image.fromarray(np.full((64, 64, 3), 128, dtype=np.uint8))
    win._refresh_timeline()
    dock = win.dockcnt_timeline
    assert dock.table.rowCount() == 1  # just the trailing empty row

    # manual polygon creation allocates a new instance -> timeline gets a row
    win.on_canvas_polygon_created({
        "id": "p1",
        "pos": QPointF(10, 10),
        "size": QPointF(1, 1),
        "angle": 0,
        "points": [QPointF(x, y) for x, y in [(10, 10), (20, 10), (20, 20), (10, 20)]],
        "closed": True,
    })
    assert dock.table.rowCount() == 2  # instance 1 + trailing empty row
    assert dock.table.item(0, 1).text().startswith("1")  # instance 1 in D1

    # manual point (keypoint) creation also refreshes the timeline
    win.settings.annotation_type = AnnotationType.POINT
    win.on_canvas_point_created({"id": "k1", "pos": QPointF(30, 30)})
    assert dock.table.rowCount() == 3  # instances 1,2 + trailing empty row
    assert dock.table.item(1, 1).text().startswith("2")  # instance 2 in D1


def test_sam_rect_results_each_get_own_instance(populated_project):
    """SAM rectangle detections each create their own instance (no zero ids)."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR
    from zlabel.widgets.zworker import SamWorkerResult

    results = [
        SamWorkerResult(anno_id="a", result=RR.new(id_="r1", x=1, y=1, w=5, h=5, labels=[proj.crt_label])),
        SamWorkerResult(anno_id="a", result=RR.new(id_="r2", x=10, y=10, w=5, h=5, labels=[proj.crt_label])),
    ]
    win.on_sam_worker_finished(results)
    r1, r2 = anno.results["r1"], anno.results["r2"]
    assert r1.instance_id and r2.instance_id
    assert r1.instance_id != r2.instance_id
    assert r1.instance_id in anno.instances
    assert r2.instance_id in anno.instances

    # a dish rectangle also becomes its own instance
    dish_lbl = Label.new("Dish", "#123456")
    proj.labels[dish_lbl.id] = dish_lbl
    dish = SamWorkerResult(anno_id="a", result=RR.new(id_="dish", x=30, y=30, w=5, h=5, labels=[dish_lbl]))
    win.on_sam_worker_finished([dish])
    assert anno.results["dish"].instance_id
    assert anno.results["dish"].instance_id != r1.instance_id
    assert anno.results["dish"].instance_id != r2.instance_id
    assert anno.results["dish"].instance_id in anno.instances


def test_sam_dish_polygon_gets_instance_and_best_mask(populated_project):
    """The best dish mask becomes its own instance (only the best is kept)."""
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import PolygonResult as PR
    from zlabel.widgets.zworker import SamWorkerResult

    dish_lbl = Label.new("Dish", "#911eb4")
    proj.labels[dish_lbl.id] = dish_lbl
    # a large, round-ish dish and a small sliver: the round one should win
    good = PR.new(id_="d1", points=[(5, 5), (20, 5), (20, 20), (5, 20)], closed=True, labels=[dish_lbl])
    sliver = PR.new(id_="d2", points=[(30, 30), (31, 30), (31, 31)], closed=True, labels=[dish_lbl])
    win.on_sam_worker_finished([SamWorkerResult(anno_id="a", result=sliver), SamWorkerResult(anno_id="a", result=good)])
    assert set(anno.results) == {"d1"}  # only the best dish is kept
    assert anno.results["d1"].instance_id
    assert anno.results["d1"].instance_id in anno.instances
