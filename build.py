"""
Description: build script, using nuitka
Author: Rainyl
LastEditTime: 2022-08-04 17:33:48
"""
import os
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
    print("Compressing...")
    working_dir = Path(f"{build_dir}/{__proj_name__}/")
    exclude_pattern = re.compile(r"qtwebengine_devtools_resources")
    for file in working_dir.glob("**/*"):
        if exclude_pattern.search(str(file)):
            os.remove(file)
            print(f"Pattern mached, remove {file}")

    save_7z_name = f"{build_dir}/{__proj_name__}-v{version}-Windows_x64.7z"
    filters = [{"id": FILTER_LZMA2, "preset": PRESET_DEFAULT}]
    with SevenZipFile(save_7z_name, "w", filters=filters, mp=True) as archive:
        archive.writeall(working_dir, arcname=f"{__proj_name__}")
    print(f"Publish successfully, saved to {save_7z_name}")


def main(version: str, enable_debug: bool = False, jobs: int = CPUS):
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

    # # compress using 7z
    if not enable_debug:
        publish_to_7z(dist_dir, version)


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
    args = parser.parse_args()
    # if provide version manully, use the provided version number
    args.version = args.version or __version__

    main(version=args.version, enable_debug=args.debug, jobs=args.jobs)
