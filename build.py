"""
Description: build script, using nuitka
Author: Rainyl
LastEditTime: 2025-11-13
"""

import os
import platform
import re
from argparse import ArgumentParser
from pathlib import Path

import tomli
from PIL import Image
from py7zr import FILTER_LZMA2, PRESET_DEFAULT, SevenZipFile
from rich import print

with open(Path(__file__).parent / "pyproject.toml", "rb") as f:
    project = tomli.load(f)
__version__ = project["project"]["version"]
__proj_name__ = project["project"]["name"]


CPUS: int = os.cpu_count()  # type: ignore


def convert_png_ico(path: str):
    path_new = path.replace(".png", ".ico")
    img = Image.open(path)
    img.save(path_new)
    print(f"converted {path} to {path_new}")


def publish_to_7z(build_dir: str, version: str):
    print(f"Compressing {build_dir}...")
    uname = platform.uname()
    os_name = uname.system
    os_arch = uname.machine
    if os_name == "Darwin":
        # archived app can run due to no signature, skip this for now
        return
    os_ext = "app" if os_name == "Darwin" else "dist"
    arcname = f"{__proj_name__}.app" if os_name == "Darwin" else __proj_name__
    extra_files = [
        "build/zlabel.conf",
        "build/projects",
    ]

    working_dir = Path(f"{build_dir}/{__proj_name__}.{os_ext}")
    exclude_pattern = re.compile(r"qtwebengine_devtools_resources")
    for file in working_dir.glob("**/*"):
        if exclude_pattern.search(str(file)):
            os.remove(file)
            print(f"Pattern mached, remove {file}")

    save_7z_name = f"{build_dir}/{__proj_name__}-v{version}-{os_name}-{os_arch}.7z"
    filters = [{"id": FILTER_LZMA2, "preset": PRESET_DEFAULT}]
    with SevenZipFile(save_7z_name, "w", filters=filters, mp=True) as archive:
        archive.writeall(working_dir, arcname=arcname)
        for extra_file in extra_files:
            if os.path.exists(extra_file):
                if os_name == "Darwin":
                    arcname = f"{extra_file.split('/')[-1]}"
                else:
                    arcname = f"{arcname}/{extra_file.split('/')[-1]}"
                archive.write(extra_file, arcname=arcname)
            else:
                print(f"Warning: {extra_file} not found, skip")
    print(f"Publish successfully, saved to {save_7z_name}")


def build_with_pyinstaller(version: str, enable_debug: bool = False, jobs: int = CPUS):
    icon_png = "zlabel/resources/icons/zlabel.png"
    convert_png_ico(icon_png)

    std_out = "--force-stdout-spec=%PROGRAM_BASE%.out.txt "
    std_err = "--force-stderr-spec=%PROGRAM_BASE%.err.txt "
    build_dir = "build/release "
    dist_dir = "dist/release"
    spec = "zlabel_release.spec"
    if enable_debug:
        build_dir = "build/debug "
        dist_dir = "dist/debug"
        std_out = ""
        std_err = ""
        spec = "zlabel_debug.spec"
    cmd = (
        "pyinstaller "
        "--clean "
        # "--disable-windowed-traceback "
        f"--workpath {build_dir} "
        f"--distpath {dist_dir} "
        "-y "
        f"{spec} "
    )

    os.system(cmd)

    # make directories and copy necessary files
    mkdirs: list[Path] = []
    for path in mkdirs:
        if not path.exists():
            print(f"Making directory: {path}")
            path.mkdir(parents=True)

    # compress using 7z
    if not enable_debug:
        publish_to_7z(dist_dir, version)


def build_with_nuitka(version: str, enable_debug: bool = False, jobs: int = CPUS):
    print("Building with Nuitka...")

    nuitka_build_dir = "build/debug" if enable_debug else "build/release"
    icon_png = "zlabel/resources/icons/zlabel.png"
    # convert_png_ico(icon_png)

    # Base Nuitka command based on pyproject.toml configuration
    cmd_parts = [
        "nuitka",
        "--standalone",
        "--enable-plugin=pyside6",
        "--include-qt-plugins=sensible",
        "--macos-create-app ",
        f"--macos-app-icon={icon_png}",
        f"--windows-icon-from-ico={icon_png}",
        f"--macos-app-version={version}",
        "--company-name=ZhengGroup",
        f"--product-name={__proj_name__}",
        f"--file-version={version}",
        f"--product-version={version}",
        '--file-description="ZhengGroup ZLabel"',
        '--copyright="Copyright © 2025 ZhengGroup. All rights reserved."',
        '--trademarks="ZhengGroup ZLabel."',
        "--include-data-files=build/zlabel.conf=zlabel.conf",
        "--include-data-dir=build/projects=projects",
        f"-j {jobs}",
    ]

    if enable_debug:
        # Debug mode options
        cmd_parts.extend([
            "--debug",
            "--no-deployment",
            "--windows-console-mode=force",
            f"--output-dir={nuitka_build_dir}",
        ])
    else:
        # Release mode options
        cmd_parts.extend([
            "--deployment",
            "--force-stdout-spec={PROGRAM_BASE}.out.txt",
            "--force-stderr-spec={PROGRAM_BASE}.err.txt",
            "--windows-console-mode=disable",
            f"--output-dir={nuitka_build_dir}",
        ])

    # Add the main script
    cmd_parts.append("zlabel.py")

    # Execute the command
    cmd = " ".join(cmd_parts)
    print(f"Executing: {cmd}")
    code = os.system(cmd)
    if code != 0:
        print(f"Error: {code}")
        return

    # For release builds, compress the result
    if not enable_debug:
        src_dir = f"{nuitka_build_dir}"
        publish_to_7z(src_dir, version)


def main(version: str, enable_debug: bool = False, jobs: int = CPUS, use_pyinstaller: bool = False):
    if use_pyinstaller:
        build_with_pyinstaller(version, enable_debug, jobs)
    else:
        build_with_nuitka(version, enable_debug, jobs)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-v", dest="version", type=str)
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="enable build for debug",
    )
    parser.add_argument("-j", dest="jobs", type=int, default=CPUS)
    parser.add_argument(
        "--pyinstaller",
        dest="use_pyinstaller",
        action="store_true",
        help="use pyinstaller instead of nuitka (default is nuitka)",
    )
    args = parser.parse_args()
    # if provide version manully, use the provided version number
    args.version = args.version or __version__

    main(version=args.version, enable_debug=args.debug, jobs=args.jobs, use_pyinstaller=args.use_pyinstaller)
