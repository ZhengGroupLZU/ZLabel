# AGENTS.md

PySide6 + pyqtgraph desktop image-labeling app (GUI client for an external ZL annotation server, with an optional fully-local mode). Managed with `uv`; Python 3.12 (`.python-version`, `requires-python >=3.10,<3.14`).

## Commands

- Setup: `uv sync` (PyPI index overridden to Tsinghua mirror in `pyproject.toml`)
- Local-inference dev deps (onnxruntime + opencv): `uv sync --extra local` (or `--extra local-gpu` for onnxruntime-gpu)
- Project commands are declared as entry points in `pyproject.toml` (`[project.scripts]` / `[project.gui-scripts]`, implemented in `zlabel/scripts.py`) and invoked via `uv run <name>`:
  - `uv run zlabel` — launch the GUI (gui-script, no console window on Windows)
  - `uv run zlabel-build` — cx_Freeze + Inno Setup build
  - `uv run zlabel-uic` — regenerate Qt generated code (uic/rcc, also runs `lupdate`)
  - `uv run zlabel-translate` — compile `i18n/zh_CN.qm`
  - The project is a uv-managed package (uv_build, flat layout) and installed editable — `import zlabel` works from anywhere, no `PYTHONPATH` needed.
- Lint: `uv run ruff check .` and `uv run ruff format .` (line-length 120; `ruff` is the configured formatter)
- Build (Nuitka): `uv run python build.py` (Nuitka default; add `--pyinstaller`, `--debug`; output 7z in `build/`)
- Tests: pytest. `uv run pytest` (runs all; real-model tests skip when onnx models in `data/` or the `local` extras are absent). Useful variants:
  - `uv run pytest -m "not models"` — skip everything needing `data/` onnx models
  - `uv run pytest --cov=zlabel` — coverage report
  - `uv run pytest tests/test_local_inference.py -v` — focused run
  - Fixtures live in `tests/conftest.py` (`local_storage`, `local_backend`, `fake_model`, `make_image`). GUI/Qt widgets are intentionally not covered.

## Architecture

- `zlabel/main.py` — app entry; `zlabel/widgets/mainwindow.py` — main window; `zlabel/widgets/canvas.py` — pyqtgraph-based annotation canvas.
- `zlabel/utils/project.py` — all pydantic data models (`User`, `Label`, `Result`/`PointResult`/`RectangleResult`/`PolygonResult`, `Annotation`, `Task`, `Project`). Annotations serialize to JSON; `Project.save_json` deliberately excludes `tasks` (fetched from the storage backend). `Project.storage_mode` ("remote"|"local") is persisted per project. Keypoints are `PointResult` (x/y + COCO `visible` 0/1/2 + `category_id` + `instance_id`), created when the annotation-type combo is "KeyPoint"; `V`/`O`/`M` toggle visibility, `G`/`U` (or annotation-dock context menu) group/split keypoints into instances.
- `zlabel/utils/exporters.py` — dataset exporters (`export_coco` / `export_yolo`) for COCO and Ultralytics YOLO, tasks: detection / segmentation / keypoints. Keypoint instances are grouped by `PointResult.instance_id`. Export UI lives in `zlabel/widgets/dialog_export.py`, opened via the Export action.
- `zlabel/utils/backend.py` — backend abstraction. Two independent axes, composed into `ZLabelBackend` via `build_backend(settings)`:
  - Inference: `RemoteInference` (HTTP `/predict`) vs `LocalInference` (in-process ONNX). Selected by `settings.inference_mode`.
  - Storage: `RemoteStorage` (wraps `ZLServerApiHelper` / OpenList) vs `LocalStorage` (filesystem under `~/.zlabel/projects/<name>/`, images in `images/`, annos in `annos/`). Selected per project via `Project.storage_mode`.
  - `needs_login` is true iff either axis is remote. Remote inference + local storage is invalid → falls back to local inference.
- `zlabel/utils/api_helper.py` (`ZLServerApiHelper`) — HTTP client for the remote server, defaults to `http://127.0.0.1:8000`.
- `zlabel/models/` — **port of the former `zlabel_server/app` inference code**: `sam_onnx.py` (`SamOnnxModel`/`EdgeSam`/`SAM2`), `worker.py` (`ZSamWorker`), `ztypes.py` (`Point`/`Rect`/`Polygon`/`SamReturn`/...). Imports `cv2`/`onnxruntime` lazily (only when `LocalInference` is used), so remote-only installs never load them. mypy excludes `zlabel/models/`.
- `zlabel/utils/paths.py` — `resource_dir()` resolves `data/` in dev and frozen (Nuitka/cx_Freeze/PyInstaller) builds.
- `zlabel/utils/__init__.py` re-exports models/enums — prefer importing from `zlabel.utils` over deep paths.

## Conventions & gotchas

- Qt is always imported through the pyqtgraph wrapper (`from pyqtgraph.Qt.QtWidgets import ...`), not `PySide6.*` directly — keeps binding agnosticness.
- `zlabel/widgets/ui/*.py` and `icons_rc.py` are GENERATED (pyside6-uic/rcc). Edit the sources under `resources/ui/*.ui` and `resources/icons.qrc`, then regenerate. Never hand-edit generated files. mypy excludes `zlabel/widgets/ui/`. New widgets can be added in code (see the "Inference" group box in `dialog_settings.py` and the storage combo in `dock_file.py`) to avoid regenerating all UI.
- SAM prediction needs onnx model files in `data/`, which is gitignored — local mode fails without them. Release builds intentionally do NOT bundle them; users must provide the `.onnx` files next to the installed app (resolved via `resource_dir()`).
- Version is single-sourced from `pyproject.toml` (`project.version`); `build.py` and `setup.py` parse it. `setup.py` also rewrites `setup.iss` (version + src dir).
- `build/`, `dist/`, `data/`, `*.zproj`, `.venv/` are gitignored; don't commit build artifacts or model files.
