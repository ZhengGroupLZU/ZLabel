import json

import numpy as np
from PIL import Image

from zlabel.utils.exporters import (
    ExportInstance,
    ExportTask,
    export_coco,
    export_yolo,
)
from zlabel.utils.project import (
    Annotation,
    GermStatus,
    Label,
    PointResult,
    PolygonResult,
    Project,
    RectangleResult,
    Task,
)


def _project() -> Project:
    p = Project(id="p1", name="proj")
    p.add_label(Label.new("cat", "#ff0000"))
    p.add_label(Label.new("dog", "#00ff00"))
    p.add_label(Label.new("nose", "#0000ff"))
    p.add_task(Task(id=1, anno_id="a1", filename="a.png", labels=["cat", "dog"]))
    p.add_task(Task(id=2, anno_id="a2", filename="b.png", labels=[]))
    anno = Annotation(id="a1", image_path="a.png", original_width=100, original_height=80)
    anno.add_result(RectangleResult.new(labels=[p.labels[list(p.labels)[0]]], x=10, y=10, w=20, h=30))
    anno.add_result(
        PolygonResult.new(
            labels=[p.labels[list(p.labels)[1]]],
            points=[(5, 5), (15, 5), (15, 15), (5, 15)],
        )
    )
    nose = p.labels[list(p.labels)[2]]
    anno.add_result(
        PointResult.new(labels=[nose], x=30, y=40, visible=1, category_id=2, instance_id=1)
    )
    anno.add_result(
        PointResult.new(labels=[nose], x=50, y=40, visible=2, category_id=2, instance_id=2)
    )
    p.tasks["a1"].anno = anno
    return p


def test_coco_detection(tmp_path):
    p = _project()
    out = tmp_path / "out.json"
    stats = export_coco(p, str(out), ExportTask.DETECTION)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert stats == {"images": 1, "annotations": 2}
    assert len(data["images"]) == 1 and data["images"][0]["file_name"] == "a.png"
    assert len(data["annotations"]) == 2
    rect_ann = data["annotations"][0]
    assert rect_ann["bbox"] == [10.0, 10.0, 20.0, 30.0]
    poly_ann = data["annotations"][1]
    assert poly_ann["bbox"] == [5.0, 5.0, 10.0, 10.0]
    assert len(data["categories"]) == 3


def test_coco_segmentation(tmp_path):
    p = _project()
    out = tmp_path / "out.json"
    export_coco(p, str(out), ExportTask.SEGMENTATION)
    data = json.loads(out.read_text(encoding="utf-8"))
    rect_ann = data["annotations"][0]
    assert rect_ann["segmentation"][0] == [10, 10, 30, 10, 30, 40, 10, 40]
    poly_ann = data["annotations"][1]
    assert poly_ann["segmentation"][0] == [5, 5, 15, 5, 15, 15, 5, 15]


def test_coco_keypoints(tmp_path):
    p = _project()
    out = tmp_path / "out.json"
    export_coco(p, str(out), ExportTask.KEYPOINTS)
    data = json.loads(out.read_text(encoding="utf-8"))
    # only PointResults, grouped into 2 instances
    assert len(data["annotations"]) == 2
    inst1 = data["annotations"][0]
    assert inst1["num_keypoints"] == 1
    # keypoints array length = 3 categories * 3
    assert len(inst1["keypoints"]) == 9
    assert inst1["keypoints"][6:9] == [30.0, 40.0, 1.0]  # nose is category 2
    assert inst1["keypoints"][0:3] == [0.0, 0.0, 0.0]
    assert data["categories"][2]["keypoints"] == ["cat", "dog", "nose"]
    assert "segmentation" not in inst1


def test_yolo_detection(tmp_path):
    p = _project()
    out = tmp_path / "yolo"
    export_yolo(p, str(out), ExportTask.DETECTION)
    txt = (out / "labels" / "a.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(txt) == 2
    # rect: class 0, center (20,25) -> (0.2, 0.3125), w=0.2, h=0.375
    parts = txt[0].split()
    assert parts[0] == "0"
    assert abs(float(parts[1]) - 0.2) < 1e-3
    assert abs(float(parts[2]) - 25 / 80) < 1e-3


def test_yolo_segmentation(tmp_path):
    p = _project()
    out = tmp_path / "yolo"
    export_yolo(p, str(out), ExportTask.SEGMENTATION)
    txt = (out / "labels" / "a.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(txt) == 2
    parts = txt[1].split()
    assert parts[0] == "1"  # dog
    assert len(parts) == 1 + 8  # class + 4 points * 2 coords


def test_yolo_keypoints(tmp_path):
    p = _project()
    out = tmp_path / "yolo"
    export_yolo(p, str(out), ExportTask.KEYPOINTS)
    txt = (out / "labels" / "a.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(txt) == 2  # two instances
    parts = txt[0].split()
    # class + bbox(4) + 3 keypoints * 3
    assert len(parts) == 1 + 4 + 9
    kpt = parts[5:8]  # first keypoint (cat category, absent -> 0 0 0)
    assert kpt == ["0.0", "0.0", "0.0"]
    kpt_nose = parts[11:14]  # nose (category 2), normalized x=0.3 y=0.5 v=1
    assert abs(float(kpt_nose[0]) - 0.3) < 1e-3
    assert abs(float(kpt_nose[1]) - 0.5) < 1e-3
    assert float(kpt_nose[2]) == 1.0


def test_yolo_copies_images(tmp_path):
    p = _project()
    out = tmp_path / "yolo"
    seen = []

    def get_image(name):
        seen.append(name)
        return Image.fromarray(np.full((80, 100, 3), 200, dtype=np.uint8))

    export_yolo(p, str(out), ExportTask.DETECTION, get_image=get_image)
    assert (out / "images" / "a.png").exists()
    assert seen == ["a.png"]


def _germ_project() -> Project:
    """Project with two seed instances: seed+root+seedling parts and a dish."""
    p = Project(id="g", name="germ")
    for name, color in [("Seed", "#f00"), ("Root", "#0f0"), ("Seedling", "#00f"), ("Dish", "#808")]:
        p.add_label(Label.new(name, color))
    p.add_task(
        Task(id=1, anno_id="g1", filename="wheat/dish1/D1.png", labels=[], group="wheat/dish1", day=1)
    )
    anno = Annotation(
        id="g1",
        image_path="wheat/dish1/D1.png",
        original_width=100,
        original_height=100,
        group="wheat/dish1",
        day=1,
        instances={1: GermStatus.NORMAL_SEED.value, 2: GermStatus.NORMAL_SEEDLING.value},
    )
    names = {lbl.name: lbl for lbl in p.labels.values()}
    anno.add_result(
        PolygonResult.new(labels=[names["Seed"]], points=[(1, 1), (9, 1), (9, 9), (1, 9)], instance_id=1)
    )
    anno.add_result(
        PolygonResult.new(labels=[names["Root"]], points=[(9, 5), (18, 5), (18, 8), (9, 8)], instance_id=1)
    )
    anno.add_result(
        PolygonResult.new(labels=[names["Seedling"]], points=[(20, 20), (28, 20), (28, 28), (20, 28)], instance_id=2)
    )
    anno.add_result(
        PolygonResult.new(labels=[names["Dish"]], points=[(40, 40), (80, 40), (80, 80), (40, 80)])
    )
    p.tasks["g1"].anno = anno
    return p


def test_coco_merged_instances(tmp_path):
    p = _germ_project()
    out = tmp_path / "merged.json"
    stats = export_coco(p, str(out), ExportTask.SEGMENTATION, ExportInstance.MERGED)
    data = json.loads(out.read_text(encoding="utf-8"))
    # categories: 5 statuses + 4 labels
    assert len(data["categories"]) == 5 + 4
    status_names = [s.value for s in GermStatus]
    cats = {c["id"]: c["name"] for c in data["categories"]}
    assert cats[0] == status_names[0]
    assert cats[5] == "Seed"
    assert stats["annotations"] == 3  # two instances + dish
    anns = sorted(data["annotations"], key=lambda a: a["id"])
    inst1 = anns[0]
    assert inst1["category_id"] == status_names.index("normal_seed")
    assert inst1["instance_id"] == 1
    assert len(inst1["segmentation"]) == 2  # seed + root merged
    assert data["images"][0]["group"] == "wheat/dish1"
    assert data["images"][0]["day"] == 1
    dish = anns[2]
    assert dish["category_id"] == 5 + 3  # Dish label id


def test_coco_split_has_instance_fields(tmp_path):
    p = _germ_project()
    out = tmp_path / "split.json"
    export_coco(p, str(out), ExportTask.SEGMENTATION, ExportInstance.SPLIT)
    data = json.loads(out.read_text(encoding="utf-8"))
    seed = [a for a in data["annotations"] if a.get("instance_id") == 1][0]
    assert seed["attributes"]["status"] == "normal_seed"
    dish = [a for a in data["annotations"] if "instance_id" not in a][0]
    assert dish["category_id"] == data["categories"].index({"id": 3, "name": "Dish"})


def test_yolo_merged_instances(tmp_path):
    p = _germ_project()
    out = tmp_path / "yolo"
    export_yolo(p, str(out), ExportTask.SEGMENTATION, instance_mode=ExportInstance.MERGED)
    txt = (out / "labels" / "D1.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(txt) == 3  # 2 instances + dish
    status_names = [s.value for s in GermStatus]
    first = txt[0].split()
    assert int(first[0]) == status_names.index("normal_seed")
    # seed(4 pts) + root(4 pts) -> 1 + 16 coords
    assert len(first) == 1 + 16
    assert all(0.0 <= float(v) <= 1.0 for v in first[1:])
