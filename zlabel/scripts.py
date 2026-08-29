"""Console entry points declared in `[project.scripts]` / `[project.gui-scripts]`.

These replace the former Poe tasks so project commands run via `uv run <name>`
(e.g. `uv run zlabel`, `uv run zlabel-translate`).
"""

import subprocess
import sys


def _run(cmd: list[str]) -> None:
    raise SystemExit(subprocess.call(cmd))


def build() -> None:
    """Build the Windows installer with cx_Freeze + Inno Setup."""
    _run([sys.executable, "setup.py", "build_exe"])


def build_nuitka() -> None:
    """Build the portable 7z + Inno Setup installer with Nuitka."""
    _run([sys.executable, "build_nuitka.py"])


def uic_rcc() -> None:
    """Regenerate Qt generated code (uic/rcc) and update translations."""
    _run([sys.executable, "uic_rcc.py"])


def translate() -> None:
    """Compile the zh_CN translation file."""
    _run(["pyside6-lrelease", "i18n/zh_CN.ts", "-qm", "i18n/zh_CN.qm"])
