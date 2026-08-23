import numpy as np
import pytest

pytest.importorskip("zlabel.models.worker", reason="opencv-python-headless not installed (uv sync --extra local)")

from zlabel.utils.backend import LocalInference, LocalStorage  # noqa: E402


def _inference(tmp_path, make_image, model=None):
    imgdir = tmp_path / "imgs"
    imgdir.mkdir()
    make_image().save(imgdir / "a.png")
    storage = LocalStorage(root_dir=tmp_path, project_name="p", local_dir=str(imgdir))
    inf = LocalInference(storage=storage, model_name="EdgeSAM")
    if model is not None:
        inf._model = model
    return inf


def test_dict_wire_format(tmp_path, make_image, fake_model):
    """ZSamPredictWorker sends {x,y} dicts; LocalInference must accept them."""
    inf = _inference(tmp_path, make_image, fake_model)
    resp = inf.predict("x", "a.png", points=[{"x": 32, "y": 32}], labels=[1.0], threshold=100, mode=1, return_type=1)
    assert resp["status"] is True
    assert resp["mode"] == "SAM"


def test_tuple_format(tmp_path, make_image, fake_model):
    inf = _inference(tmp_path, make_image, fake_model)
    resp = inf.predict("x", "a.png", points=[(32, 32)], labels=[1.0], threshold=100, mode=1, return_type=1)
    assert resp["status"] is True


def test_rect_dict_cv(tmp_path, make_image, fake_model):
    inf = _inference(tmp_path, make_image, fake_model)
    resp = inf.predict("x", "a.png", rects=[{"x": 5, "y": 5, "w": 20, "h": 20}], threshold=100, mode=2, return_type=1)
    assert resp["status"] is True
    assert resp["mode"] == "CV"


def test_missing_image(tmp_path, make_image):
    inf = _inference(tmp_path, make_image)
    resp = inf.predict("x", "nope.png", points=[{"x": 1, "y": 1}], labels=[1.0])
    assert resp["status"] is False
    assert "not found" in resp["msg"]


def test_points_labels_length_mismatch(tmp_path, make_image, fake_model):
    inf = _inference(tmp_path, make_image, fake_model)
    resp = inf.predict("x", "a.png", points=[{"x": 1, "y": 1}], labels=[1.0, 2.0], threshold=100, mode=1, return_type=1)
    assert resp["status"] is False


def test_no_prompt(tmp_path, make_image, fake_model):
    inf = _inference(tmp_path, make_image, fake_model)
    resp = inf.predict("x", "a.png", threshold=100, mode=1, return_type=1)
    assert resp["status"] is False


def test_fake_model_sam(tmp_path, make_image, fake_model):
    """SAM branch without a real onnx model via injected fake."""
    inf = _inference(tmp_path, make_image)
    inf._model = fake_model  # noqa: E402
    resp = inf.predict("x", "a.png", points=[{"x": 32, "y": 32}], labels=[1.0], threshold=100, mode=1, return_type=1)
    assert resp["status"] is True


class _CaptureModel:
    """Duck-typed predictor that records the image size and prompts it receives."""

    def __init__(self):
        self.image_shape = None
        self.last_points = None
        self.last_bboxes = None

    def set_image(self, img):
        self.image_shape = img.shape[:2]

    def predict(self, points=None, labels=None, bboxes=None):
        from zlabel.models.ztypes import SamOnnxResult

        self.last_points = points
        self.last_bboxes = bboxes
        mask = np.zeros((64, 64), dtype=np.float32)
        mask[16:48, 16:48] = 255
        return [SamOnnxResult(mask=mask, score=1.0)]


def test_local_inference_no_crop_keeps_coords(tmp_path, make_image):
    """Without crop_box the image and prompts are passed through unchanged."""
    inf = _inference(tmp_path, make_image)
    model = _CaptureModel()
    inf._model = model
    resp = inf.predict("x", "a.png", points=[{"x": 32, "y": 32}], labels=[1.0], threshold=100, mode=1, return_type=1)
    assert resp["status"] is True
    assert model.image_shape == (64, 64)
    assert model.last_points[0] == (32.0, 32.0)


def test_local_inference_crops_to_dish(tmp_path, make_image):
    """crop_box crops the image to the box, shifts prompts into crop space and
    maps the results back to full-image coordinates."""
    inf = _inference(tmp_path, make_image)
    model = _CaptureModel()
    inf._model = model
    resp = inf.predict(
        "x",
        "a.png",
        points=[{"x": 32, "y": 32}],
        labels=[1.0],
        threshold=100,
        mode=1,
        return_type=1,
        crop_box=(8, 8, 40, 40),
    )
    assert resp["status"] is True
    # the model sees the cropped 32x32 image
    assert model.image_shape == (32, 32)
    # the prompt was shifted into crop space: (32-8, 32-8)
    assert model.last_points[0] == (24.0, 24.0)
    # the result is mapped back to full-image coords (offset +8, +8)
    r = resp["data"][0]
    assert r["x"] >= 8 and r["y"] >= 8


def test_local_inference_crop_out_of_bounds_clipped(tmp_path, make_image):
    """A crop box extending past the image edge is clipped to the bounds."""
    inf = _inference(tmp_path, make_image)
    model = _CaptureModel()
    inf._model = model
    resp = inf.predict(
        "x",
        "a.png",
        points=[{"x": 32, "y": 32}],
        labels=[1.0],
        threshold=100,
        mode=1,
        return_type=1,
        crop_box=(30, 30, 100, 100),  # r/b exceed the 64x64 image
    )
    assert resp["status"] is True
    # clipped to (30,30,64,64) -> 34x34 crop
    assert model.image_shape == (34, 34)
    assert model.last_points[0] == (2.0, 2.0)


@pytest.mark.models
def test_real_edge_sam(tmp_path, make_image):
    """End-to-end local SAM with the bundled EdgeSAM MNN models."""
    from zlabel.utils.paths import resource_dir

    d = resource_dir() / "models" / "mnn"
    if not ((d / "edge_sam_3x_encoder.mnn").exists() and (d / "edge_sam_3x_decoder.mnn").exists()):
        pytest.skip("MNN models not present in data/models/mnn (gitignored)")
    try:
        import MNN  # noqa: F401, E402
    except ImportError:
        pytest.skip("MNN not installed (uv sync --extra local)")
    inf = _inference(tmp_path, make_image)
    resp = inf.predict("x", "a.png", points=[{"x": 32, "y": 32}], labels=[1.0], threshold=100, mode=1, return_type=1)
    assert resp["status"] is True
