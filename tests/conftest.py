from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from PIL import Image


def _have(pkg: str) -> bool:
    try:
        __import__(pkg)
        return True
    except ImportError:
        return False


HAVE_CV = _have("cv2")
HAVE_ORT = _have("onnxruntime")


def _have_models() -> bool:
    if not (HAVE_CV and HAVE_ORT):
        return False
    from zlabel.utils.paths import resource_dir

    return (resource_dir() / "edge_sam_3x_encoder.onnx").exists() and (
        resource_dir() / "edge_sam_3x_decoder.onnx"
    ).exists()


HAVE_MODELS = _have_models()

skip_no_local = pytest.mark.skipif(
    not (HAVE_CV and HAVE_ORT),
    reason="local inference deps not installed (uv sync --extra local)",
)
skip_no_models = pytest.mark.skipif(
    not HAVE_MODELS,
    reason="onnx models not present in data/ (gitignored)",
)


@pytest.fixture
def make_image() -> Callable[..., Image.Image]:
    def _make(h: int = 64, w: int = 64, seed: int = 42, color: int | None = None) -> Image.Image:
        if color is not None:
            arr = np.full((h, w, 3), color, dtype=np.uint8)
        else:
            arr = np.random.default_rng(seed).integers(0, 255, (h, w, 3), dtype=np.uint8)
        return Image.fromarray(arr)

    return _make


@pytest.fixture
def local_storage(tmp_path: Path, make_image: Callable[..., Image.Image]):
    """LocalStorage with the default layout (images in projects/<name>/images)."""
    from zlabel.utils.backend import LocalStorage

    imgdir = tmp_path / "projects" / "proj" / "images"
    imgdir.mkdir(parents=True)
    make_image(h=64, w=64).save(imgdir / "a.png")
    make_image(h=32, w=32, seed=1).save(imgdir / "b.jpg")
    storage = LocalStorage(root_dir=tmp_path, project_name="proj")
    storage.anno_dir.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.fixture
def local_storage_custom(tmp_path: Path, make_image: Callable[..., Image.Image]):
    """LocalStorage pointed at an arbitrary user-selected images folder."""
    from zlabel.utils.backend import LocalStorage

    imgdir = tmp_path / "custom"
    imgdir.mkdir(parents=True)
    make_image().save(imgdir / "x.png")
    storage = LocalStorage(root_dir=tmp_path, project_name="proj", local_dir=str(imgdir))
    storage.anno_dir.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.fixture
def settings_local(tmp_path: Path):
    from zlabel.widgets.zsettings import ZSettings

    s = ZSettings(root_dir=tmp_path)
    s.project.storage_mode = "local"
    s.inference_mode = "local"
    return s


@pytest.fixture
def local_backend(settings_local):
    from zlabel.utils.backend import build_backend

    return build_backend(settings_local)


@pytest.fixture
def fake_model():
    """Duck-typed SAM model returning a full-size mask, so the ZSamWorker
    SAM branch can be tested without a real onnx model."""
    from zlabel.models.ztypes import SamOnnxResult

    class _FakeSamModel:
        def predict(self, img: np.ndarray, prompts):
            h, w = img.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4] = 255
            return SamOnnxResult(mask=mask, score=1.0)

    return _FakeSamModel()
