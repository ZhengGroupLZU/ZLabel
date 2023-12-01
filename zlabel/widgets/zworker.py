import copy
import hashlib
from typing import List, Optional, Tuple
import cv2
import cv2.typing as cv2t
from qtpy.QtCore import QThread, Signal, QObject
from zlabel.models.sam_onnx import SamOnnxModel
import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass

from zlabel.models.types import PromptType, SamOnnxPrompt, SamOnnxResult
from zlabel.utils.enums import AutoMode
from zlabel.utils.project import Label, ResultType, Result

from rich import print


@dataclass
class SamWorkerResult(object):
    anno_id: str
    result: Result


class ZSamEncodeWorker(QObject):
    sigFinished = Signal(object)

    def __init__(self, model: SamOnnxModel, image: NDArray, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.model = model
        self.image = image

    def run(self):
        key = hashlib.md5(self.image.tobytes()).hexdigest()
        enc_inp = self.model.encode(self.image)
        self.sigFinished.emit((key, enc_inp))


class ZSamWorker(QObject):
    sigFinished = Signal(object)

    def __init__(
        self,
        model: SamOnnxModel,
        anno_id: str,
        result_labels: List[Label],
        img: NDArray,
        points: List[Tuple[float, float]] | List[Tuple[float, float, float, float]],
        labels: List[float],
        result_type: ResultType = ResultType.POINT,
        auto_mode: AutoMode = AutoMode.CV,
        threshold: int = 100,
        parent: QObject | None = None,
    ) -> None:
        """
        For point:
            auto_mode=AutoMode.SAM: use SAM to predict single point mask
            auto_mode=AutoMode.CV: use opencv to segment the whole image and return the mask
            auto_mode=AutoMode.SAM|AutoMode.CV: use SAM to predict the whole image
        For rectangle:
            auto_mode=AutoMode.SAM&AutoMode.CV: segment using opencv first, get rectangles' center point and use SAM to predict
            auto_mode=AutoMode.CV: use opencv to segment selected rectangle masks
            auto_mode=AutoMode.SAM: use SAM to predict the rectangle mask
        """
        super().__init__(parent)
        self.auto_mode = auto_mode
        self.model = model
        self.anno_id = anno_id
        self.result_labels = result_labels
        self.points = points
        self.labels = labels
        self.img = img
        self.result_type = result_type
        self.threshold = threshold
        self.shifts = [0, 0, 0, 0]

    def run(self) -> List[SamWorkerResult]:
        result_rects = []
        if self.result_type == ResultType.POINT:
            match self.auto_mode:
                # single point
                case AutoMode.SAM:
                    # regard multiple points as single point
                    prompts = [SamOnnxPrompt.new(p, label) for p, label in zip(self.points, self.labels)]
                    r = self.run_sam(self.img, prompts)
                    result_rects = self.rects_cv(r.mask)
                # whole image by CV
                case AutoMode.CV:
                    result_rects = self.rects_cv(self.img)
                # whole image by SAM
                case x if x == AutoMode.SAM | AutoMode.CV:
                    raise NotImplementedError
                case _:
                    raise NotImplementedError
        elif self.result_type == ResultType.RECTANGLE:
            match self.auto_mode:
                case AutoMode.SAM:
                    for p in self.points:
                        prompts = [SamOnnxPrompt.new(p, 0)]
                        r = self.run_sam(self.img, prompts)
                        result_rects.extend(self.rects_cv(r.mask))
                case AutoMode.CV:
                    for p in self.points:
                        assert len(p) == 4
                        x, y, x1, y1 = [int(i) for i in p]
                        rects = np.array(
                            [[r[0] + x, r[1] + y, r[2], r[3]] for r in self.rects_cv(self.img[y:y1, x:x1])],
                            dtype=int,
                        )
                        result_rects.extend(rects)
                case x if x == AutoMode.SAM & AutoMode.CV:
                    for p in self.points:
                        assert len(p) == 4
                        x, y, x1, y1 = [int(i) for i in p]
                        rects0 = self.rects_cv(self.img[y:y1, x:x1])
                        centers = [[x + xx + ww / 2, y + yy + hh / 2] for xx, yy, ww, hh in rects0]
                        tmp = [SamOnnxPrompt.new(pp, 1) for pp in centers]
                        r = self.run_sam(self.img, tmp)
                        result_rects.extend(self.rects_cv(r.mask))
                case _:
                    raise NotImplementedError
        else:
            raise NotImplementedError
        self.plot(result_rects)
        worker_results = self.rects_to_results(result_rects)
        self.sigFinished.emit(worker_results)
        return worker_results

    def run_sam(self, img: NDArray, prompts: List[SamOnnxPrompt]) -> SamOnnxResult:
        out = self.model.predict(img, prompts)
        return out

    def rects_to_results(
        self,
        rects: List[cv2t.Rect],
        x0: int = 0,
        y0: int = 0,
    ) -> List[SamWorkerResult]:
        results: List[SamWorkerResult] = []
        for x, y, w, h in rects:
            r = Result.new(
                ResultType.RECTANGLE,
                self.result_labels,
                x + x0 + self.shifts[0],
                y + y0 + self.shifts[1],
                w + self.shifts[2],
                h + self.shifts[3],
                origin=self.auto_mode.name,
                score=1.0,
                rotation=0,
            )
            results.append(SamWorkerResult(self.anno_id, r))
        return results

    def rects_cv(self, img: NDArray, merge_one: bool = False) -> List[cv2t.Rect]:
        # img = cv2.blur(img, (2, 2))
        canny_out = cv2.Canny(img, self.threshold, self.threshold * 2)
        contours, _ = cv2.findContours(
            canny_out,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        # contours = [cv2.approxPolyDP(c, 3, True) for c in contours]
        if merge_one:
            new_contours = []
            for c in contours:
                new_contours.extend(list(c))
            rects = [cv2.boundingRect(np.array(new_contours))]
        else:
            rects = [cv2.boundingRect(m) for m in contours]
        return self.rect_filter(rects)  # type: ignore

    def rect_filter(self, rects: List[cv2t.Rect]) -> List[cv2t.Rect]:
        areas = np.asarray([w * h for _, _, w, h in rects], dtype=np.float32)
        counts, bins = np.histogram(areas, bins="auto")
        area_most = bins[np.argmax(counts) + 1]
        # print(f"{areas=}, {area_most=}")
        idxs = np.where((areas > area_most * 0.3) & (areas < area_most * 8))[0]
        return [rects[i] for i in idxs]

    def plot(self, rects: List[cv2t.Rect]):
        print(self.points)
        im = copy.deepcopy(self.img)
        cv2.circle(
            im,
            (int(self.points[0][0]), int(self.points[0][1])),
            2,
            (0, 255, 255),
            -1,
        )
        for x, y, w, h in rects:
            cv2.rectangle(im, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.imwrite("self.img.png", im)


if __name__ == "__main__":
    ...
    # img = cv2.imread("401.png")
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # model = SamOnnxModel(
    #     "data/sam_vit_l_encoder_quantized.onnx",
    #     "data/sam_vit_l_decoder_quantized.onnx",
    # )
    # points = [
    #     (150, 85),
    # ]
    # labels = [1]
    # worker = ZSamWorker(
    #     model,
    #     "TEST_RESULT_ID",
    #     [Label.default()],
    #     img,
    #     points,
    #     ResultType.POINT,
    #     AutoMode.SAM,
    #     threshold=100,
    #     parent=None,
    # )
    # r = worker.run()
    # print(r)
