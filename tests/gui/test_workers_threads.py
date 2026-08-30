from __future__ import annotations

import pytest
from PIL import Image

from zlabel.utils import Annotation, AutoMode, Label, RectangleResult
from zlabel.widgets.zthread import ZLoginThread
from zlabel.widgets.zworker import (
    GetProjectsWorker,
    ZGetImageWorker,
    ZGetTasksWorker,
    ZPrepareImageWorker,
    ZSamPredictWorker,
)


# ---------------------------------------------------------------------------
# Fake backends
# ---------------------------------------------------------------------------
class FakeApi:
    """Duck-typed ZLabelBackend for workers."""

    def __init__(self, **kw):
        self.user_token = None
        self.__dict__.update(kw)

    def login(self, username, password):
        return "token-123"

    def get_projects(self):
        return self._projects

    def get_tasks(self, project_id, num, finished, random_select):
        return self._tasks

    def get_image(self, filename):
        return self._images.get(filename)

    def predict(self, **kwargs):
        return self._predict(kwargs)

    def save_zlabel(self, filename):
        return True

    def preupload_image(self, anno_id, image):
        return True


def test_get_projects_worker(qtbot):
    api = FakeApi(_projects=[{"id": 1, "name": "proj"}])
    worker = GetProjectsWorker(api, "u", "p")
    with qtbot.waitSignal(worker.emitter.success, timeout=2000) as blocker:
        worker.run()  # run synchronously; QRunnable path is the same code
    assert blocker.args == [[(1, "proj")]]


def test_get_projects_worker_fail(qtbot):
    api = FakeApi(_projects=None)
    worker = GetProjectsWorker(api, "u", "p")
    with qtbot.waitSignal(worker.emitter.fail, timeout=2000):
        worker.run()


def test_get_tasks_worker(qtbot):
    from zlabel.utils import Task

    tasks = [{"id": 1, "anno_id": "a", "filename": "a.png", "labels": [], "finished": False}]
    api = FakeApi(_tasks=tasks)
    worker = ZGetTasksWorker(api, 10, 1, -1, "u", "p", random_select=False)
    with qtbot.waitSignal(worker.emitter.success, timeout=2000) as blocker:
        worker.run()
    loaded = blocker.args[0]
    assert isinstance(loaded[0], Task)
    assert loaded[0].filename == "a.png"


def test_get_image_worker(qtbot):
    img = Image.new("RGB", (16, 16))
    api = FakeApi(_images={"a.png": img})
    worker = ZGetImageWorker(api, "a.png", "u", "p")
    with qtbot.waitSignal(worker.emitter.success, timeout=3000) as blocker:
        worker.run()
    name, result = blocker.args
    assert name == "a.png"
    assert result.image is img
    assert result.prepared is not None


def test_prepare_image_keeps_full_res_info():
    from zlabel.widgets.zworker import prepare_image

    img = Image.new("RGB", (4000, 3000))
    prepared = prepare_image(img)
    assert prepared.full_hw == (3000, 4000)
    assert max(prepared.display.shape) == 4000
    assert prepared.img_scale == pytest.approx(1.0)


def test_prepare_image_worker_prepares_display_off_ui_thread(qtbot):
    img = Image.new("RGB", (3000, 4000))
    worker = ZPrepareImageWorker(img)
    with qtbot.waitSignal(worker.emitter.success, timeout=3000) as blocker:
        worker.run()
    prepared = blocker.args[0]
    assert prepared.full_hw == (4000, 3000)
    assert max(prepared.display.shape) == 4000
    assert prepared.img_scale == pytest.approx(1.0)


def test_sam_predict_worker_rect(qtbot):
    api = FakeApi(_predict=lambda kw: {"status": True, "data": [{"x": 1, "y": 2, "w": 3, "h": 4}]})

    lbl = Label.new("A", "#ff0000")
    worker = ZSamPredictWorker(
        api,
        "a",
        "a.png",
        [lbl],
        rects=[(0, 0, 10, 10)],
        mode=__import__("zlabel.utils", fromlist=["AutoMode"]).AutoMode.SAM,
        return_type=1,
    )
    with qtbot.waitSignal(worker.emitter.sigFinished, timeout=2000) as blocker:
        worker.run()
    results = blocker.args[0]
    assert len(results) == 1
    r = results[0].result
    assert isinstance(r, RectangleResult)
    assert (r.x, r.y, r.w, r.h) == (1, 2, 3, 4)


def test_sam_predict_worker_forwards_crop_box(qtbot):
    """The worker forwards crop_box to the backend predict."""
    captured = {}

    api = FakeApi(_predict=lambda kw: captured.update(kw) or {"status": True, "data": []})

    lbl = Label.new("A", "#ff0000")
    worker = ZSamPredictWorker(
        api,
        "a",
        "a.png",
        [lbl],
        rects=[(0, 0, 10, 10)],
        mode=AutoMode.SAM,
        return_type=1,
        crop_box=(8, 8, 40, 40),
    )
    with qtbot.waitSignal(worker.emitter.sigFinished, timeout=2000):
        worker.run()
    assert captured["crop_box"] == (8, 8, 40, 40)


def test_sam_predict_worker_polygon(qtbot):
    api = FakeApi(
        _predict=lambda kw: {
            "status": True,
            "data": [{"points": [{"x": 1, "y": 1}, {"x": 5, "y": 1}, {"x": 5, "y": 5}]}],
        }
    )
    from zlabel.utils import PolygonResult
    from zlabel.widgets.zworker import ZSamPredictWorker

    lbl = Label.new("A", "#ff0000")
    worker = ZSamPredictWorker(
        api, "a", "a.png", [lbl], points=[(2, 2)], labels=[1.0], mode=AutoMode.SAM, return_type=2
    )
    with qtbot.waitSignal(worker.emitter.sigFinished, timeout=2000) as blocker:
        worker.run()
    results = blocker.args[0]
    assert len(results) == 1
    r = results[0].result
    assert isinstance(r, PolygonResult)
    assert r.points == [(1, 1), (5, 1), (5, 5)]


def test_sam_predict_worker_failed(qtbot):
    api = FakeApi(_predict=lambda kw: {"status": False, "data": []})
    from zlabel.widgets.zworker import ZSamPredictWorker

    lbl = Label.new("A", "#ff0000")
    worker = ZSamPredictWorker(
        api, "a", "a.png", [lbl], points=[(1, 1)], labels=[1.0], mode=AutoMode.SAM, return_type=1
    )
    with qtbot.waitSignal(worker.emitter.sigFailed, timeout=2000):
        worker.run()


def test_rects_to_results_offsets():
    lbl = Label.new("A", "#ff0000")
    worker = ZSamPredictWorker(None, "a", "a.png", [lbl], mode=AutoMode.SAM, return_type=1)  # type: ignore[arg-type]
    results = worker.rects_to_results([(10, 20, 30, 40)], x0=1, y0=2)
    r = results[0].result
    assert (r.x, r.y, r.w, r.h) == (11, 22, 30, 40)
    assert r.origin == "SAM"


# ---------------------------------------------------------------------------
# ZLoginThread
# ---------------------------------------------------------------------------
def test_login_thread_success(qtbot):
    api = FakeApi()
    thread = ZLoginThread(api, "u", "p")
    with qtbot.waitSignal(thread.login_success, timeout=2000) as blocker:
        thread.start()
    assert blocker.args == ["token-123"]
    thread.wait(1000)


def test_login_thread_fail(qtbot):
    class FailingApi(FakeApi):
        def login(self, username, password):
            return None  # failed login -> no token

    thread = ZLoginThread(FailingApi(), "u", "p")
    with qtbot.waitSignal(thread.login_fail, timeout=2000):
        thread.start()
    thread.wait(1000)
