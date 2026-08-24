from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtCore import QEvent, QPointF, Qt
from pyqtgraph.Qt.QtGui import QTabletEvent

from zlabel.utils import StatusMode

PEN_POINTER_PEN = 1
PEN_POINTER_ERASER = 2


class _FakeTabletEvent:
    """Minimal stand-in for QTabletEvent in non-polygon pen handler tests."""

    def __init__(self, pos: QPointF, button=Qt.MouseButton.LeftButton, buttons=Qt.MouseButton.LeftButton):
        self._pos = pos
        self._button = button
        self._buttons = buttons

    def position(self):
        return self._pos

    def globalPosition(self):
        return self._pos

    def button(self):
        return self._button

    def buttons(self):
        return self._buttons

    def modifiers(self):
        return Qt.KeyboardModifier.NoModifier


class _FakeTabletEventType:
    def __init__(self, etype, pos, pointer=PEN_POINTER_PEN):
        self._type = etype
        self._pos = QPointF(*pos) if not isinstance(pos, QPointF) else pos
        self._pointer = pointer

    def type(self):
        return self._type

    def position(self):
        return self._pos

    def globalPosition(self):
        return self._pos

    def pointerType(self):
        return self._pointer

    def button(self):
        return Qt.MouseButton.LeftButton

    def buttons(self):
        return Qt.MouseButton.LeftButton

    def modifiers(self):
        return Qt.KeyboardModifier.NoModifier

    def accept(self):
        pass


def _pen_click(canvas, pos):
    canvas._handle_pen_press(QPointF(*pos), None)
    canvas._handle_pen_release(QPointF(*pos), None)


def test_pen_click_creates_polygon(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_polygon_triggered()
    canvas = win.canvas

    for pt in [(10, 10), (30, 10), (30, 25)]:
        _pen_click(canvas, pt)
    canvas._finish_pen_polygon(QPointF(10, 25))
    canvas._reset_pen_state()

    assert len(anno.results) == 1
    r = next(iter(anno.results.values()))
    assert len(r.points) >= 3


def test_pen_slide_creates_freehand_polygon(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_polygon_triggered()
    canvas = win.canvas

    canvas._handle_pen_press(QPointF(10, 10), None)
    canvas._handle_pen_move(QPointF(40, 10), None)
    canvas._handle_pen_move(QPointF(40, 40), None)
    canvas._handle_pen_move(QPointF(10, 40), None)
    canvas._handle_pen_release(QPointF(10, 40), None)

    assert len(anno.results) == 1
    r = next(iter(anno.results.values()))
    assert len(r.points) >= 3


def test_pen_eraser_deletes_edit_target(populated_project, canvas_view):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult as RR

    anno.add_result(RR.new(id_="r1", x=10, y=10, w=20, h=20, labels=[proj.crt_label]))
    rebuild()
    win.on_action_edit_triggered()

    vp = canvas_view["to_view"](win.canvas, 20, 20)
    win.canvas._handle_pen_eraser_press(QPointF(vp.x(), vp.y()))

    assert "r1" not in anno.results
    assert "r1" not in win.canvas.showing_items


def test_pen_eraser_undoes_last_polygon_point(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_polygon_triggered()
    canvas = win.canvas

    for pt in [(10, 10), (30, 10), (30, 25)]:
        _pen_click(canvas, pt)
    assert len(canvas.polygon_points_committed) == 3

    canvas._handle_pen_eraser_press(QPointF(30, 25))
    assert len(canvas.polygon_points_committed) == 2


def test_pen_click_creates_keypoint(populated_project):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import AnnotationType, PointResult

    win.cmbox_anno_type.setCurrentIndex(AnnotationType.POINT.value)
    win.on_action_point_triggered()
    canvas = win.canvas

    fake = _FakeTabletEvent(QPointF(20, 20))
    canvas._handle_pen_press(QPointF(20, 20), fake)
    canvas._handle_pen_release(QPointF(20, 20), fake)

    assert len(anno.results) == 1
    assert isinstance(next(iter(anno.results.values())), PointResult)


def test_pen_drag_creates_rectangle(populated_project):
    win, proj, anno, rebuild = populated_project
    from zlabel.utils import RectangleResult

    win.on_action_rectangle_triggered()
    canvas = win.canvas

    fake = _FakeTabletEvent(QPointF(30, 25))
    canvas._handle_pen_press(QPointF(10, 10), fake)
    canvas._handle_pen_move(QPointF(30, 25), fake)
    canvas._handle_pen_release(QPointF(30, 25), fake)

    assert len(anno.results) == 1
    assert isinstance(next(iter(anno.results.values())), RectangleResult)


def test_tablet_event_routed_via_event_filter(populated_project):
    win, proj, anno, rebuild = populated_project
    win.on_action_polygon_triggered()
    canvas = win.canvas

    ev = _FakeTabletEventType(QTabletEvent.TabletPress, (20, 20))
    assert canvas.eventFilter(canvas.viewport(), ev) is True
    assert canvas._pen_press_pos is not None


def test_pinch_gesture_zooms_canvas(populated_project):
    win, proj, anno, rebuild = populated_project
    canvas = win.canvas

    class _FakeGesture:
        def __init__(self, scale):
            self._scale = scale

        def state(self):
            return Qt.GestureState.GestureUpdated

        def scaleFactor(self):
            return self._scale

        def centerPoint(self):
            return QPointF(100, 100)

    class _FakeGestureEvent:
        def __init__(self, scale):
            self.g = _FakeGesture(scale)
            self.accepted = False

        def type(self):
            return QEvent.Type.Gesture

        def gesture(self, _type):
            return self.g

        def accept(self):
            self.accepted = True

    before = [list(r) for r in canvas.view_box.viewRange()]
    ev = _FakeGestureEvent(2.0)
    canvas._pinch_last_scale = 1.0
    assert canvas.gestureEvent(ev) is True
    assert ev.accepted
    after = [list(r) for r in canvas.view_box.viewRange()]
    assert after[0][1] - after[0][0] < before[0][1] - before[0][0], "pinch out must zoom in"
