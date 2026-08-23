import platform

import numpy as np
import pytest

HAVE_WXOCR = (platform.system() == "Windows") and (
    (
        __import__("zlabel.utils.paths", fromlist=["resource_dir"]).resource_dir()
        / "WeChat-Local-OCR-Serve"
        / "wxocr"
        / "WeChatOCR.exe"
    ).exists()
)

pytestmark = pytest.mark.skipif(
    not HAVE_WXOCR,
    reason="WeChat OCR engine (wxocr) not present in data/WeChat-Local-OCR-Serve",
)


@pytest.fixture(scope="module")
def wxocr_client():
    from zlabel.utils.paths import resource_dir
    from zlabel.utils.wechat_ocr.client import WeChatOcrClient

    d = resource_dir() / "WeChat-Local-OCR-Serve" / "wxocr"
    c = WeChatOcrClient(str(d))
    ok = c.start()
    assert ok, "failed to start WeChat OCR engine"
    yield c
    c.stop()


def _make_image(text="2025-03-01 14:00"):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (300, 70), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 30)
    d.text((10, 15), text, fill="black", font=font)
    return img


def test_engine_available(wxocr_client):
    assert wxocr_client is not None


def test_ocr_recognizes_timestamp(wxocr_client, tmp_path):
    p = tmp_path / "ts.png"
    _make_image().save(p)
    text = wxocr_client.ocr_image(str(p))
    assert text is not None, "OCR returned no text"
    assert "2025" in text

    from zlabel.utils.ocr import extract_datetime

    assert extract_datetime(text) == "2025-03-01 14:00"


def test_ocr_image_np_array(wxocr_client, monkeypatch):
    """utils.ocr.ocr_image: np array -> temp file -> engine, reusing the fixture
    engine so no second WeChatOCR subprocess races the first."""
    import zlabel.utils.ocr as ocr

    monkeypatch.setattr(ocr, "_client", lambda: wxocr_client)
    img = _make_image()
    text = ocr.ocr_image(np.asarray(img, dtype=np.uint8))
    assert text is not None and "2025" in text
    assert ocr.extract_datetime(text) == "2025-03-01 14:00"
