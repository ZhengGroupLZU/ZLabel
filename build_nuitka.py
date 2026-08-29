"""Description: build script using Nuitka
Author: Rainyl
LastEditTime: 2022-08-04 17:33:48
"""

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

import tomli
from py7zr import FILTER_LZMA2, PRESET_DEFAULT, SevenZipFile
from rich import print

ROOT = Path(__file__).resolve().parent

with open(ROOT / "pyproject.toml", "rb") as f:
    project = tomli.load(f)
__version__ = project["project"]["version"]
__proj_name = project["project"]["name"]
__app_name = "ZLabel"

CPUS: int = os.cpu_count() or 1


def platform_tag() -> str:
    """Return a cx-Freeze style platform tag, e.g. windows-amd64."""
    return f"{platform.system().lower()}-{platform.machine().lower()}"


def output_base(version: str) -> str:
    """Same base name used by the cx-Freeze installer output."""
    return f"{__app_name}-{platform_tag()}-{version}"


def get_build_root(enable_debug: bool) -> str:
    return "build_debug" if enable_debug else "build"


def nuitka_dist_dir(build_root: str) -> Path:
    return ROOT / build_root / f"{__proj_name.lower()}.dist"


def run_nuitka(version: str, build_root: str, enable_debug: bool, jobs: int) -> None:
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--recompile-c-only",
        "--clang",
        f"--output-dir={build_root}",
        "--enable-console" if enable_debug else "--disable-console",
        f"--jobs={jobs}",
        "--file-description=ZLabel",
        "--company-name=ZhengGroup",
        f"--product-version={version}",
        "--product-name=ZLabel",
        "--plugin-enable=pyside6",
        # Align with the cx-Freeze build in setup.py.
        "--windows-icon-from-ico=resources/icons/logo.ico",
        "--include-data-dir=i18n=i18n",
        "./zlabel.py",
    ]
    if enable_debug:
        cmd.append("--debug")

    print(f"[yellow]Running Nuitka (version {version}, build root {build_root})...[/yellow]")
    subprocess.run(cmd, cwd=ROOT, check=True)


def publish_to_7z(dist: Path, version: str) -> Path:
    """Create a portable/green 7z archive from the Nuitka dist folder."""
    out = ROOT / "dist" / f"{output_base(version)}-green.7z"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    print(f"Compressing {dist} -> {out}")
    filters = [{"id": FILTER_LZMA2, "preset": PRESET_DEFAULT}]
    with SevenZipFile(str(out), "w", filters=filters, mp=True) as archive:
        archive.writeall(str(dist), arcname=__app_name)
    return out


def prepare_iss(dist: Path, version: str) -> Path:
    """Generate an Inno Setup script for the Nuitka dist layout."""
    template = ROOT / "setup_nuitka.iss"
    iss = template.read_text(encoding="utf-8")
    iss = re.sub(r"#define MyAppVersion .*", f'#define MyAppVersion "{version}"', iss, count=1)
    iss = re.sub(
        r"#define MyAppSrcDir .*",
        f'#define MyAppSrcDir "{dist.resolve().as_posix()}"',
        iss,
        count=1,
    )
    iss = re.sub(
        r"OutputBaseFilename=.*",
        f"OutputBaseFilename={output_base(version)}-installer",
        iss,
        count=1,
    )

    generated = ROOT / "build" / "setup_nuitka.generated.iss"
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text(iss, encoding="utf-8")
    return generated


def run_iscc(iss_path: Path, version: str) -> Path:
    """Build the Inno Setup installer and return the expected output path."""
    inno_bin = shutil.which("ISCC") or "ISCC"
    out_dir = ROOT / "dist"
    out_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            inno_bin,
            "/Q",
            f"/O{out_dir}",
            f"/F{output_base(version)}-installer",
            str(iss_path),
        ],
        cwd=ROOT,
        check=True,
    )
    return out_dir / f"{output_base(version)}-installer.exe"


def main(
    version: str | None = None,
    enable_debug: bool = False,
    jobs: int = CPUS,
) -> int:
    version = version or __version__
    build_root = get_build_root(enable_debug)

    run_nuitka(version, build_root, enable_debug, jobs)

    dist = nuitka_dist_dir(build_root)
    if not dist.exists():
        raise FileNotFoundError(f"Nuitka dist not found: {dist}")

    green = publish_to_7z(dist, version)
    print(f"[green]Green package: {green}[/green]")

    if sys.platform == "win32" and shutil.which("ISCC"):
        iss = prepare_iss(dist, version)
        installer = run_iscc(iss, version)
        print(f"[green]Installer: {installer}[/green]")
    else:
        print("Inno Setup not available / non-Windows: installer skipped")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", dest="version", type=str)
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="enable build for debug",
    )
    parser.add_argument("-j", dest="jobs", type=int, default=CPUS)
    args = parser.parse_args()

    raise SystemExit(main(version=args.version, enable_debug=args.debug, jobs=args.jobs))
