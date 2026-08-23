from pathlib import Path

import tomllib

import zlabel


def test_version_matches_pyproject():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert zlabel.__version__ == data["project"]["version"]
