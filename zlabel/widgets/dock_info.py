# -*- coding: utf-8 -*-
# @Author  : LG

from typing import List
from qtpy.QtCore import Qt, QSize, Signal, Slot
from qtpy.QtWidgets import (
    QWidget,
    QListWidgetItem,
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QDockWidget,
)

from zlabel.utils import Annotation, Result, User

from .ui import Ui_ZDockInfoContent


class ZDockInfoContent(QWidget, Ui_ZDockInfoContent):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def set_user(self, user: User | None):
        if user is None:
            return
        self.label_username.setText(user.name)

    def set_info_by_result(self, result: Result | None):
        if result is None:
            txt_note, txt_x, txt_y, txt_w, txt_h = "", "", "", "", ""
        else:
            txt_note, txt_x, txt_y, txt_w, txt_h = (
                result.note,
                f"{result.x:.2f}",
                f"{result.y:.2f}",
                f"{result.w:.2f}",
                f"{result.h:.2f}",
            )
        self.ledit_anno_note.setText(txt_note)
        self.label_anno_x.setText(txt_x)
        self.label_anno_y.setText(txt_y)
        self.label_anno_w.setText(txt_w)
        self.label_anno_h.setText(txt_h)

    def set_info_by_anno(self, anno: Annotation | None):
        if anno is None:
            self.label_img_width.setText("")
            self.label_img_height.setText("")
            self.set_info_by_result(None)
        else:
            self.label_img_width.setText(f"{anno.original_width:.2f}")
            self.label_img_height.setText(f"{anno.original_height:.2f}")
            if anno.created_by is not None:
                self.set_user(anno.created_by)
            result = anno.crt_result
            self.set_info_by_result(result)
