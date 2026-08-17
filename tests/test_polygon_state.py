import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pyqtgraph as pg
import pytest
from pyqtgraph.Qt.QtWidgets import QApplication

from zlabel.utils import Label, PolygonResult
from zlabel.widgets.graphic_objects import Polygon

_pytest_app: QApplication | None = None


def _app() -> QApplication:
    global _pytest_app
    if _pytest_app is None:
        _pytest_app = QApplication.instance() or QApplication()
    return _pytest_app


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return _app()


def _make_polygon() -> Polygon:
    pts = [(10, 10), (40, 10), (40, 30), (10, 30)]
    poly = Polygon(positions=pts, closed=True, id_="g1", movable=True)
    return poly


def _result() -> PolygonResult:
    return PolygonResult.new(
        id_="g1",
        labels=[Label.new("A")],
        points=[(10, 10), (40, 10), (40, 30), (10, 30)],
        closed=True,
    )


def _apply_state(result: PolygonResult, state: dict) -> PolygonResult:
    """Mirror of MainWindow.on_canvas_item_state_change_finished's polygon branch."""
    updated = result.model_copy(deep=True)
    px, py = state["pos"][0], state["pos"][1]
    updated.points = [(p[0] + px, p[1] + py) for p in state["points"]]
    updated.x = 0.0
    updated.y = 0.0
    updated.w = state["size"][0]
    updated.h = state["size"][1]
    updated.rotation = state["angle"]
    return updated


def test_polygon_save_state_keeps_origin_for_drag_math():
    """saveState/getState must report the real ROI origin so pyqtgraph's drag
    handler (ROI.pos()) moves the polygon 1:1 with the mouse."""
    poly = _make_polygon()
    poly.translate(pg.Point(10, 5), finish=False)
    st = poly.saveState()
    assert st["pos"] == (10.0, 5.0), "origin must stay visible to the drag handler"
    assert st["points"] == [(10.0, 10.0), (40.0, 10.0), (40.0, 30.0), (10.0, 30.0)]


def test_polygon_body_move_detected_as_edit():
    """A body move changes the origin; folding it into the points must yield a
    result that differs from the original (i.e. the undo command is pushed)."""
    poly = _make_polygon()
    result = _result()
    poly.translate(pg.Point(10, 10), finish=False)
    state = poly.saveState()
    updated = _apply_state(result, state)
    assert updated.equal_v(result) is False, "move must be detected as an edit"
    assert updated.points == [(20, 20), (50, 20), (50, 40), (20, 40)]
    assert updated.x == 0.0 and updated.y == 0.0


def test_polygon_set_state_folds_legacy_origin():
    """Non-zero origins from legacy/moved ROIs are folded into the points and
    the handles are rebuilt at the new absolute vertex positions."""
    poly = _make_polygon()
    poly.setSelected(True)
    poly.setState({
        "pos": pg.Point(10, 10),
        "size": pg.Point(1, 1),
        "angle": 0.0,
        "points": [(10, 10), (40, 10), (40, 30), (10, 30)],
        "closed": True,
    })
    st = poly.getState()
    assert st["pos"].x() == 0.0 and st["pos"].y() == 0.0
    assert [(p.x(), p.y()) for p in st["points"]] == [(20, 20), (50, 20), (50, 40), (20, 40)]
    assert len(poly.handles) == 4, "handles must be rebuilt at the new vertices"


def test_polygon_set_state_rebuilds_stale_handles():
    """After an undo/redo the vertex handles must follow the restored points
    instead of snapping the display back to the old position."""
    poly = _make_polygon()
    poly.setSelected(True)
    # simulate a body move: origin moves, local vertices unchanged
    poly.translate(pg.Point(10, 10), finish=False)
    # redo/undo applies the normalized state (origin folded, pos=0,0)
    result = _result()
    state = poly.saveState()
    normalized = _apply_state(result, state)
    poly.setState(normalized.getState(), update=True)
    st = poly.getState()
    assert [(p.x(), p.y()) for p in st["points"]] == [(20, 20), (50, 20), (50, 40), (20, 40)]
    assert len(poly.handles) == 4
    handle_positions = [tuple(p["pos"]) for p in poly.handles]
    assert handle_positions == [(20, 20), (50, 20), (50, 40), (20, 40)]
