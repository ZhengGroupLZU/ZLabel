import numpy as np
import pytest

pytest.importorskip(
    "zlabel.models.worker", reason="opencv-python-headless not installed (uv sync --extra local)"
)

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
    results = _worker(auto_mode=AutoMode.SAM, model=fake_model).run_point(
        [Point(x=32, y=32)], [1.0]
    )
    assert isinstance(results, list)


def test_sam_empty_mask_returns_empty():
    """A click on background (all-zero mask) yields no detection, not an error."""

    class _ZeroModel:
        def predict(self, img, prompts):
            from zlabel.models.ztypes import SamOnnxResult

            return SamOnnxResult(mask=np.zeros(img.shape[:2], dtype=np.uint8), score=0.0)

    results = _worker(auto_mode=AutoMode.SAM, model=_ZeroModel()).run_point(
        [Point(x=32, y=32)], [1.0]
    )
    assert results == []
