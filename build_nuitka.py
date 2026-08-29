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

# Modules that are imported by PIL/MNN/Qt packages but not used by ZLabel.
# Keeping them out of the Nuitka compile shrinks zlabel.exe and the dist.
NOFOLLOW_MODULES = [
    # PIL image formats ZLabel never opens (only png/jpg/bmp/ico are used).
    "PIL.AvifImagePlugin",
    "PIL.BlpImagePlugin",
    "PIL.BufrStubImagePlugin",
    "PIL.CurImagePlugin",
    "PIL.DcxImagePlugin",
    "PIL.DdsImagePlugin",
    "PIL.EpsImagePlugin",
    "PIL.FitsImagePlugin",
    "PIL.FliImagePlugin",
    "PIL.FpxImagePlugin",
    "PIL.FtexImagePlugin",
    "PIL.GbrImagePlugin",
    "PIL.GifImagePlugin",
    "PIL.GribStubImagePlugin",
    "PIL.Hdf5StubImagePlugin",
    "PIL.IcnsImagePlugin",
    "PIL.ImImagePlugin",
    "PIL.ImtImagePlugin",
    "PIL.IptcImagePlugin",
    "PIL.Jpeg2KImagePlugin",
    "PIL.McIdasImagePlugin",
    "PIL.MicImagePlugin",
    "PIL.MpegImagePlugin",
    "PIL.MpoImagePlugin",
    "PIL.MspImagePlugin",
    "PIL.PalmImagePlugin",
    "PIL.PcdImagePlugin",
    "PIL.PcxImagePlugin",
    "PIL.PdfImagePlugin",
    "PIL.PixarImagePlugin",
    "PIL.PpmImagePlugin",
    "PIL.PsdImagePlugin",
    "PIL.QoiImagePlugin",
    "PIL.SgiImagePlugin",
    "PIL.SpiderImagePlugin",
    "PIL.SunImagePlugin",
    "PIL.TgaImagePlugin",
    "PIL.TiffImagePlugin",
    "PIL.WebPImagePlugin",
    "PIL.WmfImagePlugin",
    "PIL.XVThumbImagePlugin",
    "PIL.XbmImagePlugin",
    "PIL.XpmImagePlugin",
    "PIL.ImageCms",
    "PIL.ImageMath",
    "PIL.ImageShow",
    "PIL.ImageWin",
    "PIL.ImageQt",
    # MNN submodules not used by ZLabel (we only use MNN.expr + MNN.nn).
    "MNN.audio",
    "MNN.llm",
    "MNN.optim",
    "MNN.data",
    "MNN.cv",
    # Qt modules not used by ZLabel (requests uses Python sockets).
    "PySide6.QtNetwork",
    "PySide6.QtTest",
    "PySide6.QtUiTools",
    "PySide6.QtXml",
    "PySide6.QtSvg",
    # Pygments/rich are not used by ZLabel at runtime, but Nuitka currently
    # compiles the entire pygments lexer/style tree into the exe.
    "pygments",
    "rich",
    # Optional HTTP compression/transport extras.
    "brotli",
    "backports.zstd",
    "urllib3.contrib.pyopenssl",
    "urllib3.contrib.socks",
    "urllib3.http2.connection",
    # Pydantic v1 compatibility, mypy/deprecated/json/parse/schema/type_adapter
    # and other modules not imported by ZLabel's BaseModel usage.
    "pydantic.v1",
    "pydantic.mypy",
    "pydantic.deprecated",
    "pydantic.json",
    "pydantic.parse",
    "pydantic.schema",
    "pydantic.type_adapter",
    "pydantic.dataclasses",
    "pydantic.class_validators",
    "pydantic.color",
    "pydantic.env_settings",
    "pydantic.error_wrappers",
    "pydantic.networks",
    "pydantic.root_model",
    "pydantic.validators",
    "pydantic.datetime_parse",
    "pydantic.alias_generators",
    "pydantic.typing",
    "pydantic.utils",
    "pydantic._internal._git",
    # OpenCV optional submodules not used by ZLabel.
    "cv2.aruco",
    "cv2.barcode",
    "cv2.ccm",
    "cv2.cuda",
    "cv2.data",
    "cv2.detail",
    "cv2.dnn",
    "cv2.fisheye",
    "cv2.flann",
    "cv2.instr",
    "cv2.ipp",
    "cv2.mcc",
    "cv2.misc",
    "cv2.ocl",
    "cv2.ogl",
    "cv2.parallel",
    "cv2.samples",
    "cv2.segmentation",
    "cv2.videoio_registry",
    # Optional PIL helper modules only needed by excluded image formats.
    "PIL.TiffTags",
    "PIL.ExifTags",
    "PIL.GimpGradientFile",
    "PIL.GimpPaletteFile",
    "PIL.PaletteFile",
    # Optional numpy submodules not used by ZLabel (no fft/polynomial/ma).
    "numpy.fft",
    "numpy.polynomial",
    "numpy.ma",
    "numpy.matlib",
    "numpy.char",
    "numpy.ctypeslib",
    "numpy.rec",
    "numpy.strings",
    # pyqtgraph optional facilities not used by ZLabel.
    "pyqtgraph.console",
    "pyqtgraph.exporters",
    "pyqtgraph.algorithms",
    "pyqtgraph.exceptionHandling",
    "pyqtgraph.widgets.MatplotlibWidget",
    "pyqtgraph.GraphicsScene.exportDialog",
]

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
        # "--clang",
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
    ]
    for module in NOFOLLOW_MODULES:
        cmd.append(f"--nofollow-import-to={module}")
    cmd.append("./zlabel.py")
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


def prune_nuitka_dist(dist: Path) -> None:
    """Remove unused files from the Nuitka standalone dist.

    These files are not needed by ZLabel at runtime but are copied by Nuitka
    because they belong to the installed packages.  Removing them before the
    7z/installer step keeps the portable and installed builds smaller.
    """

    def remove(rel: str) -> None:
        target = dist / rel
        if target.is_file() or target.is_symlink():
            target.unlink()
            print(f"  removed {rel}")

    def rmtree(rel: str) -> None:
        target = dist / rel
        if target.is_dir():
            import shutil as _shutil

            _shutil.rmtree(target)
            print(f"  removed dir {rel}")

    print("Pruning Nuitka dist...")

    # OpenCV: image processing only, no video I/O.
    remove("cv2/opencv_videoio_ffmpeg500_64.dll")

    # PIL optional codecs.
    for rel in (
        "PIL/_avif.pyd",
        "PIL/_webp.pyd",
        "PIL/_imagingcms.pyd",
        "PIL/_imagingmath.pyd",
    ):
        remove(rel)

    # Qt modules unused by ZLabel.
    for rel in (
        "PySide6/QtNetwork.pyd",
        "PySide6/QtTest.pyd",
        "PySide6/QtUiTools.pyd",
        "PySide6/QtXml.pyd",
        "PySide6/QtSvg.pyd",
        "qt6network.dll",
        "qt6test.dll",
        "qt6uitools.dll",
        "qt6xml.dll",
        "qt6svg.dll",
        "qt6pdf.dll",
    ):
        remove(rel)

    # Qt plugins: keep qjpeg/qico/qwindows only.
    keep_plugins = {"qjpeg.dll", "qico.dll", "qwindows.dll"}
    plugins = dist / "PySide6" / "qt-plugins"
    if plugins.is_dir():
        for sub in ("imageformats", "platforms", "styles", "tls", "iconengines"):
            d = plugins / sub
            if d.is_dir():
                for f in d.glob("*"):
                    if f.is_file() and f.name not in keep_plugins:
                        f.unlink()
                        print(f"  removed {sub}/{f.name}")
                if not any(d.iterdir()):
                    d.rmdir()
                    print(f"  removed dir {sub}")

    # Optional HTTP compression backends.
    remove("_brotli.pyd")
    rmtree("backports/zstd")

    # Translation sources are not needed at runtime; keep zh_CN.qm.
    remove("i18n/en.ts")
    remove("i18n/zh_CN.ts")


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
    icon = ROOT / "resources" / "icons" / "logo.ico"
    iss = re.sub(
        r"SetupIconFile=.*",
        lambda _match: f"SetupIconFile={icon.resolve()}",
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

    prune_nuitka_dist(dist)

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
