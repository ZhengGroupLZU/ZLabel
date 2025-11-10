import os
from typing import Literal

from tap import Tap
from tqdm.rich import tqdm  # type: ignore


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


class UicRccParser(Tap):
    pyside: Literal["pyside6", "pyside2"] = "pyside6"
    uic_path: list[str]
    rcc_path: list[str]

    def process_args(self) -> None:
        self.uics = [to_src_dst(p) for p in self.uic_path]
        self.rccs = [to_src_dst(p) for p in self.rcc_path]


def main(args: UicRccParser):
    for uic in tqdm(args.uics):
        os.system(f"{args.pyside}-uic -o {uic.dst} {uic.src}")
    for rcc in tqdm(args.rccs):
        os.system(f"{args.pyside}-rcc -o {rcc.dst} {rcc.src}")


if __name__ == "__main__":
    parser = UicRccParser()
    ui_dir = "zlabel/resources/ui"
    ui_dst = "zlabel/widgets/ui"
    uics = [
        f"{ui_dir}/mainwindow.ui,{ui_dst}/mainwindow.py",
        f"{ui_dir}/dialog_processing.ui,{ui_dst}/dialog_processing.py",
        f"{ui_dir}/dialog_about.ui,{ui_dst}/dialog_about.py",
        f"{ui_dir}/dialog_settings.ui,{ui_dst}/dialog_settings.py",
        f"{ui_dir}/dock_anno.ui,{ui_dst}/dock_anno.py",
        f"{ui_dir}/dock_file.ui,{ui_dst}/dock_file.py",
        f"{ui_dir}/dock_info.ui,{ui_dst}/dock_info.py",
        f"{ui_dir}/dock_label.ui,{ui_dst}/dock_label.py",
        # ignore
        # f"{ui_dir}/dialog_export.ui,{ui_dst}/dialog_export.py",
        # f"{ui_dir}/dialog_import.ui,{ui_dst}/dialog_import.py",
        # f"{ui_dir}/dialog_new_proj.ui,{ui_dst}/dialog_new_proj.py",
        # f"{ui_dir}/dialog_shortcuts.ui,{ui_dst}/dialog_shortcuts.py",
        # f"{ui_dir}/dialog_category_choice.ui,{ui_dst}/dialog_category_choice.py",
        # f"{ui_dir}/dialog_model_manager.ui,{ui_dst}/dialog_model_manager.py",
    ]
    args = parser.parse_args([
        "--uic_path",
        f"{ui_dir}/mainwindow.ui,{ui_dst}/mainwindow.py",
        f"{ui_dir}/dialog_processing.ui,{ui_dst}/dialog_processing.py",
        f"{ui_dir}/dialog_about.ui,{ui_dst}/dialog_about.py",
        f"{ui_dir}/dialog_settings.ui,{ui_dst}/dialog_settings.py",
        f"{ui_dir}/dock_anno.ui,{ui_dst}/dock_anno.py",
        f"{ui_dir}/dock_file.ui,{ui_dst}/dock_file.py",
        f"{ui_dir}/dock_info.ui,{ui_dst}/dock_info.py",
        f"{ui_dir}/dock_label.ui,{ui_dst}/dock_label.py",
        "--rcc_path",
        "zlabel/resources/icons.qrc,icons_rc.py",
    ])
    # args = parser.parse_args()
    main(args)
