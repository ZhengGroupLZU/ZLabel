import os
import platform
import re
import sys
from pathlib import Path

from cx_Freeze import Executable, setup

with open("pyproject.toml") as f:
    version = re.search(r"version = \"(.*)\"", f.read()).group(1)  # type: ignore

directory_table = [
    ("ZLabel", "TARGETDIR", "."),
    # ("MyProgramMenu", "ProgramMenuFolder", "MYPROG~1|My Program"),
]

msi_data = {
    "Directory": directory_table,
    "ProgId": [
        ("Prog.Id", None, None, "ZLabel", "IconId", None),
    ],
    "Icon": [
        ("IconId", "resources/icons/logo.ico"),
    ],
}

bdist_msi_options = {
    "add_to_path": True,
    "data": msi_data,
    # "environment_variables": [("E_MYAPP_VAR", "=-*MYAPP_VAR", "1", "TARGETDIR")],
    "upgrade_code": "{C7D21D8B-AE3B-469A-8DFC-AC6CCD23F5F1}",
}

uname = platform.uname()
output_dir = f"build/exe.{uname.system.lower()}-{uname.machine.lower()}"

# onnx model files in data/ are intentionally NOT bundled.
include_files = [["i18n/zh_CN.qm", "i18n/zh_CN.qm"]]
# WeChat OCR engine: bundle only when the wxocr component is present in the tree.
_wxocr_src = "data/WeChat-Local-OCR-Serve/wxocr"
if os.path.isdir(_wxocr_src):
    include_files.append([_wxocr_src, "data/WeChat-Local-OCR-Serve/wxocr"])

includes = [
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    # pyqtgraph.parametertree.interactive imports pydoc at runtime; cx_Freeze
    # does not detect it automatically.
    "pydoc",
]
try:
    import cv2  # noqa: F401

    includes += ["cv2"]
except ImportError:
    print("Warning: cv2 not installed, local inference disabled in this build")

try:
    import MNN  # noqa: F401

    includes += ["MNN"]
except ImportError:
    print("Warning: MNN not installed, local inference disabled in this build")

build_exe_options = {
    "build_exe": output_dir,
    "excludes": [
        "tkinter",
        "unittest",
        "pytest",
        "imageio",
        "nuitka",
        "ordered-set",
        "zstandard",
        "py7zr",
        "tqdm",
        "typed-argument-parser",
        # Nothing in ZLabel (or pyqtgraph) imports QtNetwork: HTTP goes through
        # requests. Excluding it also stops the qt_qtnetwork hook from copying
        # the tls/ and networkinformation/ plugin dirs (~2.7 MB saved).
        "PySide6.QtNetwork",
        # Optional urllib3 extra, only imported under try/except ImportError.
        "brotli",
        # Unused stdlib modules pulled in by cx_Freeze's default scanning.
        "xmlrpc",
        "wmi",
    ],
    "includes": includes,
    "bin_excludes": [
        "QtTest.pyd",
        "Qt6Test.dll",
        "Qt6Quick.dll",
        "Qt6QmlWorkerScript.dll",
        "Qt6QmlModels.dll",
        "Qt6QmlMeta.dll",
        "Qt6Qml.dll",
        "Qt6Pdf.dll",
        "opencv_videoio_ffmpeg500_64.dll",
        # Qt modules unused by ZLabel (qt_qtcore hook copies every *.dll in the
        # PySide6 dir, so they must be excluded explicitly).
        "Qt6Network.dll",
        "Qt6VirtualKeyboard.dll",
        "qtvirtualkeyboardplugin.dll",
        "qtuiotouchplugin.dll",
        # Desktop app only needs the qwindows platform plugin.
        "qdirect2d.dll",
        "qminimal.dll",
        "qoffscreen.dll",
        # Image formats never opened (app loads png/jpg/svg/ico only).
        "qpdf.dll",
        "qwebp.dll",
        "qtiff.dll",
        "qgif.dll",
        "qicns.dll",
        "qtga.dll",
        "qwbmp.dll",
        # Belt & braces: exclude the compiled brotli binary too.
        "_brotli.cp312-win_amd64.pyd",
    ],
    "include_msvcr": False,
    "optimize": 2,
    "zip_include_packages": ["encodings", "PySide6", "shiboken6", "pydantic"],
    "include_files": include_files,
}

executables = [
    Executable(
        "zlabel.py",
        base="gui",
        copyright="Copyright © 2025. ZhengGroup All Rights Reserved.",
        icon="resources/icons/logo.ico",
        shortcut_name="ZLabel",
        # shortcut_dir="MyProgramMenu",
    )
]


def _prune_build(build_dir: str) -> None:
    """Remove binaries/data cx_Freeze cannot exclude (version-tagged files,
    Qt .qm translations). Called before ISCC so the installer stays small.
    """
    build_dir = Path(build_dir)
    if not build_dir.is_dir():
        print(f"_prune_build: {build_dir} not found, skip")
        return

    # PIL codecs never used by ZLabel (Image.init() imports each plugin in a
    # try/except, so missing ones are skipped silently). The app only opens
    # png/jpg via Image.resize/crop/thumbnail/tobytes. Saves ~10 MB.
    pil_dir = build_dir / "lib" / "PIL"
    if pil_dir.is_dir():
        for pattern in (
            "_avif*.pyd",
            "_imagingft*.pyd",
            "_imagingcms*.pyd",
            "_imagingmath*.pyd",
            "_imagingmorph*.pyd",
            "_imagingtk*.pyd",
            "_webp*.pyd",
        ):
            for p in pil_dir.glob(pattern):
                p.unlink()
                print(f"_prune_build: removed {p}")

    # Qt built-in translations: keep zh_CN/zh_TW/en only (~6 MB saved). The
    # app's own strings come from i18n/zh_CN.qm (include_files), untouched.
    translations = build_dir / "lib" / "PySide6" / "translations"
    if translations.is_dir():
        keep = {
            "qt_zh_CN.qm",
            "qt_zh_TW.qm",
            "qt_en.qm",
            "qtbase_zh_CN.qm",
            "qtbase_zh_TW.qm",
            "qtbase_en.qm",
        }
        for p in translations.glob("*.qm"):
            if p.name not in keep:
                p.unlink()
                print(f"_prune_build: removed {p}")

    # Qt modules ZLabel never imports (WebEngine, Quick/Qml, 3D, Designer,
    # Help/Pdf, Positioning, Lottie, Sql, PrintSupport, DBus, UiTools, ...).
    qt_dir = build_dir / "lib" / "PySide6"
    if qt_dir.is_dir():
        unused_prefixes = (
            "Qt6WebEngine",
            "Qt63D",
            "Qt6Quick",
            "Qt6Qml",
            "Qt6Designer",
            "Qt6Help",
            "Qt6Pdf",
            "Qt6Positioning",
            "Qt6Lottie",
            "Qt6Sql",
            "Qt6PrintSupport",
            "Qt6DBus",
            "Qt6UiTools",
            "Qt6StateMachine",
            "Qt6Test",
            "Qt6Labs",
            "Qt6VirtualKeyboard",
            "Qt6WebChannel",
            "Qt6Bluetooth",
            "Qt6CanvasPainter",
            "Qt6Charts",
            "Qt6DataVisualization",
            "Qt6Graphs",
            "Qt6HttpServer",
            "Qt6Location",
            "Qt6Multimedia",
            "Qt6NetworkAuth",
            "Qt6Nfc",
            "Qt6RemoteObjects",
            "Qt6Scxml",
            "Qt6Sensors",
            "Qt6SerialBus",
            "Qt6SerialPort",
            "Qt6ShaderTools",
            "Qt6SpatialAudio",
            "Qt6TextToSpeech",
            "Qt6WebSockets",
            "Qt6WebView",
        )
        for p in qt_dir.glob("Qt6*.dll"):
            if p.name.startswith(unused_prefixes):
                p.unlink()
                print(f"_prune_build: removed {p}")

        # QML runtime + plugin dirs that ship with the Qt modules above.
        qml_dir = qt_dir / "qml"
        if qml_dir.is_dir():
            import shutil

            shutil.rmtree(qml_dir)
            print(f"_prune_build: removed {qml_dir}")
        # ffmpeg DLLs shipped with QtMultimedia (unused by ZLabel)
        for ffmpeg_dll in ("avcodec-61.dll", "avformat-61.dll", "avutil-59.dll", "swresample-5.dll", "swscale-8.dll"):
            dll = qt_dir / ffmpeg_dll
            if dll.exists():
                dll.unlink()
                print(f"_prune_build: removed {dll}")

        for plugin_dir in (
            "designer",
            "qmltooling",
            "qmllint",
            "sqldrivers",
            "networkinformation",
            "tls",
            "multimedia",
        ):
            d = qt_dir / "plugins" / plugin_dir
            if d.is_dir():
                import shutil

                shutil.rmtree(d)
                print(f"_prune_build: removed {d}")


setup(
    name="zlabel",
    version=version,
    description="ZLabel",
    executables=executables,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
)

# Trim files cx_Freeze cannot exclude before ISCC packages the installer.
_prune_build(output_dir)

with open("setup.iss", "r") as f:
    iss = f.read()
iss = re.sub(r"#define MyAppVersion .*", f'#define MyAppVersion "{version}"', iss)
iss = re.sub(r"#define MyAppSrcDir .*", f'#define MyAppSrcDir "{output_dir}"', iss)
with open("setup.iss", "w") as f:
    f.write(iss)

if sys.platform == "win32":
    inno_bin = "ISCC"
    os.system(
        " ".join([
            f"{inno_bin}",
            "/Q",
            '/O"dist"',
            f'/F"ZLabel-{uname.system.lower()}-{uname.machine.lower()}-{version}-setup"',
            "setup.iss",
        ]),
    )
