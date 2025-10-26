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
__version__ = project["tool"]["poetry"]["version"]
__proj_name = project["tool"]["poetry"]["name"]


CPUS: int = os.cpu_count()  # type: ignore


def convert_png_ico(path: str):
    path_new = path.replace(".png", ".ico")
    img = Image.open(path)
    img.save(path_new)
    print(f"converted {path} to {path_new}")


def publish_to_7z(build_dir: str, version: str):
    print("Compressing...")
    working_dir = Path(f"{build_dir}/CeleryMathGui.dist/")
    exclude_pattern = re.compile(r"qtwebengine_devtools_resources")
    for file in working_dir.glob("**/*"):
        if exclude_pattern.search(str(file)):
            os.remove(file)
            print(f"Pattern mached, remove {file}")

    save_7z_name = f"{build_dir}/CeleryMath-v{version}-Windows_x64.7z"
    filters = [{"id": FILTER_LZMA2, "preset": PRESET_DEFAULT}]
    with SevenZipFile(save_7z_name, "w", filters=filters, mp=True) as archive:
        archive.writeall(working_dir, arcname="CeleryMath")
    print(f"Publish successfully, saved to {save_7z_name}")


def main(version: str, enable_debug: bool = False, jobs: int = CPUS):
    icon_png = "zlabel/resources/icons/zlabel.png"
    convert_png_ico(icon_png)

    std_out = "--force-stdout-spec=%PROGRAM_BASE%.out.txt "
    std_err = "--force-stderr-spec=%PROGRAM_BASE%.err.txt "
    console = "--disable-console "
    build_dir = "build"
    debug = ""
    if enable_debug:
        console = "--enable-console "
        build_dir = "build_debug "
        std_out = ""
        std_err = ""
        # debug = "--debug --experimental=allow-c-warnings"
    cmd = (
        "nuitka-run "
        "--clang "
        # "--mingw64 "
        "--recompile-c-only "
        "--standalone "
        f"{debug} "
        f"--output-dir={build_dir} "
        # "--follow-imports "
        f"{console} "
        f"{std_out} "
        f"{std_err} "
        # "--warn-implicit-exceptions "
        # "--warn-unusual-code "
        f"--jobs={jobs} "
        "--file-description=ZLabel "
        "--company-name=rainyl@Zheng.group "
        f"--product-version={version} "
        f"""--product-name="ZLabel_v{version}" """
        # """--copyright="Copyright © 2023-. ZhengGroup All Rights Reserved." """
        # "--show-progress "
        # "--show-memory  "
        "--plugin-enable=pyside6 "
        # "--plugin-enable=matplotlib "
        # "--plugin-enable=multiprocessing "
        # "--plugin-enable=upx "
        # "--user-package-configuration-file=cm.nuitka-package.config.yml "
        "--windows-icon-from-ico=zlabel/resources/icons/zlabel.ico "
        "./zlabel.py "
        # "./test.py "
    )

    os.system(cmd)

    # make directories and copy necessary files
    # mkdirs = [
    #     Path(f"{build_dir}/CeleryMathGui.dist/conf"),
    # ]
    # for path in mkdirs:
    #     if not path.exists():
    #         print(f"Making directory: {path}")
    #         path.mkdir(parents=True)

    # # compress using 7z
    # publish_to_7z(build_dir, version)


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
