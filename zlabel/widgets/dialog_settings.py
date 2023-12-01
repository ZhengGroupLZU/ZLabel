# -*- coding: utf-8 -*-
# @Author  : LG

import os

from qtpy.QtCore import QSettings, QSize, Qt, Signal
from qtpy.QtWidgets import (
    QColorDialog,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QPushButton,
    QWidget,
    QApplication,
)

from .ui import Ui_DialogSettings
from ..utils import StatusMode, MapMode, DrawMode, ClickMode, ContourMode


class DialogSettings(QDialog, Ui_DialogSettings):
    settings_changed = Signal(QSettings)

    def __init__(self, parent):
        super(DialogSettings, self).__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self.format = QSettings.Format.IniFormat
        self.conf_path = os.path.join(QApplication.applicationDirPath(), "zlabel.conf")
        self.settings = QSettings(self.conf_path, self.format)
        if not os.path.exists(self.conf_path):
            self.init_settings()
        else:
            self.load_settings()

        self.init_signals()

    def init_settings(self):
        self.settings.setValue("global/status_mode", StatusMode.VIEW.value)
        self.settings.setValue("global/map_mode", MapMode.LABEL.value)
        self.settings.setValue("global/draw_mode", DrawMode.SAM_RECT.value)
        self.settings.setValue("global/click_mode", ClickMode.POSITIVE.value)
        self.settings.setValue("global/contour_mode", ContourMode.SAVE_MAX_ONLY.value)
        self.settings.setValue("global/alpha", 0.5)
        self.settings.setValue("global/vertex_size", 3)

    def load_settings(self, path: str | None = None):
        self.settings = QSettings(path or self.conf_path, self.format)
        self.cbox_status_mode.setCurrentIndex(
            self.settings.value("global/status_mode", StatusMode.VIEW.value, type=int)
        )
        self.cbox_click_mode.setCurrentIndex(
            self.settings.value("global/click_mode", ClickMode.POSITIVE.value, type=int)
        )
        self.cbox_map_mode.setCurrentIndex(
            self.settings.value("global/map_mode", MapMode.LABEL.value, type=int)
        )
        self.cbox_draw_mode.setCurrentIndex(
            self.settings.value("global/draw_mode", DrawMode.SAM_RECT.value, type=int)
        )
        self.cbox_contour_mode.setCurrentIndex(
            self.settings.value(
                "global/contour_mode", ContourMode.SAVE_MAX_ONLY.value, type=int
            )
        )
        self.dspbox_alpha.setValue(self.settings.value("global/alpha", 0.5, type=float))
        self.spbox_vertex_size.setValue(
            self.settings.value("global/vertex_size", 3, type=int)
        )
        self.settings_changed.emit(self.settings)

    def get_item_and_widget(self, category, color: str):
        item = QListWidgetItem()
        item.setSizeHint(QSize(200, 40))

        widget = QWidget()
        layout = QHBoxLayout()
        category_label = QLabel()
        category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        category_label.setText(category)
        category_label.setObjectName("category")
        # 颜色
        color_button = QPushButton()
        color_button.setStyleSheet("QWidget {background-color: %s}" % color)
        color_button.setFixedWidth(50)
        color_button.clicked.connect(self.edit_category_item_color)
        color_button.setObjectName("color")
        # 删除
        delete_button = QPushButton()
        delete_button.setText("delete")
        delete_button.setFixedWidth(80)
        delete_button.clicked.connect(self.remove_category_item)

        if category == "__background__":
            color_button.setEnabled(False)
            delete_button.setEnabled(False)

        layout.addWidget(category_label)
        layout.addWidget(color_button)
        layout.addWidget(delete_button)
        widget.setLayout(layout)
        return item, widget

    def edit_category_item_color(self):
        button = self.sender()
        color = QColorDialog.getColor()
        if color.isValid():
            button.setStyleSheet("QWidget {background-color: %s}" % (color.name()))

    def remove_category_item(self):
        button = self.sender()
        row = self.category_list_widget.indexAt(button.parent().pos()).row()
        self.category_list_widget.takeItem(row)

    def add_new_category(self):
        category = self.category_input.text()
        color = self.color_button.palette().button().color().name()
        if category:
            item, item_widget = self.get_item_and_widget(category, color)
            self.category_list_widget.addItem(item)
            self.category_list_widget.setItemWidget(item, item_widget)
        self.category_input.clear()

    def choice_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_button.setStyleSheet(
                "QWidget {background-color: %s}" % color.name()
            )

    def apply(self):
        self.settings_changed.emit(self.settings)
        self.close()

    def on_settings_changed(self, k: str, v: int | float):
        self.settings.setValue(k, v)
        self.settings_changed.emit(self.settings)

    def init_signals(self):
        self.cbox_status_mode.currentIndexChanged.connect(
            lambda idx: self.on_settings_changed("global/status_mode", idx)
        )
        self.cbox_map_mode.currentIndexChanged.connect(
            lambda idx: self.on_settings_changed("global/map_mode", idx)
        )
        self.cbox_draw_mode.currentIndexChanged.connect(
            lambda idx: self.on_settings_changed("global/draw_mode", idx)
        )
        self.cbox_click_mode.currentIndexChanged.connect(
            lambda idx: self.on_settings_changed("global/click_mode", idx)
        )
        self.cbox_contour_mode.currentIndexChanged.connect(
            lambda idx: self.on_settings_changed("global/contour_mode", idx)
        )
        self.dspbox_alpha.valueChanged.connect(
            lambda value: self.on_settings_changed("global/alpha", value)
        )
        self.spbox_vertex_size.valueChanged.connect(
            lambda value: self.on_settings_changed("global/vertex_size", value)
        )

        self.add_button.clicked.connect(self.add_new_category)
        self.btn_apply.clicked.connect(self.apply)
        self.btn_cancel.clicked.connect(self.close)
        self.color_button.clicked.connect(self.choice_color)
