import copy
from collections.abc import Sequence

import cv2
import cv2.typing as cv2t
import numpy as np
from numpy.typing import NDArray
from rich import print  # noqa: F401

from zlabel.models.sam_onnx import SamOnnxModel
from zlabel.models.ztypes import (
    Point,
    Polygon,
    Rect,
    SamOnnxPrompt,
    SamOnnxResult,
)
from zlabel.utils.enums import AutoMode, ReturnType


class ZSamWorker:
    def __init__(
        self,
        model: SamOnnxModel,
        anno_id: str,
        img: NDArray,
        auto_mode: AutoMode = AutoMode.CV,
        threshold: int = 100,
        return_type: ReturnType = ReturnType.RECT,
    ) -> None:
        """
        For point:
            auto_mode=AutoMode.SAM: use SAM to predict single point mask
            auto_mode=AutoMode.CV: use opencv to segment the whole image and return the mask
            auto_mode=AutoMode.SAM|AutoMode.CV: use SAM to predict the whole image
        For rectangle:
            auto_mode=AutoMode.SAM&AutoMode.CV: segment using opencv first,
                get rectangles' center point and use SAM to predict
            auto_mode=AutoMode.CV: use opencv to segment selected rectangle masks
            auto_mode=AutoMode.SAM: use SAM to predict the rectangle mask
        """
        super().__init__()
        self.auto_mode = auto_mode
        self.model = model
        self.anno_id = anno_id
        self.img = img
        self.threshold = threshold
        self.return_type = return_type
        self.shifts = [0, 0, 0, 0]

    def run_point(
        self,
        points: list[Point],
        labels: list[float],
    ) -> Sequence[Rect | Polygon | str]:
        result_rects: list[cv2t.Rect] = []
        match self.auto_mode:
            # single point
            case AutoMode.SAM:
                # regard multiple points as single point
                prompts = [SamOnnxPrompt.new(p, label) for p, label in zip(points, labels)]
                r = self.run_sam(self.img, prompts)
                return self.postprocess_mask(r.mask, merge_one=True)
            # whole image by CV
            case AutoMode.CV:
                return self.postprocess_mask(self.img)
            # whole image by SAM
            case x if x == AutoMode.SAM | AutoMode.CV:
                raise NotImplementedError
            case _:
                raise NotImplementedError
        return [Rect(x=x, y=y, w=w, h=h) for x, y, w, h in result_rects]

    def run_rect(self, rects: list[Rect]) -> Sequence[Rect | Polygon | str]:
        results: Sequence[Rect | Polygon | str] = []
        match self.auto_mode:
            case AutoMode.SAM:
                for rect in rects:
                    prompts = [SamOnnxPrompt.new(rect, 0)]
                    r = self.run_sam(self.img, prompts)
                    results.extend(self.postprocess_mask(r.mask))
            case AutoMode.CV:
                for rect in rects:
                    r = self.postprocess_mask(self.img, roi=rect)
                    results.extend(r)
            case x if x == AutoMode.SAM & AutoMode.CV:
                for rect in rects:
                    rects0: Sequence[Rect] = self.postprocess_mask(
                        self.img,
                        roi=rect,
                        return_type=ReturnType.RECT,
                    )  # type: ignore
                    centers = [
                        Point(x=rect.x + r.x + r.w / 2, y=rect.y + r.y + r.h / 2) for r in rects0
                    ]
                    tmp = [SamOnnxPrompt.new(pp, 1) for pp in centers]
                    r = self.run_sam(self.img, tmp)
                    results.extend(self.postprocess_mask(r.mask))
            case _:
                raise NotImplementedError
        # self.plot(result_rects)
        return results

    def run_sam(
        self,
        img: NDArray,
        prompts: list[SamOnnxPrompt],
    ) -> SamOnnxResult:
        if len(prompts) == 0:
            return SamOnnxResult(np.array([[]]), 0.0)
        out = self.model.predict(img, prompts)
        return out

    def postprocess_mask(
        self,
        mask: NDArray,
        merge_one: bool = False,
        roi: Rect | None = None,
        return_type: ReturnType | None = None,
    ) -> Sequence[Rect | Polygon | str]:
        return_type = return_type or self.return_type
        # return RLE-encoded mask
        if return_type == ReturnType.RLE:
            return [Polygon.rle_encode(mask)]

        # img = cv2.blur(img, (2, 2))
        # for ROI, process ROI
        _mask = mask.copy()
        offset_x, offset_y = 0, 0
        if roi:
            x, y, w, h = int(roi.x), int(roi.y), int(roi.w), int(roi.h)
            _mask = mask[y : y + h, x : x + w]
            offset_x, offset_y = x, y
        canny_out = cv2.Canny(_mask, self.threshold, self.threshold * 2)
        contours, _ = cv2.findContours(
            canny_out,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        # contours = [cv2.approxPolyDP(c, 3, True) for c in contours]

        # return rectangles
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
        # return polygons
        elif return_type == ReturnType.POLYGON:
            polygons = []
            for contour in contours:
                _contour = contour.copy().reshape(-1, 2).astype(np.float32)
                _contour[:, 0] += offset_x
                _contour[:, 1] += offset_y
                # _contour[:, 0] = _contour[:, 0] / mask.width
                # _contour[:, 1] = _contour[:, 1] / mask.height
                polygons.append(Polygon(points=[Point(x=i[0], y=i[1]) for i in _contour]))
            return polygons
        else:
            raise NotImplementedError

    def rect_filter(self, rects: list[cv2t.Rect]) -> list[Rect]:
        """
        Filter rects by area.
        """
        areas = np.asarray([w * h for _, _, w, h in rects], dtype=np.float32)
        counts, bins = np.histogram(areas, bins="auto")
        area_most = bins[np.argmax(counts) + 1]
        # print(f"{areas=}, {area_most=}")
        idxs = np.where((areas > area_most * 0.3) & (areas < area_most * 8))[0]
        rects1 = [rects[i] for i in idxs]
        return [Rect(x=x, y=y, w=w, h=h) for x, y, w, h in rects1]

    def plot(self, rects: list[cv2t.Rect], points: list[Point] | None = None):
        im = copy.deepcopy(self.img)
        if points:
            cv2.circle(
                im,
                (int(points[0].x), int(points[0].y)),
                2,
                (0, 255, 255),
                -1,
            )
        for x, y, w, h in rects:
            cv2.rectangle(im, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.imwrite("self.img.png", im)
