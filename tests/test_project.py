import json

from zlabel.utils.project import (
    Annotation,
    Label,
    PointResult,
    PolygonResult,
    Project,
    RectangleResult,
    ResultType,
    Task,
)


def _project() -> Project:
    p = Project(id="p1", name="proj")
    p.add_task(Task(id=1, anno_id="a1", filename="a.png", labels=["A"]))
    p.add_label(Label.new("A", "#ff0000"))
    return p


def test_project_defaults():
    p = Project(id="p1")
    assert p.storage_mode == "remote"
    assert p.local_dir == ""
    assert p.crt_task is None
    assert p.crt_label is None


def test_save_json_excludes_tasks(tmp_path):
    p = _project()
    path = tmp_path / "proj.json"
    p.save_json(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "tasks" not in data
    assert data["name"] == "proj"
    assert data["storage_mode"] == "remote"


def test_save_json_roundtrip_storage_fields(tmp_path):
    p = _project()
    p.storage_mode = "local"
    p.local_dir = "C:/imgs"
    path = tmp_path / "proj.json"
    p.save_json(path)
    p2 = Project.model_validate_json(path.read_text(), strict=True)
    assert p2.storage_mode == "local"
    assert p2.local_dir == "C:/imgs"
    assert len(p2.tasks) == 0


def test_project_key_result():
    p = _project()
    anno = Annotation(id="a1", image_path="a.png", original_width=10, original_height=10)
    r = RectangleResult.new(labels=[])
    anno.add_result(r)
    p.add_annotation(anno)
    assert p.crt_anno is anno
    assert p.crt_result is r
    assert p.key_result == r.id


def test_annotation_add_remove_result():
    anno = Annotation(id="a1", image_path="a.png", original_width=10, original_height=10)
    r1 = RectangleResult.new(labels=[Label.new("A")], x=1, y=1, w=2, h=2)
    r2 = RectangleResult.new(labels=[Label.new("A")], x=5, y=5, w=2, h=2)
    anno.add_result(r1)
    anno.add_result(r2)
    assert anno.crt_result is r2
    assert anno.remove_result(r2.id) is True
    assert anno.crt_result is r1
    assert anno.remove_result("missing") is False


def test_annotation_reset_results():
    anno = Annotation(id="a1", image_path="a.png", original_width=10, original_height=10)
    anno.add_result(RectangleResult.new(labels=[]))
    anno.reset_results()
    assert len(anno.results) == 0
    assert anno.crt_result is None


def test_annotation_save_json(tmp_path):
    anno = Annotation(
        id="a1",
        image_path="a.png",
        original_width=10,
        original_height=10,
        results={},
    )
    path = tmp_path / "annos" / "a1.zlabel"
    anno.save_json(str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["id"] == "a1"
    assert data["image_path"] == "a.png"


def test_rect_result_get_state():
    r = RectangleResult.new(labels=[], x=1.0, y=2.0, w=3.0, h=4.0, rotation=0)
    state = r.getState()
    assert state["pos"].x() == 1.0
    assert state["size"].y() == 4.0


def test_point_result_defaults():
    r = PointResult.new(labels=[], x=1.5, y=2.5)
    assert r.type_id == ResultType.POINT
    assert r.visible == 1
    assert r.category_id == 0


def test_point_result_get_state():
    r = PointResult.new(labels=[], x=1.5, y=2.5, visible=2, category_id=3)
    state = r.getState()
    assert state["id"] == r.id
    assert state["pos"].x() == 1.5
    assert state["pos"].y() == 2.5
    assert state["visible"] == 2


def test_point_result_equal_v():
    lab = Label.new("A")
    a = PointResult.new(labels=[lab], x=1.0, y=2.0, visible=1)
    b = PointResult.new(labels=[lab], x=1.0, y=2.0, visible=1)
    c = PointResult.new(labels=[lab], x=1.0, y=3.0, visible=1)
    assert a.equal_v(b)
    assert not a.equal_v(c)


def test_polygon_result_equal_v_tracks_geometry():
    """Polygon equality must detect position/size/rotation changes, not just
    vertex points - a body move on the canvas changes the ROI origin which the
    saved points no longer reflect."""
    lab = Label.new("A")
    pts = [(10, 10), (40, 10), (40, 30), (10, 30)]
    base = PolygonResult.new(labels=[lab], points=pts, closed=True)
    moved = PolygonResult.new(labels=[lab], points=pts, closed=True)
    moved.x, moved.y = 5.0, 5.0
    assert base.equal_v(moved) is False

    resized = PolygonResult.new(labels=[lab], points=pts, closed=True)
    resized.w, resized.h = 3.0, 4.0
    assert base.equal_v(resized) is False

    rotated = PolygonResult.new(labels=[lab], points=pts, closed=True)
    rotated.rotation = 30.0
    assert base.equal_v(rotated) is False

    # vertex moves are still detected too
    vertex_moved = PolygonResult.new(labels=[lab], points=[(15, 10), (40, 10), (40, 30), (10, 30)], closed=True)
    assert base.equal_v(vertex_moved) is False

    # identical geometry stays equal
    assert base.equal_v(PolygonResult.new(labels=[lab], points=pts, closed=True))


def test_annotation_with_point_result_roundtrip(tmp_path):
    anno = Annotation(id="a1", image_path="a.png", original_width=10, original_height=10)
    r = PointResult.new(labels=[Label.new("A")], x=1.5, y=2.5, visible=2, category_id=1)
    anno.add_result(r)
    path = tmp_path / "a1.zlabel"
    anno.save_json(str(path))
    anno2 = Annotation.model_validate_json(path.read_text(encoding="utf-8"), strict=True)
    r2 = anno2.results[r.id]
    assert isinstance(r2, PointResult)
    assert r2.x == 1.5 and r2.y == 2.5 and r2.visible == 2 and r2.category_id == 1


def test_reconcile_result_labels_maps_foreign_ids():
    """Legacy annos embed labels whose ids differ from the project's labels;
    they must be re-pointed at the project labels so id-based lookups (e.g.
    the label show/hide eye buttons) work."""
    p = _project()
    label_a = p.crt_label
    p.add_label(Label.new("B", "#00ff00"))
    label_b = next(lbl for lbl in p.labels.values() if lbl.id != label_a.id)
    anno = Annotation(id="a1", image_path="a.png", original_width=10, original_height=10)
    # same names/colors, foreign ids (as saved by older versions / other projects)
    anno.add_result(RectangleResult.new(labels=[Label(id="deadbeef1", name="A", color="#ff0000")], x=1, y=1, w=2, h=2))
    anno.add_result(RectangleResult.new(labels=[Label(id="deadbeef2", name="B", color="#00ff00")], x=5, y=5, w=2, h=2))
    # already matching ids are kept
    anno.add_result(RectangleResult.new(labels=[label_a], x=9, y=9, w=2, h=2))

    p.reconcile_result_labels(anno)

    by_name = {r.labels[0].name: r.labels[0] for r in anno.results.values()}
    assert by_name["A"].id == label_a.id
    assert by_name["B"].id == label_b.id
    assert by_name["A"] is label_a  # existing project object, not a copy


def test_reconcile_result_labels_keeps_unmatched():
    """Labels with no id/name match in the project are left untouched."""
    p = _project()
    anno = Annotation(id="a1", image_path="a.png", original_width=10, original_height=10)
    unknown = Label(id="deadbeef9", name="NoSuchLabel", color="#123456")
    anno.add_result(RectangleResult.new(labels=[unknown], x=1, y=1, w=2, h=2))

    p.reconcile_result_labels(anno)

    r = anno.results[list(anno.results)[0]]
    assert r.labels[0] is unknown


def test_add_annotation_reconciles_labels():
    """Every anno entering the project gets its result labels reconciled."""
    p = _project()
    label_a = p.crt_label
    anno = Annotation(id="a1", image_path="a.png", original_width=10, original_height=10)
    anno.add_result(RectangleResult.new(labels=[Label(id="deadbeef1", name="A", color="#ff0000")], x=1, y=1, w=2, h=2))

    p.add_annotation(anno)

    r = anno.results[list(anno.results)[0]]
    assert r.labels[0].id == label_a.id
    assert r.labels[0] is label_a
