# AGENTS.md

PySide6 + pyqtgraph desktop image-labeling app (GUI client for an external ZL annotation server, with an optional fully-local mode). Managed with `uv`; Python 3.12 (`.python-version`, `requires-python >=3.10,<3.14`).

## Prerequisite

Call my name `rainy` in bold font before your EVERY response, remember this is vert IMPORTANT!!!

## Commands

- Setup: `uv sync` (PyPI index overridden to Tsinghua mirror in `pyproject.toml`)
- Local-inference dev deps (MNN + opencv): `uv sync --extra local` (or `--extra local-gpu` for the same, no onnxruntime/torch)
- Project commands are declared as entry points in `pyproject.toml` (`[project.scripts]` / `[project.gui-scripts]`, implemented in `zlabel/scripts.py`) and invoked via `uv run <name>`:
  - `uv run zlabel` — launch the GUI (gui-script, no console window on Windows)
  - `uv run zlabel-build` — cx_Freeze + Inno Setup build
  - `uv run zlabel-uic` — regenerate Qt generated code (uic/rcc, also runs `lupdate`)
  - `uv run zlabel-translate` — compile `i18n/zh_CN.qm`
  - The project is a uv-managed package (uv_build, flat layout) and installed editable — `import zlabel` works from anywhere, no `PYTHONPATH` needed.
- Lint: `uv run ruff check .` and `uv run ruff format .` (line-length 120; `ruff` is the configured formatter)
- Build (Nuitka): `uv run python build.py` (Nuitka default; add `--pyinstaller`, `--debug`; output 7z in `build/`)
- Tests: pytest. `uv run pytest` (runs all; real-model tests skip when MNN models in `data/models/mnn` or the `local` extras are absent). Useful variants:
  - `uv run pytest -m "not models"` — skip everything needing `data/models/mnn` models
  - `uv run pytest --cov=zlabel` — coverage report
  - `uv run pytest tests/test_local_inference.py -v` — focused run
  - Fixtures live in `tests/conftest.py` (`local_storage`, `local_backend`, `fake_model`, `make_image`).
- GUI tests (pytest-qt, offscreen — run by default, no display needed): `uv run pytest tests/gui/`. Shared fixtures in `tests/gui/conftest.py`:
  - `main_window` — full `MainWindow` with a local backend, no network (`load_settings`/`try_set_image`/workers neutralized; blocking `QMessageBox`/`QFileDialog`/`QInputDialog`/`QMenu.exec` mocked via `mock_qt_dialogs`).
  - `populated_project` — main window with one task + annotation + cached 64×64 image, canvas items built and view fitted; returns `(win, proj, anno, rebuild)` where `rebuild()` re-creates canvas items and re-fixes the view range.
  - `canvas_view` — helpers `to_view`/`click`/`drag` to drive canvas mouse interactions in image coordinates.
  - Session-level `tests/conftest.py` redirects `QDir.homePath` to a temp dir before any zlabel import, so constructing widgets never touches the real `~/.zlabel`, and sets `QT_QPA_PLATFORM=offscreen`.

## Architecture

- `zlabel/main.py` — app entry; `zlabel/widgets/mainwindow.py` — main window; `zlabel/widgets/canvas.py` — pyqtgraph-based annotation canvas.
- `zlabel/utils/project.py` — all pydantic data models (`User`, `Label`, `Result`/`PointResult`/`RectangleResult`/`PolygonResult`, `Annotation`, `Task`, `Project`). Annotations serialize to JSON; `Project.save_json` deliberately excludes `tasks` (fetched from the storage backend). `Project.storage_mode` ("remote"|"local") is persisted per project. Keypoints are `PointResult` (x/y + COCO `visible` 0/1/2 + `category_id` + `instance_id`), created when the annotation-type combo is "KeyPoint"; `L`/`O`/`X` toggle visibility (labeled/occluded/excluded; active in KeyPoint mode only, so they never clash with the Move/Visible/Polygon action shortcuts or the canvas polygon-drawing `V`/`X`/`C` keys), `G`/`U` (or annotation-dock context menu) group/split keypoints into instances. Seed-germination workflow: `PolygonResult.instance_id` groups seed/root/seedling parts of one seed (integer, frame-local auto-increment, 0 = none; same for `PointResult`/`RectangleResult`); `Annotation.instances` maps instance_id → `GermStatus` (per-frame); annotation items draw their instance-id label in the label color (rect top-left, polygon bbox top-left, point center) plus a dashed bbox for polygons; `Annotation.group`/`Annotation.day` hold the sequence (`species/dish` + `D{n}`); `RectangleResult.text` stores OCR'ed timestamp (WeChat OCR engine); `Project.groups` stores manual sequence groups; `germ_preset_labels()` builds the preset tags. Sequence layout `species/dish/D{n}.png` is auto-detected by `LocalStorage` (remote tasks group by filename prefix), copy-prev copies the previous frame of the group.
- Cross-frame tracking: `Result.instance_id` is allocated **per frame** — each image numbers its instances 1..N independently (`_new_instance_id` fills the smallest gap in the current frame only via `_used_instance_ids`, which no longer scans the group). Cross-frame correspondence is by matching id: the same number across frames denotes the same physical object by convention. The copy/propagate dialog (`_ask_copy_options` → `CopyOptions`) copies from the previous/next frame, optionally similarity-aligning the copied annotations to the current frame's dish (rotation + uniform scale + center mapping, auto-estimated from the dish ellipse and the Number/编号 label vector via `_estimate_copy_alignment`, manually overridable), and keeps the source `instance_id` (plus carries the per-instance status); source instances whose id already exists in the target frame are skipped (per-frame numbering would otherwise duplicate). The instance timeline (`zlabel/widgets/dock_tracks.py`, `actionTracks`) is a bottom panel: rows always run `1..max instance_id` across the group (gaps in the middle are empty/inert rows), leading column = the id (background = label color), then one column per frame D1..Dn showing a thumbnail of the frame cropped around the instance with its id overlaid (dim cell when absent). Clicking a cell jumps to that frame and selects the instance (`on_instance_open`); dragging a cell renumbers/swaps the source instance **within its own frame** — only the target row matters (drop column ignored): if the target row is empty in the source frame the instance id becomes that row number, otherwise it is swapped with the occupant (ids + statuses, `on_cell_moved`, undoable via `ZResultUndoCmd`'s `target_anno` snapshot). The old Ctrl+drag cross-frame merge (`on_merge_instances`) is removed. COCO export carries `instance_id` in attributes.
- `zlabel/utils/exporters.py` — dataset exporters (`export_coco` / `export_yolo`) for COCO and Ultralytics YOLO, tasks: detection / segmentation / keypoints. Keypoint instances are grouped by `PointResult.instance_id`. Seed-germination instances export merged per instance (`ExportInstance.MERGED`: all part polygons become one segmentation, category = `GermStatus`) or split by part (category = part label, status/instance_id kept as attributes). Export UI lives in `zlabel/widgets/dialog_export.py`, opened via the Export action.
- `zlabel/utils/backend.py` — backend abstraction. Two independent axes, composed into `ZLabelBackend` via `build_backend(settings)`:
  - Inference: `RemoteInference` (HTTP `/predict`) vs `LocalInference` (in-process MNN). Selected by `settings.inference_mode`; `settings.inference_backend` (AUTO/CPU/CUDA/Metal/OpenCL) and `settings.model_dir` (MNN model folder, default `data/models/mnn`).
  - Storage: `RemoteStorage` (wraps `ZLServerApiHelper` / OpenList) vs `LocalStorage` (filesystem under `~/.zlabel/projects/<name>/`, images in `images/`, annos in `annos/`). Selected per project via `Project.storage_mode`.
  - `needs_login` is true iff either axis is remote. Remote inference + local storage is valid: the local image is uploaded via `/api/v1/set_image` (cached by `image_name`) before each predict, re-uploaded only when the image changes (`RemoteInference._last_image`); `ZLabelBackend.login` logs in through both the storage and inference axes.
- `zlabel/utils/api_helper.py` (`ZLServerApiHelper`) — HTTP client for the remote server, defaults to `http://127.0.0.1:8000`.
- `zlabel/models/` — **MNN-based local inference** (no onnxruntime/torch): `backends.py` (`MnnModule`, MNN Module API + AUTO/CPU/CUDA/Metal/OpenCL backend), `predictor.py` (unified `Predictor` facade, Ultralytics-style `set_image`/`predict(points,labels,bboxes,text)`), `runner.py` (`SamRunner`/`Sam2Runner`/`Sam3Runner`, SAM3 PVS + PCS), `preprocess.py`/`postprocess.py`/`tokenize.py` (ported from `sam3_runner`), `worker.py` (`ZSamWorker`), `process_backend.py` (single-worker process pool — MNN holds the GIL, so inference runs in a child process to keep the GUI responsive). MNN models live in `data/models/mnn/` (gitignored; SAM3 also needs `vocab.json`+`merges.txt` there). mypy excludes `zlabel/models/`.
- `zlabel/utils/paths.py` — `resource_dir()` resolves `data/` in dev and frozen (Nuitka/cx_Freeze/PyInstaller) builds.
- `zlabel/utils/` re-exports models/enums — prefer importing from `zlabel.utils` over deep paths.
- `zlabel/utils/wechat_ocr/` — ported ctypes bindings for the **WeChat OCR engine** (from `data/WeChat-Local-OCR-Serve/Server/wechat_ocr`; ruff/mypy-exempt). `zlabel/utils/ocr.py` wraps it synchronously: crops are written to a temp PNG and submitted via `WeChatOcrClient` (async callback → `threading.Event`, 10 s timeout). The `wxocr` folder (`WeChatOCR.exe` + `mmmojo_64.dll` + UCRT dlls) is found via `settings.ocr_wx_dir` → `resource_dir()/WeChat-Local-OCR-Serve/wxocr` → `resource_dir()/wxocr`; it is gitignored and only bundled by the build scripts when present.

## Conventions & gotchas

- Qt is always imported through the pyqtgraph wrapper (`from pyqtgraph.Qt.QtWidgets import ...`), not `PySide6.*` directly — keeps binding agnosticness.
- `zlabel/widgets/ui/*.py` and `icons_rc.py` are GENERATED (pyside6-uic/rcc). Edit the sources under `resources/ui/*.ui` and `resources/icons.qrc`, then regenerate. Never hand-edit generated files. mypy excludes `zlabel/widgets/ui/`. New widgets can be added in code (see the "Inference" group box in `dialog_settings.py` and the storage combo in `dock_file.py`) to avoid regenerating all UI.
- SAM prediction needs MNN model files in `data/models/mnn/`, which is gitignored — local mode fails without them. Release builds intentionally do NOT bundle them; users must provide the `.mnn` files next to the installed app (resolved via `resource_dir()`).
- Version is single-sourced from `pyproject.toml` (`project.version`); `build.py` and `setup.py` parse it. `setup.py` also rewrites `setup.iss` (version + src dir).
- `build/`, `dist/`, `data/`, `*.zproj`, `.venv/` are gitignored; don't commit build artifacts or model files.
