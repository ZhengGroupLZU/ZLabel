import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from pyqtgraph.Qt.QtCore import QPointF
from pyqtgraph.Qt.QtWidgets import QApplication

from zlabel.utils import Label, PolygonResult, RectangleResult
from zlabel.widgets.canvas import Canvas

_pytest_app: QApplication | None = None


def _app() -> QApplication:
    global _pytest_app
    if _pytest_app is None:
        _pytest_app = QApplication.instance() or QApplication()
    return _pytest_app


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return _app()


def _canvas() -> Canvas:
    c = Canvas()
    c.resize(800, 600)
    c.show()
    return c


def test_item_at_point_skips_hidden_items():
    """Hidden annotation shapes must not be returned by the canvas hit test, so
    pressing inside a hidden shape starts a box-select instead of an edit."""
    c = _canvas()
    lbl_a = Label.new("A", "#ff0000")
    lbl_b = Label.new("B", "#00ff00")

    ra = RectangleResult.new(id_="ra", x=5, y=5, w=20, h=20, labels=[lbl_a], score=1.0)
    rb = RectangleResult.new(id_="rb", x=30, y=30, w=20, h=20, labels=[lbl_b], score=1.0)
    c.create_item_by_result(ra)
    c.create_item_by_result(rb)

    # both visible -> hit test finds the shapes
    assert c.item_at_point(QPointF(10, 10)) is c.showing_items["ra"]
    assert c.item_at_point(QPointF(40, 40)) is c.showing_items["rb"]

    # hide label B's shape -> hit test must skip it (treated as empty space)
    c.showing_items["rb"].setVisible(False)
    assert c.item_at_point(QPointF(40, 40)) is None

    # the still-visible shape is unaffected
    assert c.item_at_point(QPointF(10, 10)) is c.showing_items["ra"]

    # hidden shapes are also skipped for polygon/point items
    c.showing_items["rb"].setVisible(True)
    pg = PolygonResult.new(
        id_="pg",
        labels=[lbl_b],
        points=[(50, 50), (80, 50), (80, 80), (50, 80)],
        closed=True,
    )
    c.create_item_by_result(pg)
    assert c.item_at_point(QPointF(60, 60)) is c.showing_items["pg"]
    c.showing_items["pg"].setVisible(False)
    assert c.item_at_point(QPointF(60, 60)) is None


def test_selected_items_exclude_hidden():
    """Hidden items must never appear as selected (no accidental edits/deletes)."""
    c = _canvas()
    lbl = Label.new("A", "#ff0000")
    ra = RectangleResult.new(id_="ra", x=5, y=5, w=20, h=20, labels=[lbl], score=1.0)
    rb = RectangleResult.new(id_="rb", x=30, y=30, w=20, h=20, labels=[lbl], score=1.0)
    c.create_item_by_result(ra)
    c.create_item_by_result(rb)

    c.showing_items["ra"].setSelected(True)
    c.showing_items["rb"].setSelected(True)
    assert {i.id_ for i in c.selected_items} == {"ra", "rb"}

    c.showing_items["rb"].setVisible(False)
    assert [i.id_ for i in c.selected_items] == ["ra"], "hidden selected item must be excluded"
