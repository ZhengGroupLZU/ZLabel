# Contributing to ZLabel

Thanks for your interest in contributing! This guide explains how to set up a
development environment, understand the codebase, run tests, and build the
application.

## Development Environment

### Prerequisites

- Python 3.10–3.13 (the project is developed with 3.12, see `.python-version`)
- [uv](https://docs.astral.sh/uv/) — the project is managed with `uv`

### Setup

```bash
# install the package and dev dependencies
uv sync

# launch the GUI
uv run zlabel
```

The PyPI index is overridden to the Tsinghua mirror in `pyproject.toml`; adjust
it if you are outside the intended network.

### Project commands

| Command | Purpose |
| --- | --- |
| `uv run zlabel` | Launch the GUI |
| `uv run zlabel-uic` | Regenerate Qt `uic`/`rcc` output and update translations |
| `uv run zlabel-translate` | Compile `i18n/zh_CN.qm` from `i18n/zh_CN.ts` |
| `uv run zlabel-build` | Build the Windows installer (cx_Freeze + Inno Setup) |

## Project Layout

```
zlabel/
├── main.py                 # application entry point
├── scripts.py              # console entry points (build / uic / translate)
├── widgets/
│   ├── mainwindow.py       # main window, actions, workflows
│   ├── canvas.py           # pyqtgraph annotation canvas
│   ├── graphic_objects.py  # Rectangle / Point / Polygon / instance bbox items
│   ├── dock_*.py           # Files / Info / Annos / Labels / Timeline docks
│   ├── dialog_*.py         # Settings / Export / Shortcut / About dialogs
│   ├── ui/                 # GENERATED Qt uic output — do not edit by hand
│   └── zworker.py          # background workers (image loading, SAM predict, ...)
├── utils/
│   ├── project.py          # pydantic data models (Label, Result, Annotation, ...)
│   ├── backend.py          # storage + inference backend abstraction
│   ├── api_helper.py       # HTTP client for the ZL annotation server
│   ├── exporters.py        # COCO / YOLO dataset export
│   ├── polygon_ops.py      # polygon merging / geometry helpers
│   └── wechat_ocr/         # ported WeChat OCR bindings (ruff/mypy-exempt)
├── models/
│   ├── predictor.py        # unified Predictor facade
│   ├── runner.py           # SAM / SAM2 / SAM3 MNN runners
│   ├── preprocess.py       # image preprocessing for MNN models
│   ├── postprocess.py      # mask upscaling / NMS / contour helpers
│   └── process_backend.py  # single-worker process pool (MNN runs off the UI thread)
└── resources/
    ├── ui/*.ui             # Qt Designer sources
    └── icons.qrc           # icon resource manifest
```

## Architecture Overview

- **Storage / inference are independent axes**, composed into `ZLabelBackend`:
  - Storage: `RemoteStorage` (ZL server API) or `LocalStorage` (files under `~/.zlabel/projects/`)
  - Inference: `RemoteInference` (HTTP `/predict`) or `LocalInference` (in-process MNN)
- **Data model**: all annotation data is pydantic models in `zlabel/utils/project.py`.
  Annotations serialize to JSON; `Project.save_json` deliberately excludes tasks
  (tasks are fetched from the storage backend).
- **Canvas**: `zlabel/widgets/canvas.py` is a pyqtgraph `PlotWidget`; annotations
  are `Rectangle`, `Point` and `Polygon` graphics items. Instance-level polygon
  bounding boxes are rendered as overlay `InstanceBBox` items.
- **Instances**: `Result.instance_id` groups parts of one object. IDs are
  per-frame (1..N) and the same number across frames denotes the same physical
  object. The instance timeline uses this convention for cross-frame navigation.
- **Local inference**: MNN holds the GIL, so inference runs in a child process
  via `zlabel/models/process_backend.py` to keep the GUI responsive.

## Common Development Tasks

### Adding or editing a Qt form

1. Edit the source under `resources/ui/*.ui` (or `resources/icons.qrc`).
2. Run `uv run zlabel-uic` to regenerate `zlabel/widgets/ui/*.py` / `icons_rc.py`.
3. Never hand-edit generated files.

New small widgets can also be written directly in code (see the inference group
in `dialog_settings.py`) to avoid regenerating all UI files.

### Local inference models

MNN model files are **not** committed and are **not** bundled in release builds.
They live in `data/models/mnn/` (gitignored) or in the directory configured in
Settings. SAM3 additionally needs `vocab.json` and `merges.txt` next to the models.

### Adding a new worker

Background work (image loading, SAM prediction, OCR) should be implemented as a
`QRunnable` in `zlabel/widgets/zworker.py` and started with
`self.threadpool.start(worker)` so the UI thread is never blocked.

## Testing

```bash
# run everything (real-model tests skip when MNN models are absent)
uv run pytest

# skip tests that require data/models/mnn
uv run pytest -m "not models"

# GUI tests only (offscreen, no display required)
uv run pytest tests/gui/

# coverage
uv run pytest --cov=zlabel
```

GUI fixtures live in `tests/gui/conftest.py`:

- `main_window` — full `MainWindow` with local backend, no network
- `populated_project` — main window with one task + annotation + cached image
- `canvas_view` — helpers to drive canvas clicks / drags in image coordinates

## Lint & Format

```bash
uv run ruff check .
uv run ruff format .
```

Line length is 120. Run both before opening a pull request.

## Building the Windows Installer

```bash
uv run zlabel-build
```

This runs cx_Freeze (`setup.py build_exe`) and, on Windows, Inno Setup (`ISCC`).
The installer is written to `dist/`.

Notes:

- MNN model files are intentionally **not** bundled; users must provide them.
- The WeChat OCR engine is bundled only when `data/WeChat-Local-OCR-Serve/wxocr`
  exists at build time.
- `build/` and `dist/` are gitignored; do not commit build artifacts.

## Contribution Workflow

1. Fork the repository and create a feature branch.
2. Make focused changes with tests.
3. Run `uv run ruff check .` and `uv run pytest -m "not models"`.
4. Open a pull request with a clear description.

### Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(canvas): add instance-level polygon bbox
fix(labels): sync default instance status radio
perf(mainwindow): batch instance-tree refresh on merge
```

Keep the subject under 72 characters and explain the *why* in the body when it is
not obvious.

## Translations

UI strings are translated with Qt Linguist:

- Source: `i18n/zh_CN.ts`
- Compiled: `i18n/zh_CN.qm`
- Regenerate UI + update translations: `uv run zlabel-uic`
- Compile translations only: `uv run zlabel-translate`

## License

By contributing you agree that your contributions are licensed under the same
Apache-2.0 license as the project.
