import argparse
import os
import warnings
from pathlib import Path

from tqdm.rich import tqdm  # type: ignore
from tqdm.std import TqdmExperimentalWarning

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)


class SrcDst:
    def __init__(self, src: str, dst: str) -> None:
        self.src = src
        self.dst = dst

    def __repr__(self) -> str:
        return f"SrcDst({self.src}->{self.dst})"


def to_src_dst(s: str):
    ss = s.split(",")
    assert len(ss) == 2
    return SrcDst(ss[0], ss[1])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Regenerate Qt uic/rcc output and update translations")
    parser.add_argument(
        "--pyside",
        choices=["pyside6", "pyside2"],
        default="pyside6",
        help="PySide binding to use (default: pyside6)",
    )
    parser.add_argument(
        "--uic_path",
        nargs="+",
        default=[],
        metavar="SRC,DST",
        help="uic source/destination pairs, e.g. resources/ui/mainwindow.ui,zlabel/widgets/ui/mainwindow.py",
    )
    parser.add_argument(
        "--rcc_path",
        nargs="+",
        default=[],
        metavar="SRC,DST",
        help="rcc source/destination pairs, e.g. resources/icons.qrc,icons_rc.py",
    )
    return parser


def main(args: argparse.Namespace):
    uics = [to_src_dst(p) for p in args.uic_path]
    rccs = [to_src_dst(p) for p in args.rcc_path]
    for uic in tqdm(uics):
        os.system(f"{args.pyside}-uic -o {uic.dst} {uic.src}")
    for rcc in tqdm(rccs):
        os.system(f"{args.pyside}-rcc -o {rcc.dst} {rcc.src}")
    translates = " ".join([uic.src for uic in uics])
    os.system(f"{args.pyside}-lupdate  {translates} -ts i18n/zh_CN.ts")
    os.system(f"{args.pyside}-lupdate  {translates} -ts i18n/en.ts")


if __name__ == "__main__":
    parser = build_parser()
    ui_dir = Path("resources/ui")
    ui_dst = Path("zlabel/widgets/ui")
    # ui_files = list(ui_dir.glob("*.ui"))
    ui_files = [
        ui_dir / "mainwindow.ui",
        ui_dir / "dialog_processing.ui",
        ui_dir / "dialog_about.ui",
        ui_dir / "dialog_settings.ui",
        ui_dir / "dialog_shortcuts.ui",
        ui_dir / "dock_anno.ui",
        ui_dir / "dock_file.ui",
        ui_dir / "dock_info.ui",
        ui_dir / "dock_label.ui",
        ui_dir / "dialog_export.ui",
        # ui_dir / "dialog_import.ui",
        # ui_dir / "dialog_new_proj.ui",
        # ui_dir / "dialog_category_choice.ui",
        # ui_dir / "dialog_model_manager.ui",
    ]
    uics = [str(ui_file) + "," + str(ui_dst / f"{ui_file.stem}.py") for ui_file in ui_files]
    args = parser.parse_args([
        "--uic_path",
        *uics,
        "--rcc_path",
        "resources/icons.qrc,icons_rc.py",
    ])
    main(args)
