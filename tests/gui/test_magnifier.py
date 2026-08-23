from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtCore import QEvent, QPoint, Qt
from PySide6.QtTest import QTest


class _FakeWheelEvent:
    def __init__(self, delta: int, modifiers=Qt.KeyboardModifier.NoModifier):
        self._delta = delta
        self._modifiers = modifiers
        self.accepted = False

    def type(self):
        return QEvent.Type.Wheel

    def angleDelta(self):
        return QPoint(0, self._delta)

    def modifiers(self):
        return self._modifiers

    def accept(self):
        self.accepted = True


def test_magnifier_default_off(populated_project):
    win, proj, anno, rebuild = populated_project
    assert win.canvas._magnifier_enabled is False
    assert win.canvas._magnifier is None or not win.canvas._magnifier.isVisible()


def test_magnifier_enable_follows_mouse(populated_project, qtbot):
    win, proj, anno, rebuild = populated_project
    canvas = win.canvas
    canvas.set_magnifier_enabled(True)
    assert canvas._magnifier is not None

    QTest.mouseMove(canvas.viewport(), QPoint(150, 150))
    qtbot.wait(20)

    overlay = canvas._magnifier
    assert overlay.isVisible()
    # lens is offset above-right of the cursor
    assert overlay.x() > 150
    assert overlay.y() < 150
    assert not overlay._source_scene_rect.isEmpty()


def test_magnifier_ctrl_wheel_changes_zoom_plain_wheel_passes_through(populated_project):
    win, proj, anno, rebuild = populated_project
    canvas = win.canvas
    before_range = [list(r) for r in canvas.view_box.viewRange()]

    canvas.set_magnifier_enabled(True)
    ctrl = _FakeWheelEvent(120, Qt.KeyboardModifier.ControlModifier)
    assert canvas.eventFilter(canvas.viewport(), ctrl) is True
    assert ctrl.accepted
    assert canvas._magnifier_zoom == pytest.approx(2.5)
    assert [list(r) for r in canvas.view_box.viewRange()] == before_range

    # plain wheel is not consumed and does not change the lens zoom
    plain = _FakeWheelEvent(120)
    assert not canvas.eventFilter(canvas.viewport(), plain)
    assert canvas._magnifier_zoom == pytest.approx(2.5)

    # magnifier disabled: Ctrl+wheel also passes through
    canvas.set_magnifier_enabled(False)
    disabled = _FakeWheelEvent(120, Qt.KeyboardModifier.ControlModifier)
    assert not canvas.eventFilter(canvas.viewport(), disabled)


def test_magnifier_zoom_clamped(populated_project):
    win, proj, anno, rebuild = populated_project
    canvas = win.canvas
    canvas.set_magnifier_zoom(100.0)
    assert canvas._magnifier_zoom == 10.0
    canvas.set_magnifier_zoom(0.0)
    assert canvas._magnifier_zoom == 1.0


def test_magnifier_edge_does_not_escape_viewport(populated_project, qtbot):
    win, proj, anno, rebuild = populated_project
    canvas = win.canvas
    canvas.set_magnifier_enabled(True)

    QTest.mouseMove(canvas.viewport(), QPoint(0, 0))
    qtbot.wait(20)

    overlay = canvas._magnifier
    assert overlay.isVisible()
    vp = canvas.viewport().rect()
    assert overlay.x() >= 0
    assert overlay.y() >= 0
    assert overlay.x() + overlay.width() <= vp.width()
    assert overlay.y() + overlay.height() <= vp.height()
