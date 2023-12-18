from dataclasses import dataclass
import os
import time
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image
from qtpy.QtCore import QObject, QThread, Signal, QRunnable
from rich import print

from zlabel.utils import AlistApiHelper, SamApiHelper, AutoMode, Label, Result, ResultType


@dataclass
class SamWorkerResult(object):
    anno_id: str
    result: Result


class ApiWorkerEmitter(QObject):
    sigFinished = Signal(object)
    sigFailed = Signal()


class ZSamApiWorker(QRunnable):
    def __init__(
        self,
        api: SamApiHelper,
        anno_id: str,
        image: Image.Image,
        result_labels: List[Label],
        points: List[Tuple[float, float]] | None = None,
        labels: List[float] | None = None,
        rects: List[Tuple[float, float, float, float]] | None = None,
        threshold: int = 100,
        mode: AutoMode = AutoMode.SAM,
    ) -> None:
        """
        points: [(x, y), (x1, y1)]
        rects: [(x, y, w, h), (x1, y1, w1, h1)]
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

        self.emitter = ApiWorkerEmitter()

        self.shifts = [0, 0, 0, 0]

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
            image=self.image,
            points=points,
            labels=self.labels,
            rects=rects,
            threshold=self.threshold,
            mode=self.mode.value,
        )
        if not resp["status"]:
            self.emitter.sigFailed.emit()
            print(f"Predict Failed, {resp=}")
            return
        _rects: List[Dict[str, float]] = resp["rects"]
        rects = [[r["x"], r["y"], r["w"], r["h"]] for r in _rects]  # type: ignore
        results = self.rects_to_results(rects)  # type: ignore
        self.emitter.sigFinished.emit(results)

    def rects_to_results(
        self,
        rects: List[Sequence[int]],
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
                origin=self.mode.name,  # type: ignore
                score=1.0,
                rotation=0,
            )
            results.append(SamWorkerResult(anno_id=self.anno_id, result=r))
        return results


class PreuploadEmitter(QObject):
    finished = Signal()


class ZPreuploadImageWorker(QRunnable):
    def __init__(
        self,
        api: SamApiHelper,
        anno_id: str,
        image: Image.Image,
    ) -> None:
        super().__init__()
        self.api = api
        self.anno_id = anno_id
        self.image = image
        self.emitter = PreuploadEmitter()

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
        api: AlistApiHelper,
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

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        if os.path.exists(self.filename):
            r = self.api.upload_file(self.filename)
            if "success" not in r:
                self.emitter.fail.emit(f"Upload failed with {r=}")
            else:
                self.emitter.success.emit("Upload success!")


class GetFileEmitter(QObject):
    success = Signal(str, object)
    fail = Signal(object)


class ZGetImageWorker(QRunnable):
    def __init__(
        self,
        api: AlistApiHelper,
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

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        url = self.api.get_img_url(self.filename)
        image = self.api.get_image_by_api(url, self.api.user_token)
        if image is not None:
            self.emitter.success.emit(self.filename, image)
        else:
            self.emitter.fail.emit(f"Get image {self.filename} failed")


if __name__ == "__main__":
    ...
