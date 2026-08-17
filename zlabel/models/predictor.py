"""Unified predictor facade over the MNN runners, mirroring the Ultralytics-style API.

predictor = Predictor(model_dir="...", model_name="EdgeSAM", backend="CPU")
predictor.set_image(image_bgr)
results = predictor.predict(points=[[x, y]], labels=[1])
results = predictor.predict(bboxes=[[x1, y1, x2, y2]])
results = predictor.predict(text=["person"])        # SAM3 PCS
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from zlabel.models.backends import configure_backend
from zlabel.models.runner import Sam2Runner, Sam3Runner, SamRunner
from zlabel.models.ztypes import PvsResult, SamOnnxResult

MODEL_FILES: dict[str, tuple[str, str]] = {
    "SAM": ("sam_vit_b_encoder.mnn", "sam_vit_b_decoder.mnn"),
    "EdgeSAM": ("edge_sam_3x_encoder.mnn", "edge_sam_3x_decoder.mnn"),
    "SlimSAM": ("slimsam_encoder.mnn", "slimsam_decoder.mnn"),
    "SAM2": ("sam2_hiera_large_encoder.mnn", "sam2_hiera_large_decoder.mnn"),
}


def build_runner(
    model_dir: str | Path,
    model_name: str,
    backend: str = "AUTO",
    threads: int = 4,
    conf: float = 0.25,
    iou: float = 0.7,
):
    configure_backend(backend, threads)
    d = Path(model_dir)
    if model_name == "SAM3":
        return Sam3Runner(d, backend=backend, threads=threads, conf=conf, iou=iou)
    enc, dec = MODEL_FILES.get(model_name, MODEL_FILES["EdgeSAM"])
    if model_name == "SAM2":
        return Sam2Runner(d / enc, d / dec, letterbox=True)
    if model_name == "SlimSAM":
        return SamRunner(d / enc, d / dec, letterbox=True)
    return SamRunner(d / enc, d / dec)


def _to_results(r) -> list[SamOnnxResult]:
    if isinstance(r, SamOnnxResult):
        return [r]
    if isinstance(r, PvsResult):
        return [SamOnnxResult(mask=r.mask.astype(np.float32), score=r.score, box=tuple(r.box))]
    return list(r)


class Predictor:
    """Local MNN predictor with an Ultralytics-style API."""

    def __init__(
        self,
        model_dir: str | Path,
        model_name: str = "EdgeSAM",
        backend: str = "AUTO",
        threads: int = 4,
        conf: float = 0.25,
        iou: float = 0.7,
    ):
        self.model_dir = str(Path(model_dir))
        self.model_name = model_name
        self.backend = backend
        self.threads = threads
        self.conf = conf
        self.iou = iou
        self._runner = None

    def setup_model(self):
        if self._runner is None:
            self._runner = build_runner(
                self.model_dir, self.model_name, self.backend, self.threads, self.conf, self.iou
            )
        return self

    def set_image(self, image: np.ndarray) -> Predictor:
        self.setup_model()
        self._runner.set_image(image)
        return self

    def reset_image(self):
        self._runner = None

    def predict(
        self,
        points: list | None = None,
        labels: list | None = None,
        bboxes: list | None = None,
        text: list | str | None = None,
        conf: float | None = None,
        iou: float | None = None,
    ) -> list[SamOnnxResult]:
        """Run inference and return a flat list of SamOnnxResult (mask/score/box)."""
        self.setup_model()
        if conf is not None:
            self._runner.conf = conf
        if iou is not None:
            self._runner.iou = iou

        results: list[SamOnnxResult] = []
        if text is not None:
            if not hasattr(self._runner, "segment_text"):
                raise ValueError("text prompts require the SAM3 model")
            return list(self._runner.segment_text(text, bboxes))

        if points is None and bboxes is None:
            raise ValueError("provide at least one of points= or bboxes=")

        if bboxes:
            for b in bboxes:
                results.extend(_to_results(self._runner.segment_box([float(v) for v in b])))
        if points:
            pts = [tuple(float(v) for v in p) for p in points]
            lbs = list(labels) if labels is not None else [1] * len(pts)
            results.extend(_to_results(self._runner.segment_points(pts, lbs)))
        return results

    def __call__(self, *args, **kwargs):
        return self.predict(*args, **kwargs)
