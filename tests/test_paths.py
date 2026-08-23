import sys
from dataclasses import dataclass
from pathlib import Path

import zlabel.utils.paths as paths

_IS_WINDOWS = sys.platform.startswith("win")
_FAKE_MEIPASS = r"C:\bundle\_MEI123" if _IS_WINDOWS else "/opt/bundle/_MEI123"
_FAKE_EXECUTABLE = r"C:\app\ZLabel.exe" if _IS_WINDOWS else "/opt/app/ZLabel"


@dataclass
class _FakeSys:
    frozen: bool = False
    _MEIPASS: str | None = None
    executable: str = ""


def test_app_root_dev():
    root = paths.app_root()
    assert (root / "zlabel").is_dir()
    assert (root / "pyproject.toml").exists()


def test_resource_dir_dev():
    assert paths.resource_dir() == paths.app_root() / "data"


def test_app_root_pyinstaller(monkeypatch):
    monkeypatch.setattr(paths, "sys", _FakeSys(frozen=True, _MEIPASS=_FAKE_MEIPASS))
    assert paths.app_root() == Path(_FAKE_MEIPASS)


def test_app_root_frozen_exec_dir(monkeypatch):
    monkeypatch.setattr(paths, "sys", _FakeSys(frozen=True, executable=_FAKE_EXECUTABLE))
    assert paths.app_root() == Path(_FAKE_EXECUTABLE).resolve().parent


def test_resource_dir_frozen(monkeypatch):
    monkeypatch.setattr(paths, "sys", _FakeSys(frozen=True, _MEIPASS=_FAKE_MEIPASS))
    assert paths.resource_dir() == Path(_FAKE_MEIPASS) / "data"
