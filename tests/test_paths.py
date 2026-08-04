from dataclasses import dataclass
from pathlib import Path

import zlabel.utils.paths as paths


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
    monkeypatch.setattr(paths, "sys", _FakeSys(frozen=True, _MEIPASS=r"C:\bundle\_MEI123"))
    assert paths.app_root() == Path(r"C:\bundle\_MEI123")


def test_app_root_frozen_exec_dir(monkeypatch):
    monkeypatch.setattr(paths, "sys", _FakeSys(frozen=True, executable=r"C:\app\ZLabel.exe"))
    assert paths.app_root() == Path(r"C:\app")


def test_resource_dir_frozen(monkeypatch):
    monkeypatch.setattr(paths, "sys", _FakeSys(frozen=True, _MEIPASS=r"C:\bundle\_MEI123"))
    assert paths.resource_dir() == Path(r"C:\bundle\_MEI123\data")
