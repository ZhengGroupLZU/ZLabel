import os
import time
from dataclasses import dataclass

import numpy as np
from PIL import Image
from pyqtgraph.Qt.QtCore import QObject, QRunnable, Signal

from zlabel.utils import AutoMode, Label, PolygonResult, RectangleResult
from zlabel.utils.backend import ZLabelBackend
from zlabel.utils.project import Task

# must match Canvas.DISPLAY_MAX_SIDE; the downsample is done off the UI thread
# so switching to a large uncached image does not freeze the interface.
DISPLAY_MAX_SIDE = 2560


def _levels_for(img: np.ndarray) -> tuple[float, float]:
    if img.dtype == np.uint8:
        return (0.0, 255.0)
    small = img[:: max(1, img.shape[0] // 256), :: max(1, img.shape[1] // 256)]
    return float(small.min()), float(small.max())


@dataclass
class PreparedImage:
    """Display-ready image data computed off the UI thread."""

    display: np.ndarray
    flipped: np.ndarray
    full_hw: tuple[int, int]
    img_scale: float
    levels: tuple[float, float]


@dataclass
class GetImageResult:
    """PIL image for caching plus its display-ready numpy counterpart."""

    image: Image.Image
    prepared: PreparedImage | None = None


def prepare_image(image: Image.Image) -> PreparedImage:
    """Decode/downsample/rotate an image for canvas display in a worker thread."""
    full_hw = (image.height, image.width)
    img = np.asarray(image, dtype=np.uint8)
    h, w = img.shape[:2]
    if max(w, h) > DISPLAY_MAX_SIDE:
        s = DISPLAY_MAX_SIDE / max(w, h)
        new_w = max(1, round(w * s))
        new_h = max(1, round(h * s))
        img = np.asarray(Image.fromarray(img).resize((new_w, new_h), Image.Resampling.LANCZOS))
        img_scale = max(w, h) / DISPLAY_MAX_SIDE
    else:
        img_scale = 1.0
    img = np.rot90(img, k=3, axes=(1, 0))
    flipped = np.flipud(img)
    return PreparedImage(
        display=img,
        flipped=flipped,
        full_hw=full_hw,
        img_scale=img_scale,
        levels=_levels_for(img),
    )


@dataclass
class SamWorkerResult:
    anno_id: str
    result: RectangleResult | PolygonResult


class PredictWorkerEmitter(QObject):
    sigFinished = Signal(object)
    sigFailed = Signal()


class ZSamPredictWorker(QRunnable):
    def __init__(
        self,
        api: ZLabelBackend,
        anno_id: str,
        image: str,
        result_labels: list[Label],
        points: list[tuple[float, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[tuple[float, float, float, float]] | None = None,
        threshold: int = 100,
        mode: AutoMode = AutoMode.SAM,
        return_type: int = 1,  # RECT = 1 POLYGON = 2 RLE = 3
        crop_box: tuple[int, int, int, int] | None = None,
    ) -> None:
        """
        points: [(x, y), (x1, y1)]
        rects: [(x, y, w, h), (x1, y1, w1, h1)]
        crop_box: (left, top, right, bottom) in full-image coords; the backend
        crops the image to this box and shifts prompts/results accordingly.
        """
        super().__init__()

        self.api = api
        self.image = image
        self.anno_id = anno_id
        self.points = points
        self.labels = labels
        self.rects = rects
        self.threshold = threshold
        self.mode = mode
        self.result_labels = result_labels
        self.return_type = return_type
        self.crop_box = crop_box

        self.emitter = PredictWorkerEmitter()

        self.shifts = [0, 0, 0, 0]
        self.setAutoDelete(True)

    def run(self):
        points = None
        rects = None
        if self.points is not None:
            points = [
                {
                    "x": p[0],
                    "y": p[1],
                }
                for p in self.points
            ]
        if self.rects is not None:
            rects = [
                {
                    "x": r[0],
                    "y": r[1],
                    "w": r[2],
                    "h": r[3],
                }
                for r in self.rects
            ]
        resp = self.api.predict(
            anno_id=self.anno_id,
            image_name=self.image,
            points=points,
            labels=self.labels,
            rects=rects,
            threshold=self.threshold,
            mode=self.mode.value,
            return_type=self.return_type,
            crop_box=self.crop_box,
        )
        if not resp["status"]:
            self.emitter.sigFailed.emit()
            print(f"Predict Failed, {resp=}")
            return

        results: list[SamWorkerResult] = []
        if self.return_type == 1:  # RECT
            rects = [(r["x"], r["y"], r["w"], r["h"]) for r in resp["data"]]  # type: ignore
            results.extend(self.rects_to_results(rects))  # type: ignore
        elif self.return_type == 2:  # POLYGON
            polys = [[(p["x"], p["y"]) for p in poly["points"]] for poly in resp["data"]]  # type: ignore
            results.extend(self.polys_to_results(polys))  # type: ignore
        elif self.return_type == 3:  # RLE
            ...
        self.emitter.sigFinished.emit(results)

    def rects_to_results(
        self,
        rects: list[tuple[int, int, int, int]],
        x0: int = 0,
        y0: int = 0,
    ) -> list[SamWorkerResult]:
        results: list[SamWorkerResult] = []
        for x, y, w, h in rects:
            r = RectangleResult.new(
                labels=self.result_labels,
                x=x + x0 + self.shifts[0],
                y=y + y0 + self.shifts[1],
                w=w + self.shifts[2],
                h=h + self.shifts[3],
                origin=self.mode.name,  # type: ignore
                score=1.0,
                rotation=0,
            )
            results.append(SamWorkerResult(anno_id=self.anno_id, result=r))
        return results

    def polys_to_results(self, polys: list[list[tuple[float, float]]]) -> list[SamWorkerResult]:
        results: list[SamWorkerResult] = []
        for poly in polys:
            r = PolygonResult.new(
                labels=self.result_labels,
                origin=self.mode.name,  # type: ignore
                score=1.0,
                points=poly,
            )
            results.append(SamWorkerResult(anno_id=self.anno_id, result=r))
        return results


class PreuploadEmitter(QObject):
    finished = Signal()


class ZPreuploadImageWorker(QRunnable):
    def __init__(
        self,
        api: ZLabelBackend,
        anno_id: str,
        image: Image.Image,
    ) -> None:
        super().__init__()
        self.api = api
        self.anno_id = anno_id
        self.image = image
        self.emitter = PreuploadEmitter()
        self.setAutoDelete(True)

    def run(self):
        try:
            self.api.preupload_image(self.anno_id, self.image)
            self.emitter.finished.emit()
        except Exception as e:
            print(e)


class UploadFileEmitter(QObject):
    success = Signal(str)
    fail = Signal(str)


class ZUploadFileWorker(QRunnable):
    def __init__(
        self,
        api: ZLabelBackend,
        filename: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__()

        self.api = api
        self.filename = filename
        self.username = username
        self.password = password
        self.emitter = UploadFileEmitter()
        self.setAutoDelete(True)

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        if os.path.exists(self.filename):
            r = self.api.save_zlabel(self.filename)
            if r:
                self.emitter.success.emit("Upload success!")
            else:
                self.emitter.fail.emit(f"Upload failed with {r=}")


class GetFileEmitter(QObject):
    success = Signal(str, object)
    fail = Signal(object)


class ZGetImageWorker(QRunnable):
    def __init__(
        self,
        api: ZLabelBackend,
        filename: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__()

        self.api = api
        self.filename = filename
        self.username = username
        self.password = password
        self.emitter = GetFileEmitter()
        self.setAutoDelete(True)

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        image = self.api.get_image(self.filename)
        time.sleep(0.5)
        if image is not None:
            self.emitter.success.emit(self.filename, GetImageResult(image=image, prepared=prepare_image(image)))
        else:
            self.emitter.fail.emit(f"Get image {self.filename} failed")


class GetProjectsEmitter(QObject):
    success = Signal(object)
    fail = Signal(object)


class OcrEmitter(QObject):
    finished = Signal(str, object)  # result_id, text_or_None
    failed = Signal(str)


class ZOcrWorker(QRunnable):
    """OCR a cropped image region in a background thread (RapidOCR)."""

    def __init__(
        self,
        image: Image.Image,
        box: tuple[int, int, int, int],
        result_id: str,
    ) -> None:
        super().__init__()
        self.image = image
        self.box = box
        self.result_id = result_id
        self.emitter = OcrEmitter()
        self.setAutoDelete(True)

    def run(self):
        from zlabel.utils.ocr import extract_datetime, ocr_image

        try:
            crop = self.image.crop(self.box).convert("RGB")
            import numpy as np

            text = ocr_image(np.asarray(crop, dtype=np.uint8))
            self.emitter.finished.emit(self.result_id, extract_datetime(text) if text else None)
        except Exception as e:
            print(f"OCR failed: {e}")
            self.emitter.failed.emit(self.result_id)


class GetProjectsWorker(QRunnable):
    def __init__(
        self,
        api: ZLabelBackend,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__()

        self.api = api
        self.username = username
        self.password = password
        self.emitter = GetProjectsEmitter()
        self.setAutoDelete(True)

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        projects = self.api.get_projects()
        if projects is not None:
            try:
                project_list = [(p["id"], p["name"]) for p in projects]
                if len(project_list) > 0:
                    self.emitter.success.emit(project_list)
                else:
                    self.emitter.fail.emit("No projects found")
            except Exception as e:
                self.emitter.fail.emit(f"Get projects failed with {e=}")
        else:
            self.emitter.fail.emit("Get projects failed")


class GetTasksEmitter(QObject):
    success = Signal(object)
    fail = Signal(object)


class ZGetTasksWorker(QRunnable):
    def __init__(
        self,
        api: ZLabelBackend,
        num: int,
        finished: int = 1,
        project_id: int = -1,
        username: str | None = None,
        password: str | None = None,
        random_select: bool = True,
    ) -> None:
        super().__init__()

        self.api = api
        self.username = username
        self.password = password
        self.random_select = random_select
        self.num = num
        self.finished = finished
        self.project_id = project_id
        self.emitter = GetTasksEmitter()
        self.setAutoDelete(True)

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        tasks = self.api.get_tasks(self.project_id, self.num, self.finished, self.random_select)
        if tasks is not None:
            try:
                task_list = [Task.model_validate(t) for t in tasks]
                self.emitter.success.emit(task_list)
            except Exception as e:
                self.emitter.fail.emit(f"Get tasks failed with {e=}")
        else:
            self.emitter.fail.emit("Get tasks failed")


if __name__ == "__main__":
    ...
