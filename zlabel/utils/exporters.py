"""Annotation dataset exporters (COCO / Ultralytics YOLO).

Supported tasks: object detection, segmentation, keypoint detection.
Keypoints are grouped into instances via `PointResult.instance_id`.
"""

import json
from collections import OrderedDict
from collections.abc import Callable
from enum import IntEnum
from pathlib import Path
from typing import Any

from PIL import Image

from zlabel.utils.project import (
    Annotation,
    GermStatus,
    PointResult,
    PolygonResult,
    Project,
    RectangleResult,
)


class ExportFormat(IntEnum):
    COCO = 0
    YOLO = 1


class ExportTask(IntEnum):
    DETECTION = 0
    SEGMENTATION = 1
    KEYPOINTS = 2


class ExportInstance(IntEnum):
    """How to export seed instances: split by part or merged per instance."""

    SPLIT = 0
    MERGED = 1


def _annotated_tasks(project: Project):
    """Tasks that carry at least one result."""
    for task in project.tasks.values():
        if task.anno is not None and len(task.anno.results) > 0:
            yield task


def _result_bbox(result: RectangleResult | PolygonResult) -> tuple[float, float, float, float]:
    """Return (x, y, w, h) for a rectangle or the bounding box of a polygon."""
    if isinstance(result, RectangleResult):
        return result.x, result.y, result.w, result.h
    xs = [p[0] for p in result.points]
    ys = [p[1] for p in result.points]
    if not xs:
        return 0.0, 0.0, 0.0, 0.0
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return x0, y0, x1 - x0, y1 - y0


def _polygon_points(result: RectangleResult | PolygonResult) -> list[list[float]]:
    """Absolute-coordinate polygon (a rectangle becomes a 4-corner polygon)."""
    if isinstance(result, PolygonResult):
        return [[p[0], p[1]] for p in result.points]
    x, y, w, h = result.x, result.y, result.w, result.h
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def _label_names(project: Project) -> list[str]:
    return [label.name for label in project.labels.values()]


def _group_keypoints(anno: Annotation, label_names: list[str]) -> list[dict[str, Any]]:
    """Group a task's PointResults into instances.

    Points sharing an `instance_id` form one instance; points with an empty
    `instance_id` are each their own single-keypoint instance. The keypoints
    array follows `label_names` order, missing categories filled with 0,0,0.
    """
    by_instance: OrderedDict[str, list[PointResult]] = OrderedDict()
    for result in anno.results.values():
        if isinstance(result, PointResult):
            by_instance.setdefault(result.instance_id or result.id, []).append(result)

    instances = []
    for pts in by_instance.values():
        keypoints: list[float] = [0.0, 0.0, 0.0] * len(label_names)
        n = 0
        for p in pts:
            cat = p.category_id
            if 0 <= cat < len(label_names) and keypoints[cat * 3 + 2] == 0:
                keypoints[cat * 3] = p.x
                keypoints[cat * 3 + 1] = p.y
                keypoints[cat * 3 + 2] = float(p.visible)
                n += 1
        xs = [keypoints[i] for i in range(0, len(keypoints), 3) if keypoints[i + 2] != 0]
        ys = [keypoints[i + 1] for i in range(0, len(keypoints), 3) if keypoints[i + 2] != 0]
        if xs:
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            bbox = (x0, y0, x1 - x0, y1 - y0)
        else:
            bbox = (0.0, 0.0, 0.0, 0.0)
        instances.append({"keypoints": keypoints, "num_keypoints": n, "bbox": bbox})
    return instances


# ---------------------------------------------------------------------------
# COCO
# ---------------------------------------------------------------------------
def export_coco(
    project: Project,
    output: str,
    task: ExportTask,
    instance_mode: ExportInstance = ExportInstance.SPLIT,
) -> dict[str, Any]:
    label_names = _label_names(project)
    if instance_mode == ExportInstance.MERGED:
        return _export_coco_merged(project, output, task, label_names)
    categories: list[dict[str, Any]] = []
    for i, name in enumerate(label_names):
        cat: dict[str, Any] = {"id": i, "name": name}
        if task == ExportTask.KEYPOINTS:
            cat["keypoints"] = label_names
            cat["skeleton"] = []
        categories.append(cat)

    images: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    ann_id = 1
    for img_id, task_ in enumerate(_annotated_tasks(project)):
        anno = task_.anno
        assert anno is not None
        images.append({
            "id": img_id,
            "file_name": task_.filename,
            "width": int(anno.original_width),
            "height": int(anno.original_height),
        })
        if task == ExportTask.KEYPOINTS:
            for inst in _group_keypoints(anno, label_names):
                bbox = inst["bbox"]
                annotations.append({
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": 0,
                    "bbox": [round(v, 2) for v in bbox],
                    "area": round(bbox[2] * bbox[3], 2),
                    "iscrowd": 0,
                    "keypoints": [round(v, 2) for v in inst["keypoints"]],
                    "num_keypoints": inst["num_keypoints"],
                })
                ann_id += 1
        else:
            for result in anno.results.values():
                if isinstance(result, PointResult):
                    continue
                label_id = _label_id(project, result)
                if label_id < 0:
                    continue
                bbox = _result_bbox(result)
                ann: dict[str, Any] = {
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": label_id,
                    "bbox": [round(v, 2) for v in bbox],
                    "area": round(bbox[2] * bbox[3], 2),
                    "iscrowd": 0,
                }
                iid = getattr(result, "instance_id", 0)
                if iid:
                    ann["instance_id"] = iid
                    ann["attributes"] = {"status": anno.instances.get(iid, "")}
                if task == ExportTask.SEGMENTATION:
                    flat = [v for p in _polygon_points(result) for v in p]
                    ann["segmentation"] = [[round(v, 2) for v in flat]]
                annotations.append(ann)
                ann_id += 1

    data = {
        "info": {
            "description": f"ZLabel export ({task.name.lower()})",
            "version": "1.0",
        },
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"images": len(images), "annotations": len(annotations)}


def _label_id(project: Project, result: RectangleResult | PolygonResult) -> int:
    if not result.labels:
        return -1
    return _label_names(project).index(result.labels[0].name) if result.labels[0].name in _label_names(project) else -1


# ---------------------------------------------------------------------------
# Merged (per-instance) COCO
# ---------------------------------------------------------------------------
def _group_instances(anno: Annotation):
    """Split annotation results into (instances, independent).

    instances: instance_id -> list[PolygonResult] (part polygons sharing the id)
    independent: results without an instance_id (dish polygon, timestamp rects).
    """
    groups: OrderedDict[str, list[PolygonResult]] = OrderedDict()
    independent: list[RectangleResult | PolygonResult] = []
    for r in anno.results.values():
        if isinstance(r, PointResult):
            continue
        if isinstance(r, PolygonResult) and r.instance_id:
            groups.setdefault(r.instance_id, []).append(r)
        else:
            independent.append(r)
    return groups, independent


def _export_coco_merged(
    project: Project,
    output: str,
    task: ExportTask,
    label_names: list[str],
) -> dict[str, Any]:
    if task != ExportTask.SEGMENTATION:
        raise ValueError("merged instance export requires the segmentation task")
    status_names = [s.value for s in GermStatus]
    label_start = len(status_names)
    categories = [{"id": i, "name": n} for i, n in enumerate(status_names)]
    categories += [{"id": label_start + i, "name": n} for i, n in enumerate(label_names)]

    images: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    ann_id = 1
    for img_id, task_ in enumerate(_annotated_tasks(project)):
        anno = task_.anno
        assert anno is not None
        images.append({
            "id": img_id,
            "file_name": task_.filename,
            "width": int(anno.original_width),
            "height": int(anno.original_height),
            "group": anno.group,
            "day": anno.day,
        })
        groups, independent = _group_instances(anno)
        for iid, polys in groups.items():
            status = anno.instances.get(iid, "")
            if status not in status_names:
                continue
            all_pts = [p for poly in polys for p in poly.points]
            xs = [p[0] for p in all_pts]
            ys = [p[1] for p in all_pts]
            if not xs:
                continue
            bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
            segmentation = [[round(v, 2) for p in poly.points for v in p] for poly in polys]
            ann: dict[str, Any] = {
                "id": ann_id,
                "image_id": img_id,
                "category_id": status_names.index(status),
                "bbox": [round(v, 2) for v in bbox],
                "area": round(bbox[2] * bbox[3], 2),
                "iscrowd": 0,
                "segmentation": segmentation,
                "instance_id": iid,
            }
            annotations.append(ann)
            ann_id += 1
        for r in independent:
            if not r.labels or r.labels[0].name not in label_names:
                continue
            bbox = _result_bbox(r)
            annotations.append({
                "id": ann_id,
                "image_id": img_id,
                "category_id": label_start + label_names.index(r.labels[0].name),
                "bbox": [round(v, 2) for v in bbox],
                "area": round(bbox[2] * bbox[3], 2),
                "iscrowd": 0,
                "segmentation": [[round(v, 2) for p in _polygon_points(r) for v in p]],
            })
            ann_id += 1

    data = {
        "info": {"description": "ZLabel export (segmentation, merged instances)", "version": "1.0"},
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"images": len(images), "annotations": len(annotations)}


# ---------------------------------------------------------------------------
# Ultralytics YOLO
# ---------------------------------------------------------------------------
def export_yolo(
    project: Project,
    output_dir: str,
    task: ExportTask,
    get_image: Callable[[str], Image.Image | None] | None = None,
    instance_mode: ExportInstance = ExportInstance.SPLIT,
) -> dict[str, Any]:
    """Write `images/` + `labels/` to output_dir, one txt per image."""
    out = Path(output_dir)
    images_dir = out / "images"
    labels_dir = out / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    label_names = _label_names(project)
    if instance_mode == ExportInstance.MERGED:
        return _export_yolo_merged(project, images_dir, labels_dir, task, label_names, get_image)
    n_images = 0
    n_annos = 0
    for task_ in _annotated_tasks(project):
        anno = task_.anno
        assert anno is not None
        w = float(anno.original_width) or 1.0
        h = float(anno.original_height) or 1.0
        filename = Path(task_.filename).name
        lines: list[str] = []

        if task == ExportTask.KEYPOINTS:
            for inst in _group_keypoints(anno, label_names):
                cx = (inst["bbox"][0] + inst["bbox"][2] / 2) / w
                cy = (inst["bbox"][1] + inst["bbox"][3] / 2) / h
                bw = inst["bbox"][2] / w
                bh = inst["bbox"][3] / h
                kpts = " ".join(
                    f"{inst['keypoints'][i] / w} {inst['keypoints'][i + 1] / h} {inst['keypoints'][i + 2]}"
                    for i in range(0, len(inst["keypoints"]), 3)
                )
                lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f} {kpts}".rstrip())
                n_annos += 1
        else:
            for result in anno.results.values():
                if isinstance(result, PointResult):
                    continue
                label_id = _label_id(project, result)
                if label_id < 0:
                    continue
                if task == ExportTask.DETECTION:
                    x, y, bw, bh = _result_bbox(result)
                    cx = (x + bw / 2) / w
                    cy = (y + bh / 2) / h
                    lines.append(f"{label_id} {cx:.6f} {cy:.6f} {bw / w:.6f} {bh / h:.6f}")
                else:  # SEGMENTATION
                    pts = " ".join(f"{p[0] / w:.6f} {p[1] / h:.6f}" for p in _polygon_points(result))
                    lines.append(f"{label_id} {pts}".rstrip())
                n_annos += 1

        stem = filename.rsplit(".", 1)[0]
        (labels_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

        if get_image is not None:
            img = get_image(task_.filename)
            if img is not None:
                img.save(images_dir / filename)
        n_images += 1

    return {"images": n_images, "annotations": n_annos}


def _export_yolo_merged(
    project: Project,
    images_dir: Path,
    labels_dir: Path,
    task: ExportTask,
    label_names: list[str],
    get_image: Callable[[str], Image.Image | None] | None,
) -> dict[str, Any]:
    if task != ExportTask.SEGMENTATION:
        raise ValueError("merged instance export requires the segmentation task")
    status_names = [s.value for s in GermStatus]
    label_start = len(status_names)
    n_images = 0
    n_annos = 0
    for task_ in _annotated_tasks(project):
        anno = task_.anno
        assert anno is not None
        w = float(anno.original_width) or 1.0
        h = float(anno.original_height) or 1.0
        filename = Path(task_.filename).name
        lines: list[str] = []
        groups, independent = _group_instances(anno)
        for iid, polys in groups.items():
            status = anno.instances.get(iid, "")
            if status not in status_names:
                continue
            pts = [p for poly in polys for p in poly.points]
            txt = " ".join(f"{p[0] / w:.6f} {p[1] / h:.6f}" for p in pts)
            lines.append(f"{status_names.index(status)} {txt}".rstrip())
            n_annos += 1
        for r in independent:
            if not r.labels or r.labels[0].name not in label_names:
                continue
            pts = " ".join(f"{p[0] / w:.6f} {p[1] / h:.6f}" for p in _polygon_points(r))
            lines.append(f"{label_start + label_names.index(r.labels[0].name)} {pts}".rstrip())
            n_annos += 1

        stem = filename.rsplit(".", 1)[0]
        (labels_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

        if get_image is not None:
            img = get_image(task_.filename)
            if img is not None:
                img.save(images_dir / filename)
        n_images += 1

    return {"images": n_images, "annotations": n_annos}
