"""Run MNN inference in a separate process.

MNN's forward holds the Python GIL, which would freeze the GUI event loop when
called from a background thread. A single-worker process pool keeps the model in
a child process so inference never blocks the UI thread.
"""

from __future__ import annotations

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

import numpy as np

_PREDICTOR = None
_pool: ProcessPoolExecutor | None = None


def _init_worker(model_dir, model_name, backend, threads):
    global _PREDICTOR
    from zlabel.models.predictor import Predictor

    _PREDICTOR = Predictor(model_dir=model_dir, model_name=model_name, backend=backend, threads=threads)


def _run_predict(args) -> list[dict]:
    img, points, labels, bboxes = args
    assert _PREDICTOR is not None
    _PREDICTOR.set_image(img)
    results = _PREDICTOR.predict(points=points, labels=labels, bboxes=bboxes)
    return [{"mask": r.mask, "score": r.score, "box": r.box} for r in results]


def predict(
    model_dir: str,
    model_name: str,
    backend: str,
    img: np.ndarray,
    points=None,
    labels=None,
    bboxes=None,
    threads: int = 4,
) -> list[dict]:
    global _pool
    if _pool is None:
        ctx = mp.get_context("spawn")
        _pool = ProcessPoolExecutor(
            max_workers=1,
            mp_context=ctx,
            initializer=_init_worker,
            initargs=(model_dir, model_name, backend, threads),
        )
    return _pool.submit(_run_predict, (img, points, labels, bboxes)).result()


class ProcessPredictor:
    """Drop-in Predictor facade backed by the process pool (MNN runs off the UI process)."""

    def __init__(self, model_dir: str, model_name: str, backend: str = "AUTO", threads: int = 4):
        self._model_dir = model_dir
        self._model_name = model_name
        self._backend = backend
        self._threads = threads
        self._img: np.ndarray | None = None

    def set_image(self, img: np.ndarray):
        self._img = img

    def reset_image(self):
        self._img = None

    def predict(self, points=None, labels=None, bboxes=None):
        if self._img is None:
            raise RuntimeError("call set_image() first")
        from zlabel.models.process_backend import predict as _predict
        from zlabel.models.ztypes import SamOnnxResult

        raw = _predict(
            self._model_dir,
            self._model_name,
            self._backend,
            self._img,
            points,
            labels,
            bboxes,
            self._threads,
        )
        return [SamOnnxResult(mask=r["mask"], score=r["score"], box=r["box"]) for r in raw]
