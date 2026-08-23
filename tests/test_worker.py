import numpy as np
import pytest

pytest.importorskip("zlabel.models.worker", reason="opencv-python-headless not installed (uv sync --extra local)")

from zlabel.models.worker import ZSamWorker  # noqa: E402
from zlabel.models.ztypes import Point, Rect  # noqa: E402
from zlabel.utils.enums import AutoMode, ReturnType  # noqa: E402


def _img(h: int = 64, w: int = 64) -> np.ndarray:
    return np.random.default_rng(42).integers(0, 255, (h, w, 3), dtype=np.uint8)


def _worker(
    auto_mode: AutoMode = AutoMode.CV,
    return_type: ReturnType = ReturnType.RECT,
    model=None,
) -> ZSamWorker:
    return ZSamWorker(
        model=model,
        anno_id="TEST_RESULT_ID",
        img=_img(),
        auto_mode=auto_mode,
        threshold=100,
        return_type=return_type,
    )


def test_cv_rect():
    results = _worker().run_rect([Rect(x=10, y=10, w=30, h=30)])
    assert isinstance(results, list)
    assert all(hasattr(r, "x") and hasattr(r, "y") for r in results)


def test_cv_polygon():
    results = _worker(return_type=ReturnType.POLYGON).run_rect([Rect(x=10, y=10, w=30, h=30)])
    assert isinstance(results, list)
    for poly in results:
        assert hasattr(poly, "points")


def test_cv_point_whole_image():
    results = _worker().run_point([Point(x=32, y=32)], [1.0])
    assert isinstance(results, list)


def test_sam_point_fake_model(fake_model):
    results = _worker(auto_mode=AutoMode.SAM, model=fake_model).run_point([Point(x=32, y=32)], [1.0])
    assert isinstance(results, list)


def test_sam_empty_mask_returns_empty():
    """A click on background (all-zero mask) yields no detection, not an error."""

    class _ZeroModel:
        def predict(self, points=None, labels=None, bboxes=None):
            from zlabel.models.ztypes import SamOnnxResult

            return [SamOnnxResult(mask=np.zeros((64, 64), np.float32), score=0.0)]

    results = _worker(auto_mode=AutoMode.SAM, model=_ZeroModel()).run_point([Point(x=32, y=32)], [1.0])
    assert results == []


def test_sam_rect_keeps_only_best_candidate():
    """SAM box prompts return several overlapping candidate masks; only the
    highest-scoring one should be turned into annotations (no near-duplicate)."""

    class _MultiMaskModel:
        def predict(self, points=None, labels=None, bboxes=None):
            from zlabel.models.ztypes import SamOnnxResult

            def mask(x0, y0):
                m = np.zeros((64, 64), np.float32)
                m[y0 : y0 + 30, x0 : x0 + 30] = 255
                return m

            return [
                SamOnnxResult(mask=mask(16, 16), score=0.9),
                SamOnnxResult(mask=mask(18, 18), score=0.5),
                SamOnnxResult(mask=mask(20, 20), score=0.2),
            ]

    results = _worker(auto_mode=AutoMode.SAM, model=_MultiMaskModel()).run_rect([Rect(x=10, y=10, w=40, h=40)])
    # Only the score-0.9 candidate (single contour) survives
    assert len(results) == 1
    r = results[0]
    # mask starts at (16,16); dilate(1) -> 15, smoothing keeps it near there
    assert abs(r.x - 15) <= 1 and abs(r.y - 15) <= 1, (r.x, r.y)
