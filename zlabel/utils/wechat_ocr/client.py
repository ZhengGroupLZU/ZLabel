"""Synchronous wrapper around the ported WeChat OCR engine (OcrManager).

The underlying engine is asynchronous: ``DoOCRTask`` submits a picture and the
result arrives on a native callback thread. This client serializes submissions
and blocks the caller until the callback (or a timeout).
"""

from __future__ import annotations

import os
import threading

from zlabel.utils.wechat_ocr.ocr_manager import OcrManager

OCR_TIMEOUT = 10.0


class WeChatOcrClient:
    def __init__(self, wxocr_dir: str) -> None:
        self._wxocr_dir = wxocr_dir
        self._manager: OcrManager | None = None
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._result: str | None = None

    def start(self) -> bool:
        """Load the engine (wxocr folder with mmmojo dll + WeChatOCR.exe)."""

        ocr_exe = os.path.join(self._wxocr_dir, "WeChatOCR.exe")
        if not os.path.exists(ocr_exe):
            return False
        try:
            self._manager = OcrManager(self._wxocr_dir)
            self._manager.SetExePath(ocr_exe)
            self._manager.SetUsrLibDir(self._wxocr_dir)
            self._manager.SetOcrResultCallback(self._on_result)
            self._manager.StartWeChatOCR()
        except Exception:
            self._manager = None
            return False
        return True

    def stop(self) -> None:
        with self._lock:
            if self._manager is not None:
                try:
                    self._manager.KillWeChatOCR()
                except Exception:
                    pass
                self._manager = None

    def _on_result(self, image_path: str, results: dict) -> None:
        texts = [str(i.get("text", "")) for i in results.get("ocrResult", []) if i.get("text")]
        self._result = " ".join(t.strip() for t in texts if t.strip()) or None
        self._event.set()

    def ocr_image(self, image_path: str) -> str | None:
        """Run OCR on an image file, blocking until the callback (or timeout)."""
        if self._manager is None:
            if not self.start():
                return None
        with self._lock:
            self._event.clear()
            self._result = None
            try:
                if self._manager is None:
                    return None
                self._manager.DoOCRTask(image_path)
            except Exception:
                return None
            if not self._event.wait(OCR_TIMEOUT):
                return None
            return self._result
