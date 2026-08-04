import os
import platform
import re
import sys

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

includes = [
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
]
try:
    import cv2  # noqa: F401
    import onnxruntime  # noqa: F401

    includes += ["onnxruntime", "cv2"]
except ImportError:
    print("Warning: onnxruntime/cv2 not installed, local inference disabled in this build")

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
