"""ZSamWorker: consume Predictor results and post-process into Rect/Polygon/RLE."""

from __future__ import annotations

import copy
from collections.abc import Sequence

import cv2
import cv2.typing as cv2t
import numpy as np
from numpy.typing import NDArray

from zlabel.models.postprocess import (
    contour_filter,
    nms_filter,
    reduce_contour_points,
    smooth_contour,
)
from zlabel.models.predictor import Predictor
from zlabel.models.ztypes import Point, Polygon, Rect
from zlabel.utils.enums import AutoMode, ReturnType


class ZSamWorker:
    def __init__(
        self,
        model: Predictor,
        anno_id: str,
        img: NDArray,
        auto_mode: AutoMode = AutoMode.CV,
        threshold: int = 100,
        return_type: ReturnType = ReturnType.RECT,
        min_contour_area_ratio: float = 3.0e-5,
        iou_threshold: float = 0.5,
        contour_min_points: int = 10,
        contour_max_points: int = 100,
        contour_max_iterations: int = 10,
    ) -> None:
        super().__init__()
        self.auto_mode = auto_mode
        self.model = model
        self.anno_id = anno_id
        self.img = img
        self.threshold = threshold
        self.return_type = return_type
        self.min_contour_area_ratio = min_contour_area_ratio
        self.iou_threshold = iou_threshold
        self.contour_min_points = contour_min_points
        self.contour_max_points = contour_max_points
        self.contour_max_iterations = contour_max_iterations
        self.shifts = [0, 0, 0, 0]

    def run_sam(
        self,
        points: list[tuple[float, float]] | None = None,
        labels: list[float] | None = None,
        bboxes: list[tuple[float, float, float, float]] | None = None,
    ):
        return self.model.predict(points=points, labels=labels, bboxes=bboxes)

    def run_point(self, points: list[Point], labels: list[float]) -> Sequence[Rect | Polygon | str]:
        final: list[Rect | Polygon | str] = []
        match self.auto_mode:
            case AutoMode.SAM:
                pts = [(p.x, p.y) for p in points]
                results = self.run_sam(points=pts, labels=labels)
                if results:
                    final.extend(self.postprocess_mask(results[0].mask.astype(np.uint8), merge_one=True))
                return final
            case AutoMode.CV:
                return self.postprocess_mask(self.img)
            case x if x == AutoMode.SAM | AutoMode.CV:
                raise NotImplementedError
            case _:
                raise NotImplementedError
        return final

    def run_rect(self, rects: list[Rect]) -> Sequence[Rect | Polygon | str]:
        results: list[Rect | Polygon | str] = []
        match self.auto_mode:
            case AutoMode.SAM:
                for rect in rects:
                    box = (rect.x, rect.y, rect.x + rect.w, rect.y + rect.h)
                    # SAM returns several candidate masks per box; keep only the
                    # highest-scoring one to avoid drawing near-identical overlays.
                    candidates = self.run_sam(bboxes=[box])
                    if candidates:
                        results.extend(
                            self.postprocess_mask(candidates[0].mask.astype(np.uint8))
                        )
            case AutoMode.CV:
                for rect in rects:
                    results.extend(self.postprocess_mask(self.img, roi=rect))
            case x if x == AutoMode.SAM & AutoMode.CV:
                for rect in rects:
                    rects0: Sequence[Rect] = self.postprocess_mask(self.img, roi=rect, return_type=ReturnType.RECT)  # type: ignore
                    centers = [Point(x=rect.x + r.x + r.w / 2, y=rect.y + r.y + r.h / 2) for r in rects0]
                    for r in self.run_sam(points=[(p.x, p.y) for p in centers], labels=[1] * len(centers)):
                        results.extend(self.postprocess_mask(r.mask.astype(np.uint8)))
            case _:
                raise NotImplementedError
        return self.results_filter(results)

    def postprocess_mask(
        self,
        mask: NDArray,
        merge_one: bool = False,
        roi: Rect | None = None,
        return_type: ReturnType | None = None,
    ) -> Sequence[Rect | Polygon | str]:
        return_type = return_type or self.return_type
        if return_type == ReturnType.RLE:
            return [Polygon.rle_encode(mask)]

        _mask = mask.copy()
        if _mask.ndim == 3:
            _mask = cv2.cvtColor(_mask, cv2.COLOR_BGR2GRAY)
        offset_x, offset_y = 0, 0
        if roi is not None:
            x, y, w, h = int(roi.x), int(roi.y), int(roi.w), int(roi.h)
            _mask = _mask[y : y + h, x : x + w]
            offset_x, offset_y = x, y

        _mask = cv2.dilate(_mask, np.ones((3, 3), np.uint8), iterations=1)
        # Gaussian blur + re-threshold rounds the binary edge (vs the tiny 2x2 box
        # blur), which removes most of the mask stair-stepping.
        _mask = cv2.GaussianBlur(_mask, (3, 3), 0)
        # _, _mask = cv2.threshold(_mask, 127, 255, cv2.THRESH_BINARY)
        _mask = cv2.erode(_mask, np.ones((3, 3), np.uint8), iterations=1)
        contours, _ = cv2.findContours(_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contour_filter(contours, self.min_contour_area_ratio, self.img.shape[:2])
        # smooth the contour points, then drop redundant points for a cleaner shape
        contours = [smooth_contour(c) for c in contours]
        contours = [
            reduce_contour_points(
                c,
                min_points=self.contour_min_points,
                max_points=self.contour_max_points,
                max_iterations=self.contour_max_iterations,
            )
            for c in contours
        ]

        if return_type == ReturnType.RECT:
            if merge_one:
                new_contours = []
                for c in contours:
                    new_contours.extend(list(c))
                if len(new_contours) == 0:
                    return []
                rects = [cv2.boundingRect(np.array(new_contours))]
            else:
                rects = [cv2.boundingRect(m) for m in contours]
                rects = [(x + offset_x, y + offset_y, w, h) for x, y, w, h in rects]
            return self.rect_filter(rects)  # type: ignore

        if return_type == ReturnType.POLYGON:
            polygons = []
            for contour in contours:
                _contour = contour.copy().reshape(-1, 2).astype(np.float32)
                _contour[:, 0] += offset_x
                _contour[:, 1] += offset_y
                polygons.append(Polygon(points=[Point(x=i[0], y=i[1]) for i in _contour]))
            return polygons
        raise NotImplementedError

    def rect_filter(self, rects: list[cv2t.Rect]) -> list[Rect]:
        areas = np.asarray([w * h for _, _, w, h in rects], dtype=np.float32)
        if len(areas) == 0:
            return []
        counts, bins = np.histogram(areas, bins="auto")
        area_most = bins[np.argmax(counts) + 1]
        idxs = np.where((areas > area_most * 0.3) & (areas < area_most * 8))[0]
        return [Rect(x=x, y=y, w=w, h=h) for x, y, w, h in [rects[i] for i in idxs]]

    def results_filter(self, results: list[Rect | Polygon | str]) -> list[Rect | Polygon | str]:
        boxes: list[tuple[float, float, float, float]] = []
        for r in results:
            if isinstance(r, Rect):
                boxes.append((r.x, r.y, r.w, r.h))
            elif isinstance(r, Polygon):
                pts = np.array([[p.x, p.y] for p in r.points], dtype=np.int32).reshape(-1, 1, 2)
                x, y, w, h = cv2.boundingRect(pts)
                boxes.append((x, y, w, h))
        keep = nms_filter(boxes, self.iou_threshold)
        new_results = [results[i] for i in keep]
        new_results += [r for r in results if isinstance(r, str)]
        return new_results
