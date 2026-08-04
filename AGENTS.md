# AGENTS.md

PySide6 + pyqtgraph desktop image-labeling app (GUI client for an external ZL annotation server). Managed with `uv`; Python 3.12 (`.python-version`, `requires-python >=3.10,<3.14`).

## Commands

- Setup: `uv sync` (PyPI index overridden to Tsinghua mirror in `pyproject.toml`)
- Run: `uv run python zlabel.py` — entry point is `zlabel.py`, `.vscode/launch.json` also launches `zlabel.py`.
- Lint: `uv run ruff check .` and `uv run ruff format .` (line-length 120; `ruff` is the configured formatter)
- Regenerate Qt generated code: `uv run python uic_rcc.py` (also runs `lupdate` for i18n)
- Compile translations: `uv run pyside6-lrelease i18n/zh_CN.ts -qm i18n/zh_CN.qm`
- Build: `uv run python build.py` (Nuitka default; add `--pyinstaller`, `--debug`; output 7z in `build/`) or `uv run python setup.py` (cx_Freeze + Inno Setup via `setup.iss`)
- Tests: do NOT rely on `pytest` — `tests/test_zworker.py` is stale (imports removed `zlabel.models.sam_onnx`), requires opencv-python (not a dependency) and a missing `401.png`.

## Architecture

- `zlabel/main.py` — app entry; `zlabel/widgets/mainwindow.py` — main window; `zlabel/widgets/canvas.py` — pyqtgraph-based annotation canvas.
- `zlabel/utils/project.py` — all pydantic data models (`User`, `Label`, `Result`/`RectangleResult`/`PolygonResult`, `Annotation`, `Task`, `Project`). Annotations serialize to JSON; `Project.save_json` deliberately excludes `tasks` (fetched from the server).
- `zlabel/utils/api_helper.py` (`ZLServerApiHelper`) — HTTP client for the external server, defaults to `http://127.0.0.1:8000`. The app depends on a running backend; tasks/images/projects come from it.
- `zlabel/utils/__init__.py` re-exports models/enums — prefer importing from `zlabel.utils` over deep paths.

## Conventions & gotchas

- Qt is always imported through the pyqtgraph wrapper (`from pyqtgraph.Qt.QtWidgets import ...`), not `PySide6.*` directly — keeps binding agnosticness.
- `zlabel/widgets/ui/*.py` and `icons_rc.py` are GENERATED (pyside6-uic/rcc). Edit the sources under `resources/ui/*.ui` and `resources/icons.qrc`, then regenerate. Never hand-edit generated files. mypy excludes `zlabel/widgets/ui/`.
- SAM prediction needs onnx model files in `data/`, which is gitignored — local runs may fail without them.
- Version is single-sourced from `pyproject.toml` (`project.version`); `build.py` and `setup.py` parse it. `setup.py` also rewrites `setup.iss` (version + src dir).
- `build/`, `dist/`, `data/`, `*.zproj`, `.venv/` are gitignored; don't commit build artifacts or model files.
