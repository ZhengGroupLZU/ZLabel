from __future__ import annotations

import pytest

from zlabel.utils import (
    Annotation,
    Label,
    PointResult,
    PolygonResult,
    RectangleResult,
)
from zlabel.widgets.dock_info import ZDockInfoContent


@pytest.fixture
def dock(qtbot):
    d = ZDockInfoContent()
    qtbot.addWidget(d)
    d.resize(300, 400)
    d.show()
    return d


def _anno() -> Annotation:
    return Annotation(id="a1", image_path="a.png", original_width=64, original_height=32)


def test_set_info_by_anno(dock):
    anno = _anno()
    dock.set_info_by_anno(anno)
    assert dock.label_img_width.text() == "64.00"
    assert dock.label_img_height.text() == "32.00"
    assert dock._value_labels["group"].text() == "-"
    assert dock._value_labels["nresults"].text() == "0"


def test_set_info_by_anno_with_results(dock):
    anno = _anno()
    lbl = Label.new("A", "#ff0000")
    anno.add_result(RectangleResult.new(id_="r1", x=1, y=2, w=3, h=4, labels=[lbl]))
    anno.add_result(RectangleResult.new(id_="r2", x=5, y=6, w=3, h=4, labels=[lbl], instance_id=7))
    anno.instances[7] = "moldy_seed"
    dock.set_info_by_anno(anno)
    assert dock._value_labels["ninstances"].text() == "1"
    assert dock._value_labels["nresults"].text() == "2"


def test_note_edit_emits(dock, qtbot):
    with qtbot.waitSignal(dock.sigNoteTextChanged, timeout=1000) as blocker:
        dock.ledit_anno_note.setPlainText("hello")
    assert blocker.args == ["hello"]


def test_set_info_rect_result(dock):
    anno = _anno()
    lbl = Label.new("A", "#ff0000")
    r = RectangleResult.new(id_="r1", x=1, y=2, w=3, h=4, rotation=30, text="12:34", labels=[lbl])
    anno.add_result(r)
    dock.set_info_by_result(anno, r)
    assert dock._value_labels["size"].text() == "(1.0, 2.0, 3.0, 4.0)"
    assert dock._value_labels["rotation"].text() == "30.00"
    assert dock._value_labels["text"].text() == "12:34"


def test_set_info_point_result(dock):
    anno = _anno()
    lbl = Label.new("A", "#ff0000")
    r = PointResult.new(id_="p1", x=1.5, y=2.5, labels=[lbl], visible=2)
    anno.add_result(r)
    dock.set_info_by_result(anno, r)
    assert dock._value_labels["pos"].text() == "(1.5, 2.5)"
    assert dock._value_labels["visible"].text() == "OCCLUDED"


def test_set_info_polygon_result(dock):
    anno = _anno()
    lbl = Label.new("A", "#ff0000")
    r = PolygonResult.new(
        id_="g1",
        points=[(0, 0), (4, 0), (4, 3)],
        closed=True,
        labels=[lbl],
        instance_id=5,
    )
    anno.add_result(r)
    anno.instances[5] = "normal_seed"
    dock.set_info_by_result(anno, r)
    assert dock._value_labels["npoints"].text() == "3"
    # shoelace area of the triangle = 6
    assert float(dock._value_labels["area"].text()) == pytest.approx(6.0)
    assert dock._value_labels["instance"].text() == "5"
    assert dock._value_labels["status"].text() == "normal_seed"


def test_clear_hides_rows(dock):
    dock.set_info_by_anno(_anno())
    dock.clear()
    assert dock._value_labels["pos"].text() == ""
