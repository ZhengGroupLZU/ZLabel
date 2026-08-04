import sys
from pathlib import Path


def app_root() -> Path:
    """Return the app base directory, works both in dev and frozen builds.

    - dev: repo root (parents[2] of zlabel/utils/)
    - PyInstaller: sys._MEIPASS
    - Nuitka / cx_Freeze: directory of the executable
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return Path(base)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_dir() -> Path:
    """Directory holding runtime resources (onnx model files, etc.)."""
    return app_root() / "data"
