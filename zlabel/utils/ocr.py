"""OCR for timestamp rectangles (WeChat OCR engine; gracefully no-ops when the
wxocr component is unavailable)."""

from __future__ import annotations

import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

from zlabel.utils.paths import resource_dir

_wxocr_dir_override: str = ""


def _find_wxocr_dir() -> str | None:
    """Locate the wxocr folder: explicit setting, packaged resource, then dev tree."""
    candidates = []
    if _wxocr_dir_override:
        candidates.append(_wxocr_dir_override)
    candidates += [
        resource_dir() / "WeChat-Local-OCR-Serve" / "wxocr",
        resource_dir() / "wxocr",
    ]
    for c in candidates:
        p = Path(c)
        if (p / "WeChatOCR.exe").exists() and (p / "mmmojo_64.dll").exists():
            return str(p)
    return None


@lru_cache(maxsize=1)
def _client():
    from zlabel.utils.wechat_ocr.client import WeChatOcrClient

    d = _find_wxocr_dir()
    if d is None:
        return None
    c = WeChatOcrClient(d)
    return c if c.start() else None


def set_wxocr_dir(path: str):
    """Override the wxocr folder (e.g. from settings) and reset the engine cache."""
    global _wxocr_dir_override
    _wxocr_dir_override = path
    _client.cache_clear()


def ocr_available() -> bool:
    return _client() is not None


def ocr_image(image_rgb: np.ndarray) -> str | None:
    """Run WeChat OCR on an RGB array, return the joined recognized text or None."""
    client = _client()
    if client is None:
        return None
    fd, tmp = tempfile.mkstemp(suffix=".png")
    try:
        os.close(fd)
        from PIL import Image

        Image.fromarray(image_rgb).save(tmp)
        return client.ocr_image(tmp)
    except Exception:
        return None
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def extract_datetime(text: str) -> str:
    """Extract a date/time pattern; fall back to the raw text when nothing matches."""
    m = re.search(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?", text)
    if m:
        return m.group(0)
    return text
