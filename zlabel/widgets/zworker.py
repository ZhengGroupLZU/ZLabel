import os
import time
from dataclasses import dataclass

from PIL import Image
from pyqtgraph.Qt.QtCore import QObject, QRunnable, Signal
from rich import print

from zlabel.utils import AutoMode, Label, PolygonResult, RectangleResult, SamApiHelper
from zlabel.utils.project import Task


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
        api: SamApiHelper,
        anno_id: str,
        image: str,
        result_labels: list[Label],
        points: list[tuple[float, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[tuple[float, float, float, float]] | None = None,
        threshold: int = 100,
        mode: AutoMode = AutoMode.SAM,
        return_type: int = 1,  # RECT = 1 POLYGON = 2 RLE = 3
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
        self.return_type = return_type

        self.emitter = PredictWorkerEmitter()

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
            image_name=self.image,
            points=points,
            labels=self.labels,
            rects=rects,
            threshold=self.threshold,
            mode=self.mode.value,
            return_type=self.return_type,
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
        api: SamApiHelper,
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
        api: SamApiHelper,
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
        image = self.api.get_image(self.filename)
        time.sleep(0.5)
        if image is not None:
            self.emitter.success.emit(self.filename, image)
        else:
            self.emitter.fail.emit(f"Get image {self.filename} failed")


class GetProjectsEmitter(QObject):
    success = Signal(object)
    fail = Signal(object)


class GetProjectsWorker(QRunnable):
    def __init__(
        self,
        api: SamApiHelper,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__()

        self.api = api
        self.username = username
        self.password = password
        self.emitter = GetProjectsEmitter()

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        projects = self.api.get_projects()
        if projects is not None:
            try:
                project_list = [(p["id"], p["name"]) for p in projects]
                self.emitter.success.emit(project_list)
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
        api: SamApiHelper,
        num: int,
        finished: int = 1,
        project_id: int = -1,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__()

        self.api = api
        self.username = username
        self.password = password
        self.num = num
        self.finished = finished
        self.project_id = project_id
        self.emitter = GetTasksEmitter()

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        tasks = self.api.get_tasks(self.project_id, self.num, self.finished)
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
