import os
import tempfile
from collections.abc import Callable
from pathlib import Path

# GUI tests run headless; set before any QApplication is created.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Redirect the user home used by ZSettings/MainWindow default paths BEFORE any
# zlabel import, so constructing widgets never touches the real ~/.zlabel.
_TEST_HOME = Path(tempfile.mkdtemp(prefix="zlabel-test-home-"))
from pyqtgraph.Qt.QtCore import QDir

QDir.homePath = staticmethod(lambda: str(_TEST_HOME))  # type: ignore[method-assign]

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
HAVE_MNN = _have("MNN")


def _have_models() -> bool:
    if not (HAVE_CV and HAVE_MNN):
        return False
    from zlabel.utils.paths import resource_dir

    d = resource_dir() / "models" / "mnn"
    return (d / "edge_sam_3x_encoder.mnn").exists() and (d / "edge_sam_3x_decoder.mnn").exists()


HAVE_MODELS = _have_models()

skip_no_local = pytest.mark.skipif(
    not (HAVE_CV and HAVE_MNN),
    reason="local inference deps not installed (uv sync --extra local)",
)
skip_no_models = pytest.mark.skipif(
    not HAVE_MODELS,
    reason="MNN models not present in data/models/mnn (gitignored)",
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
    """Duck-typed predictor returning a full-size mask, so the ZSamWorker
    SAM branch can be tested without loading an MNN model."""
    from zlabel.models.ztypes import SamOnnxResult

    class _FakeSamModel:
        def set_image(self, img: np.ndarray):
            pass

        def predict(self, points=None, labels=None, bboxes=None):
            mask = np.zeros((64, 64), dtype=np.float32)
            mask[16:48, 16:48] = 255
            return [SamOnnxResult(mask=mask, score=1.0)]

    return _FakeSamModel()
