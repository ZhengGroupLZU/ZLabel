# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

from zlabel.widgets.zwidgets import ZColorButton
import icons_rc

class Ui_DialogSettings(object):
    def setupUi(self, DialogSettings):
        if not DialogSettings.objectName():
            DialogSettings.setObjectName(u"DialogSettings")
        DialogSettings.resize(977, 790)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(12)
        DialogSettings.setFont(font)
        self.gridLayout_5 = QGridLayout(DialogSettings)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.btn_cancel = QPushButton(DialogSettings)
        self.btn_cancel.setObjectName(u"btn_cancel")
        icon = QIcon()
        icon.addFile(u":/icon/icons/close-one.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_cancel.setIcon(icon)

        self.horizontalLayout_4.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton(DialogSettings)
        self.btn_apply.setObjectName(u"btn_apply")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/check-one.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_apply.setIcon(icon1)

        self.horizontalLayout_4.addWidget(self.btn_apply)


        self.gridLayout_5.addLayout(self.horizontalLayout_4, 1, 0, 1, 1)

        self.tabWidget = QTabWidget(DialogSettings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_application = QWidget()
        self.tab_application.setObjectName(u"tab_application")
        self.gridLayout_7 = QGridLayout(self.tab_application)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(5, 5, 5, 5)
        self.scrollArea = QScrollArea(self.tab_application)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 947, 699))
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.groupBox_application = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_application.setObjectName(u"groupBox_application")
        self.gridLayout_2 = QGridLayout(self.groupBox_application)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_2 = QLabel(self.groupBox_application)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)

        self.gridLayout_4.addWidget(self.label_2, 6, 0, 1, 1)

        self.cmbox_loglevel = QComboBox(self.groupBox_application)
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.setObjectName(u"cmbox_loglevel")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.cmbox_loglevel.sizePolicy().hasHeightForWidth())
        self.cmbox_loglevel.setSizePolicy(sizePolicy2)

        self.gridLayout_4.addWidget(self.cmbox_loglevel, 6, 1, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout_4, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_application, 0, 0, 1, 1)

        self.gbox_others = QGroupBox(self.scrollAreaWidgetContents)
        self.gbox_others.setObjectName(u"gbox_others")
        self.grid_inference_2 = QGridLayout(self.gbox_others)
        self.grid_inference_2.setObjectName(u"grid_inference_2")
        self.ledit_ocr_dir = QLineEdit(self.gbox_others)
        self.ledit_ocr_dir.setObjectName(u"ledit_ocr_dir")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.ledit_ocr_dir.sizePolicy().hasHeightForWidth())
        self.ledit_ocr_dir.setSizePolicy(sizePolicy3)

        self.grid_inference_2.addWidget(self.ledit_ocr_dir, 1, 1, 1, 1)

        self.label_ocr_dir = QLabel(self.gbox_others)
        self.label_ocr_dir.setObjectName(u"label_ocr_dir")

        self.grid_inference_2.addWidget(self.label_ocr_dir, 1, 0, 1, 1)

        self.btn_ocr_dir = QPushButton(self.gbox_others)
        self.btn_ocr_dir.setObjectName(u"btn_ocr_dir")

        self.grid_inference_2.addWidget(self.btn_ocr_dir, 1, 2, 1, 1)


        self.gridLayout.addWidget(self.gbox_others, 4, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 6, 0, 1, 1)

        self.gbox_performance = QGroupBox(self.scrollAreaWidgetContents)
        self.gbox_performance.setObjectName(u"gbox_performance")
        self.grid_performance = QGridLayout(self.gbox_performance)
        self.grid_performance.setObjectName(u"grid_performance")
        self.spin_image_cache_size = QSpinBox(self.gbox_performance)
        self.spin_image_cache_size.setObjectName(u"spin_image_cache_size")
        self.spin_image_cache_size.setMinimum(1)
        self.spin_image_cache_size.setMaximum(64)
        self.spin_image_cache_size.setValue(5)

        self.grid_performance.addWidget(self.spin_image_cache_size, 0, 3, 1, 1)

        self.spin_tl_cache_size = QSpinBox(self.gbox_performance)
        self.spin_tl_cache_size.setObjectName(u"spin_tl_cache_size")
        self.spin_tl_cache_size.setMinimum(1)
        self.spin_tl_cache_size.setMaximum(256)
        self.spin_tl_cache_size.setValue(32)

        self.grid_performance.addWidget(self.spin_tl_cache_size, 2, 1, 1, 1)

        self.spin_tl_cell_size = QSpinBox(self.gbox_performance)
        self.spin_tl_cell_size.setObjectName(u"spin_tl_cell_size")
        self.spin_tl_cell_size.setMinimum(16)
        self.spin_tl_cell_size.setMaximum(128)
        self.spin_tl_cell_size.setValue(48)

        self.grid_performance.addWidget(self.spin_tl_cell_size, 2, 3, 1, 1)

        self.label_display_max_side = QLabel(self.gbox_performance)
        self.label_display_max_side.setObjectName(u"label_display_max_side")
        sizePolicy1.setHeightForWidth(self.label_display_max_side.sizePolicy().hasHeightForWidth())
        self.label_display_max_side.setSizePolicy(sizePolicy1)
        self.label_display_max_side.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.grid_performance.addWidget(self.label_display_max_side, 0, 0, 1, 1)

        self.label_tl_cell_size = QLabel(self.gbox_performance)
        self.label_tl_cell_size.setObjectName(u"label_tl_cell_size")
        sizePolicy1.setHeightForWidth(self.label_tl_cell_size.sizePolicy().hasHeightForWidth())
        self.label_tl_cell_size.setSizePolicy(sizePolicy1)
        self.label_tl_cell_size.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.grid_performance.addWidget(self.label_tl_cell_size, 2, 2, 1, 1)

        self.spin_display_max_side = QSpinBox(self.gbox_performance)
        self.spin_display_max_side.setObjectName(u"spin_display_max_side")
        self.spin_display_max_side.setMinimum(512)
        self.spin_display_max_side.setMaximum(8192)
        self.spin_display_max_side.setSingleStep(256)
        self.spin_display_max_side.setValue(2560)

        self.grid_performance.addWidget(self.spin_display_max_side, 0, 1, 1, 1)

        self.label_tl_cache_size = QLabel(self.gbox_performance)
        self.label_tl_cache_size.setObjectName(u"label_tl_cache_size")
        sizePolicy1.setHeightForWidth(self.label_tl_cache_size.sizePolicy().hasHeightForWidth())
        self.label_tl_cache_size.setSizePolicy(sizePolicy1)
        self.label_tl_cache_size.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.grid_performance.addWidget(self.label_tl_cache_size, 2, 0, 1, 1)

        self.label_image_cache_size = QLabel(self.gbox_performance)
        self.label_image_cache_size.setObjectName(u"label_image_cache_size")
        sizePolicy1.setHeightForWidth(self.label_image_cache_size.sizePolicy().hasHeightForWidth())
        self.label_image_cache_size.setSizePolicy(sizePolicy1)
        self.label_image_cache_size.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.grid_performance.addWidget(self.label_image_cache_size, 0, 2, 1, 1)

        self.ckbox_copy_prev = QCheckBox(self.gbox_performance)
        self.ckbox_copy_prev.setObjectName(u"ckbox_copy_prev")

        self.grid_performance.addWidget(self.ckbox_copy_prev, 3, 5, 1, 1)

        self.ckbox_ocr_enable = QCheckBox(self.gbox_performance)
        self.ckbox_ocr_enable.setObjectName(u"ckbox_ocr_enable")

        self.grid_performance.addWidget(self.ckbox_ocr_enable, 3, 4, 1, 1)

        self.ckbox_random = QCheckBox(self.gbox_performance)
        self.ckbox_random.setObjectName(u"ckbox_random")
        self.ckbox_random.setChecked(False)

        self.grid_performance.addWidget(self.ckbox_random, 3, 3, 1, 1)

        self.ckbox_auto_dish = QCheckBox(self.gbox_performance)
        self.ckbox_auto_dish.setObjectName(u"ckbox_auto_dish")

        self.grid_performance.addWidget(self.ckbox_auto_dish, 3, 2, 1, 1)

        self.ckbox_catmull_rom = QCheckBox(self.gbox_performance)
        self.ckbox_catmull_rom.setObjectName(u"ckbox_catmull_rom")
        self.ckbox_catmull_rom.setChecked(False)

        self.grid_performance.addWidget(self.ckbox_catmull_rom, 3, 0, 1, 2)

        self.label_tl_small_side = QLabel(self.gbox_performance)
        self.label_tl_small_side.setObjectName(u"label_tl_small_side")
        sizePolicy1.setHeightForWidth(self.label_tl_small_side.sizePolicy().hasHeightForWidth())
        self.label_tl_small_side.setSizePolicy(sizePolicy1)
        self.label_tl_small_side.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.grid_performance.addWidget(self.label_tl_small_side, 2, 4, 1, 1)

        self.spin_tl_small_side = QSpinBox(self.gbox_performance)
        self.spin_tl_small_side.setObjectName(u"spin_tl_small_side")
        self.spin_tl_small_side.setMinimum(128)
        self.spin_tl_small_side.setMaximum(2048)
        self.spin_tl_small_side.setSingleStep(64)
        self.spin_tl_small_side.setValue(512)

        self.grid_performance.addWidget(self.spin_tl_small_side, 2, 5, 1, 1)

        self.ckbox_mipmap = QCheckBox(self.gbox_performance)
        self.ckbox_mipmap.setObjectName(u"ckbox_mipmap")
        self.ckbox_mipmap.setChecked(True)

        self.grid_performance.addWidget(self.ckbox_mipmap, 4, 0, 1, 2)


        self.gridLayout.addWidget(self.gbox_performance, 3, 0, 1, 1)

        self.gbox_appearance = QGroupBox(self.scrollAreaWidgetContents)
        self.gbox_appearance.setObjectName(u"gbox_appearance")
        self.grid_appearance = QGridLayout(self.gbox_appearance)
        self.grid_appearance.setObjectName(u"grid_appearance")
        self.label = QLabel(self.gbox_appearance)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label, 0, 0, 1, 1)

        self.dspbox_alpha = QDoubleSpinBox(self.gbox_appearance)
        self.dspbox_alpha.setObjectName(u"dspbox_alpha")
        sizePolicy2.setHeightForWidth(self.dspbox_alpha.sizePolicy().hasHeightForWidth())
        self.dspbox_alpha.setSizePolicy(sizePolicy2)
        self.dspbox_alpha.setMinimumSize(QSize(63, 0))
        self.dspbox_alpha.setMaximum(1.000000000000000)
        self.dspbox_alpha.setSingleStep(0.100000000000000)
        self.dspbox_alpha.setValue(0.100000000000000)

        self.grid_appearance.addWidget(self.dspbox_alpha, 0, 1, 1, 1)

        self.label_default_color = QLabel(self.gbox_appearance)
        self.label_default_color.setObjectName(u"label_default_color")
        self.label_default_color.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_default_color, 0, 2, 1, 1)

        self.btn_default_color = ZColorButton(self.gbox_appearance)
        self.btn_default_color.setObjectName(u"btn_default_color")
        sizePolicy2.setHeightForWidth(self.btn_default_color.sizePolicy().hasHeightForWidth())
        self.btn_default_color.setSizePolicy(sizePolicy2)

        self.grid_appearance.addWidget(self.btn_default_color, 0, 3, 1, 1)

        self.label_edit_alpha = QLabel(self.gbox_appearance)
        self.label_edit_alpha.setObjectName(u"label_edit_alpha")
        self.label_edit_alpha.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_edit_alpha, 1, 0, 1, 1)

        self.dspbox_edit_alpha = QDoubleSpinBox(self.gbox_appearance)
        self.dspbox_edit_alpha.setObjectName(u"dspbox_edit_alpha")
        self.dspbox_edit_alpha.setMaximum(1.000000000000000)
        self.dspbox_edit_alpha.setSingleStep(0.050000000000000)
        self.dspbox_edit_alpha.setValue(0.050000000000000)

        self.grid_appearance.addWidget(self.dspbox_edit_alpha, 1, 1, 1, 1)

        self.label_draw_alpha = QLabel(self.gbox_appearance)
        self.label_draw_alpha.setObjectName(u"label_draw_alpha")
        self.label_draw_alpha.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_draw_alpha, 1, 2, 1, 1)

        self.dspbox_draw_alpha = QDoubleSpinBox(self.gbox_appearance)
        self.dspbox_draw_alpha.setObjectName(u"dspbox_draw_alpha")
        self.dspbox_draw_alpha.setMaximum(1.000000000000000)
        self.dspbox_draw_alpha.setSingleStep(0.050000000000000)
        self.dspbox_draw_alpha.setValue(0.050000000000000)

        self.grid_appearance.addWidget(self.dspbox_draw_alpha, 1, 3, 1, 1)

        self.label_hline_color = QLabel(self.gbox_appearance)
        self.label_hline_color.setObjectName(u"label_hline_color")
        sizePolicy1.setHeightForWidth(self.label_hline_color.sizePolicy().hasHeightForWidth())
        self.label_hline_color.setSizePolicy(sizePolicy1)
        self.label_hline_color.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_hline_color, 0, 4, 1, 1)

        self.btn_hline_color = ZColorButton(self.gbox_appearance)
        self.btn_hline_color.setObjectName(u"btn_hline_color")
        sizePolicy2.setHeightForWidth(self.btn_hline_color.sizePolicy().hasHeightForWidth())
        self.btn_hline_color.setSizePolicy(sizePolicy2)

        self.grid_appearance.addWidget(self.btn_hline_color, 0, 5, 1, 1)

        self.label_hline_width = QLabel(self.gbox_appearance)
        self.label_hline_width.setObjectName(u"label_hline_width")
        sizePolicy1.setHeightForWidth(self.label_hline_width.sizePolicy().hasHeightForWidth())
        self.label_hline_width.setSizePolicy(sizePolicy1)
        self.label_hline_width.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_hline_width, 1, 4, 1, 1)

        self.spin_hline_width = QSpinBox(self.gbox_appearance)
        self.spin_hline_width.setObjectName(u"spin_hline_width")
        self.spin_hline_width.setMinimum(1)
        self.spin_hline_width.setMaximum(10)

        self.grid_appearance.addWidget(self.spin_hline_width, 1, 5, 1, 1)

        self.label_mag_min = QLabel(self.gbox_appearance)
        self.label_mag_min.setObjectName(u"label_mag_min")
        self.label_mag_min.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_mag_min, 8, 0, 1, 1)

        self.dspbox_mag_min = QDoubleSpinBox(self.gbox_appearance)
        self.dspbox_mag_min.setObjectName(u"dspbox_mag_min")
        self.dspbox_mag_min.setMinimum(0.500000000000000)
        self.dspbox_mag_min.setMaximum(20.000000000000000)
        self.dspbox_mag_min.setSingleStep(0.500000000000000)
        self.dspbox_mag_min.setValue(1.000000000000000)

        self.grid_appearance.addWidget(self.dspbox_mag_min, 8, 1, 1, 1)

        self.label_vline_color = QLabel(self.gbox_appearance)
        self.label_vline_color.setObjectName(u"label_vline_color")
        sizePolicy1.setHeightForWidth(self.label_vline_color.sizePolicy().hasHeightForWidth())
        self.label_vline_color.setSizePolicy(sizePolicy1)
        self.label_vline_color.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_vline_color, 5, 4, 1, 1)

        self.btn_vline_color = ZColorButton(self.gbox_appearance)
        self.btn_vline_color.setObjectName(u"btn_vline_color")
        sizePolicy2.setHeightForWidth(self.btn_vline_color.sizePolicy().hasHeightForWidth())
        self.btn_vline_color.setSizePolicy(sizePolicy2)

        self.grid_appearance.addWidget(self.btn_vline_color, 5, 5, 1, 1)

        self.label_vline_width = QLabel(self.gbox_appearance)
        self.label_vline_width.setObjectName(u"label_vline_width")
        sizePolicy1.setHeightForWidth(self.label_vline_width.sizePolicy().hasHeightForWidth())
        self.label_vline_width.setSizePolicy(sizePolicy1)
        self.label_vline_width.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_vline_width, 8, 4, 1, 1)

        self.spin_vline_width = QSpinBox(self.gbox_appearance)
        self.spin_vline_width.setObjectName(u"spin_vline_width")
        self.spin_vline_width.setMinimum(1)
        self.spin_vline_width.setMaximum(10)

        self.grid_appearance.addWidget(self.spin_vline_width, 8, 5, 1, 1)

        self.label_mag_diameter = QLabel(self.gbox_appearance)
        self.label_mag_diameter.setObjectName(u"label_mag_diameter")
        self.label_mag_diameter.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_mag_diameter, 5, 0, 1, 1)

        self.spin_mag_diameter = QSpinBox(self.gbox_appearance)
        self.spin_mag_diameter.setObjectName(u"spin_mag_diameter")
        self.spin_mag_diameter.setMinimum(80)
        self.spin_mag_diameter.setMaximum(400)
        self.spin_mag_diameter.setValue(200)

        self.grid_appearance.addWidget(self.spin_mag_diameter, 5, 1, 1, 1)

        self.label_mag_max = QLabel(self.gbox_appearance)
        self.label_mag_max.setObjectName(u"label_mag_max")
        self.label_mag_max.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.grid_appearance.addWidget(self.label_mag_max, 5, 2, 1, 1)

        self.dspbox_mag_max = QDoubleSpinBox(self.gbox_appearance)
        self.dspbox_mag_max.setObjectName(u"dspbox_mag_max")
        self.dspbox_mag_max.setMinimum(0.500000000000000)
        self.dspbox_mag_max.setMaximum(20.000000000000000)
        self.dspbox_mag_max.setSingleStep(0.500000000000000)
        self.dspbox_mag_max.setValue(10.000000000000000)

        self.grid_appearance.addWidget(self.dspbox_mag_max, 5, 3, 1, 1)


        self.gridLayout.addWidget(self.gbox_appearance, 1, 0, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_7.addWidget(self.scrollArea, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_application, "")
        self.tab_remote = QWidget()
        self.tab_remote.setObjectName(u"tab_remote")
        self.gridLayout_remote = QGridLayout(self.tab_remote)
        self.gridLayout_remote.setObjectName(u"gridLayout_remote")
        self.gridLayout_remote.setContentsMargins(5, 5, 5, 5)
        self.scrollArea_remote = QScrollArea(self.tab_remote)
        self.scrollArea_remote.setObjectName(u"scrollArea_remote")
        self.scrollArea_remote.setWidgetResizable(True)
        self.scrollAreaWidgetContents_remote = QWidget()
        self.scrollAreaWidgetContents_remote.setObjectName(u"scrollAreaWidgetContents_remote")
        self.scrollAreaWidgetContents_remote.setGeometry(QRect(0, 0, 947, 699))
        self.gridLayout_remote_body = QGridLayout(self.scrollAreaWidgetContents_remote)
        self.gridLayout_remote_body.setObjectName(u"gridLayout_remote_body")
        self.gridLayout_remote_body.setContentsMargins(3, 3, 3, 3)
        self.groupBox_remote = QGroupBox(self.scrollAreaWidgetContents_remote)
        self.groupBox_remote.setObjectName(u"groupBox_remote")
        self.gridLayout_2_remote = QGridLayout(self.groupBox_remote)
        self.gridLayout_2_remote.setObjectName(u"gridLayout_2_remote")
        self.gridLayout_2_remote.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_4_remote = QGridLayout()
        self.gridLayout_4_remote.setObjectName(u"gridLayout_4_remote")
        self.ledit_host = QLineEdit(self.groupBox_remote)
        self.ledit_host.setObjectName(u"ledit_host")
        self.ledit_host.setEnabled(True)

        self.gridLayout_4_remote.addWidget(self.ledit_host, 0, 1, 1, 1)

        self.ledit_username = QLineEdit(self.groupBox_remote)
        self.ledit_username.setObjectName(u"ledit_username")

        self.gridLayout_4_remote.addWidget(self.ledit_username, 1, 1, 1, 1)

        self.ledit_password = QLineEdit(self.groupBox_remote)
        self.ledit_password.setObjectName(u"ledit_password")
        self.ledit_password.setInputMethodHints(Qt.InputMethodHint.ImhHiddenText|Qt.InputMethodHint.ImhNoAutoUppercase|Qt.InputMethodHint.ImhNoPredictiveText|Qt.InputMethodHint.ImhSensitiveData)
        self.ledit_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_4_remote.addWidget(self.ledit_password, 2, 1, 1, 1)

        self.label_3 = QLabel(self.groupBox_remote)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_4_remote.addWidget(self.label_3, 0, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox_remote)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_4_remote.addWidget(self.label_4, 1, 0, 1, 1)

        self.label_5 = QLabel(self.groupBox_remote)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_4_remote.addWidget(self.label_5, 2, 0, 1, 1)


        self.gridLayout_2_remote.addLayout(self.gridLayout_4_remote, 0, 0, 1, 1)


        self.gridLayout_remote_body.addWidget(self.groupBox_remote, 0, 0, 1, 1)

        self.verticalSpacer_remote = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_remote_body.addItem(self.verticalSpacer_remote, 1, 0, 1, 1)

        self.scrollArea_remote.setWidget(self.scrollAreaWidgetContents_remote)

        self.gridLayout_remote.addWidget(self.scrollArea_remote, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_remote, "")
        self.tab_inference = QWidget()
        self.tab_inference.setObjectName(u"tab_inference")
        self.gridLayout_inference = QGridLayout(self.tab_inference)
        self.gridLayout_inference.setObjectName(u"gridLayout_inference")
        self.gridLayout_inference.setContentsMargins(5, 5, 5, 5)
        self.scrollArea_inference = QScrollArea(self.tab_inference)
        self.scrollArea_inference.setObjectName(u"scrollArea_inference")
        self.scrollArea_inference.setWidgetResizable(True)
        self.scrollAreaWidgetContents_inference = QWidget()
        self.scrollAreaWidgetContents_inference.setObjectName(u"scrollAreaWidgetContents_inference")
        self.scrollAreaWidgetContents_inference.setGeometry(QRect(0, 0, 947, 699))
        self.gridLayout_inference_body = QGridLayout(self.scrollAreaWidgetContents_inference)
        self.gridLayout_inference_body.setObjectName(u"gridLayout_inference_body")
        self.gridLayout_inference_body.setContentsMargins(3, 3, 3, 3)
        self.gbox_inference = QGroupBox(self.scrollAreaWidgetContents_inference)
        self.gbox_inference.setObjectName(u"gbox_inference")
        self.grid_inference = QGridLayout(self.gbox_inference)
        self.grid_inference.setObjectName(u"grid_inference")
        self.spin_upload_size = QSpinBox(self.gbox_inference)
        self.spin_upload_size.setObjectName(u"spin_upload_size")
        self.spin_upload_size.setMinimum(64)
        self.spin_upload_size.setMaximum(8192)
        self.spin_upload_size.setSingleStep(64)
        self.spin_upload_size.setValue(1024)

        self.grid_inference.addWidget(self.spin_upload_size, 4, 1, 1, 1)

        self.cmbox_backend = QComboBox(self.gbox_inference)
        self.cmbox_backend.addItem("")
        self.cmbox_backend.addItem("")
        self.cmbox_backend.addItem("")
        self.cmbox_backend.addItem("")
        self.cmbox_backend.addItem("")
        self.cmbox_backend.setObjectName(u"cmbox_backend")

        self.grid_inference.addWidget(self.cmbox_backend, 1, 1, 1, 1)

        self.label_inf_mode = QLabel(self.gbox_inference)
        self.label_inf_mode.setObjectName(u"label_inf_mode")

        self.grid_inference.addWidget(self.label_inf_mode, 0, 0, 1, 1)

        self.label_backend = QLabel(self.gbox_inference)
        self.label_backend.setObjectName(u"label_backend")

        self.grid_inference.addWidget(self.label_backend, 1, 0, 1, 1)

        self.label_model_folder = QLabel(self.gbox_inference)
        self.label_model_folder.setObjectName(u"label_model_folder")

        self.grid_inference.addWidget(self.label_model_folder, 3, 0, 1, 1)

        self.cmbox_model_name = QComboBox(self.gbox_inference)
        self.cmbox_model_name.addItem("")
        self.cmbox_model_name.addItem("")
        self.cmbox_model_name.addItem("")
        self.cmbox_model_name.addItem("")
        self.cmbox_model_name.addItem("")
        self.cmbox_model_name.setObjectName(u"cmbox_model_name")

        self.grid_inference.addWidget(self.cmbox_model_name, 2, 1, 1, 1)

        self.ledit_model_dir = QLineEdit(self.gbox_inference)
        self.ledit_model_dir.setObjectName(u"ledit_model_dir")

        self.grid_inference.addWidget(self.ledit_model_dir, 3, 1, 1, 1)

        self.label_model = QLabel(self.gbox_inference)
        self.label_model.setObjectName(u"label_model")

        self.grid_inference.addWidget(self.label_model, 2, 0, 1, 1)

        self.cmbox_inference_mode = QComboBox(self.gbox_inference)
        self.cmbox_inference_mode.addItem("")
        self.cmbox_inference_mode.addItem("")
        self.cmbox_inference_mode.setObjectName(u"cmbox_inference_mode")

        self.grid_inference.addWidget(self.cmbox_inference_mode, 0, 1, 1, 1)

        self.btn_model_dir = QPushButton(self.gbox_inference)
        self.btn_model_dir.setObjectName(u"btn_model_dir")

        self.grid_inference.addWidget(self.btn_model_dir, 3, 2, 1, 1)

        self.label_upload_size = QLabel(self.gbox_inference)
        self.label_upload_size.setObjectName(u"label_upload_size")

        self.grid_inference.addWidget(self.label_upload_size, 4, 0, 1, 1)


        self.gridLayout_inference_body.addWidget(self.gbox_inference, 0, 0, 1, 1)

        self.verticalSpacer_inference = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_inference_body.addItem(self.verticalSpacer_inference, 1, 0, 1, 1)

        self.scrollArea_inference.setWidget(self.scrollAreaWidgetContents_inference)

        self.gridLayout_inference.addWidget(self.scrollArea_inference, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_inference, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout_13 = QGridLayout(self.tab)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.scrollArea_2 = QScrollArea(self.tab)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 939, 691))
        self.gridLayout_8 = QGridLayout(self.scrollAreaWidgetContents_2)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(3, 3, 3, 3)
        self.groupBox_5 = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy4)
        self.groupBox_5.setMinimumSize(QSize(0, 500))
        self.gridLayout_11 = QGridLayout(self.groupBox_5)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.gridLayout_11.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_12 = QGridLayout()
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.btn_new_project = QPushButton(self.groupBox_5)
        self.btn_new_project.setObjectName(u"btn_new_project")

        self.gridLayout_12.addWidget(self.btn_new_project, 0, 1, 1, 1)

        self.status_btns = QVBoxLayout()
        self.status_btns.setObjectName(u"status_btns")
        self.btn_add_status = QPushButton(self.groupBox_5)
        self.btn_add_status.setObjectName(u"btn_add_status")

        self.status_btns.addWidget(self.btn_add_status)

        self.btn_del_status = QPushButton(self.groupBox_5)
        self.btn_del_status.setObjectName(u"btn_del_status")

        self.status_btns.addWidget(self.btn_del_status)

        self.status_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.status_btns.addItem(self.status_spacer)


        self.gridLayout_12.addLayout(self.status_btns, 6, 2, 1, 1)

        self.label_statuses = QLabel(self.groupBox_5)
        self.label_statuses.setObjectName(u"label_statuses")

        self.gridLayout_12.addWidget(self.label_statuses, 6, 0, 1, 1)

        self.ledit_prjdesc = QLineEdit(self.groupBox_5)
        self.ledit_prjdesc.setObjectName(u"ledit_prjdesc")

        self.gridLayout_12.addWidget(self.ledit_prjdesc, 3, 1, 1, 2)

        self.label_14 = QLabel(self.groupBox_5)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_12.addWidget(self.label_14, 5, 0, 1, 1)

        self.table_labels = QTableWidget(self.groupBox_5)
        if (self.table_labels.columnCount() < 4):
            self.table_labels.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table_labels.setObjectName(u"table_labels")
        sizePolicy.setHeightForWidth(self.table_labels.sizePolicy().hasHeightForWidth())
        self.table_labels.setSizePolicy(sizePolicy)

        self.gridLayout_12.addWidget(self.table_labels, 5, 1, 1, 1)

        self.label_15 = QLabel(self.groupBox_5)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_12.addWidget(self.label_15, 3, 0, 1, 1)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.btn_add_label = QPushButton(self.groupBox_5)
        self.btn_add_label.setObjectName(u"btn_add_label")

        self.verticalLayout_2.addWidget(self.btn_add_label)

        self.btn_delete_label = QPushButton(self.groupBox_5)
        self.btn_delete_label.setObjectName(u"btn_delete_label")

        self.verticalLayout_2.addWidget(self.btn_delete_label)

        self.btn_clear = QPushButton(self.groupBox_5)
        self.btn_clear.setObjectName(u"btn_clear")

        self.verticalLayout_2.addWidget(self.btn_clear)

        self.verticalSpacer_2 = QSpacerItem(20, 110, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.gridLayout_12.addLayout(self.verticalLayout_2, 5, 2, 1, 1)

        self.btn_delete_project = QPushButton(self.groupBox_5)
        self.btn_delete_project.setObjectName(u"btn_delete_project")

        self.gridLayout_12.addWidget(self.btn_delete_project, 0, 2, 1, 1)

        self.ledit_projname = QLineEdit(self.groupBox_5)
        self.ledit_projname.setObjectName(u"ledit_projname")

        self.gridLayout_12.addWidget(self.ledit_projname, 2, 1, 1, 2)

        self.table_statuses = QTableWidget(self.groupBox_5)
        if (self.table_statuses.columnCount() < 1):
            self.table_statuses.setColumnCount(1)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.table_statuses.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        self.table_statuses.setObjectName(u"table_statuses")
        self.table_statuses.setMaximumSize(QSize(16777215, 160))

        self.gridLayout_12.addWidget(self.table_statuses, 6, 1, 1, 1)

        self.label_16 = QLabel(self.groupBox_5)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_12.addWidget(self.label_16, 2, 0, 1, 1)

        self.label_projects = QLabel(self.groupBox_5)
        self.label_projects.setObjectName(u"label_projects")

        self.gridLayout_12.addWidget(self.label_projects, 1, 0, 1, 1)

        self.combo_projects = QComboBox(self.groupBox_5)
        self.combo_projects.setObjectName(u"combo_projects")

        self.gridLayout_12.addWidget(self.combo_projects, 1, 1, 1, 2)

        self.label_preset = QLabel(self.groupBox_5)
        self.label_preset.setObjectName(u"label_preset")

        self.gridLayout_12.addWidget(self.label_preset, 4, 0, 1, 1)

        self.combo_preset = QComboBox(self.groupBox_5)
        self.combo_preset.addItem("")
        self.combo_preset.addItem("")
        self.combo_preset.setObjectName(u"combo_preset")

        self.gridLayout_12.addWidget(self.combo_preset, 4, 1, 1, 2)


        self.gridLayout_11.addLayout(self.gridLayout_12, 0, 0, 1, 1)


        self.gridLayout_8.addWidget(self.groupBox_5, 0, 0, 1, 1)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)

        self.gridLayout_13.addWidget(self.scrollArea_2, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab, "")

        self.gridLayout_5.addWidget(self.tabWidget, 0, 0, 1, 1)


        self.retranslateUi(DialogSettings)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DialogSettings)
    # setupUi

    def retranslateUi(self, DialogSettings):
        DialogSettings.setWindowTitle(QCoreApplication.translate("DialogSettings", u"Setting", None))
        self.btn_cancel.setText(QCoreApplication.translate("DialogSettings", u"Cancel", None))
        self.btn_apply.setText(QCoreApplication.translate("DialogSettings", u"Apply", None))
        self.groupBox_application.setTitle(QCoreApplication.translate("DialogSettings", u"Application", None))
        self.label_2.setText(QCoreApplication.translate("DialogSettings", u"Log level:", None))
        self.cmbox_loglevel.setItemText(0, QCoreApplication.translate("DialogSettings", u"DEBUG", None))
        self.cmbox_loglevel.setItemText(1, QCoreApplication.translate("DialogSettings", u"INFO", None))
        self.cmbox_loglevel.setItemText(2, QCoreApplication.translate("DialogSettings", u"WARNING", None))
        self.cmbox_loglevel.setItemText(3, QCoreApplication.translate("DialogSettings", u"ERROR", None))

        self.gbox_others.setTitle(QCoreApplication.translate("DialogSettings", u"Others", None))
        self.label_ocr_dir.setText(QCoreApplication.translate("DialogSettings", u"WeChat OCR Folder:", None))
        self.btn_ocr_dir.setText(QCoreApplication.translate("DialogSettings", u"Browse...", None))
        self.gbox_performance.setTitle(QCoreApplication.translate("DialogSettings", u"Performance", None))
        self.label_display_max_side.setText(QCoreApplication.translate("DialogSettings", u"Display max side:", None))
        self.label_tl_cell_size.setText(QCoreApplication.translate("DialogSettings", u"Timeline cell size:", None))
        self.spin_display_max_side.setSuffix(QCoreApplication.translate("DialogSettings", u"px", None))
        self.label_tl_cache_size.setText(QCoreApplication.translate("DialogSettings", u"Timeline cache size:", None))
        self.label_image_cache_size.setText(QCoreApplication.translate("DialogSettings", u"Image cache size:", None))
        self.ckbox_copy_prev.setText(QCoreApplication.translate("DialogSettings", u"Copy previous frame", None))
        self.ckbox_ocr_enable.setText(QCoreApplication.translate("DialogSettings", u"Manual timestamp", None))
        self.ckbox_random.setText(QCoreApplication.translate("DialogSettings", u"Enable Random Tasks", None))
        self.ckbox_auto_dish.setText(QCoreApplication.translate("DialogSettings", u"Auto-fit dish", None))
        self.ckbox_catmull_rom.setText(QCoreApplication.translate("DialogSettings", u"Enable Catmull-Rom Spline", None))
        self.label_tl_small_side.setText(QCoreApplication.translate("DialogSettings", u"Timeline small side:", None))
        self.spin_tl_small_side.setSuffix(QCoreApplication.translate("DialogSettings", u"px", None))
        self.ckbox_mipmap.setText(QCoreApplication.translate("DialogSettings", u"Enable Mipmap Anti-aliasing", None))
        self.gbox_appearance.setTitle(QCoreApplication.translate("DialogSettings", u"Appearance", None))
        self.label.setText(QCoreApplication.translate("DialogSettings", u"Fill alpha:", None))
        self.label_default_color.setText(QCoreApplication.translate("DialogSettings", u"Default color:", None))
        self.label_edit_alpha.setText(QCoreApplication.translate("DialogSettings", u"Edit fill alpha:", None))
        self.label_draw_alpha.setText(QCoreApplication.translate("DialogSettings", u"Draw fill alpha:", None))
        self.label_hline_color.setText(QCoreApplication.translate("DialogSettings", u"Hline color:", None))
        self.label_hline_width.setText(QCoreApplication.translate("DialogSettings", u"Hline width:", None))
        self.label_mag_min.setText(QCoreApplication.translate("DialogSettings", u"Magnifier min zoom:", None))
        self.label_vline_color.setText(QCoreApplication.translate("DialogSettings", u"Vline color:", None))
        self.label_vline_width.setText(QCoreApplication.translate("DialogSettings", u"Vline width:", None))
        self.label_mag_diameter.setText(QCoreApplication.translate("DialogSettings", u"Magnifier diameter:", None))
        self.label_mag_max.setText(QCoreApplication.translate("DialogSettings", u"Magnifier max zoom:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_application), QCoreApplication.translate("DialogSettings", u"Application", None))
        self.groupBox_remote.setTitle(QCoreApplication.translate("DialogSettings", u"Remote API", None))
        self.label_3.setText(QCoreApplication.translate("DialogSettings", u"Host:", None))
        self.label_4.setText(QCoreApplication.translate("DialogSettings", u"User name:", None))
        self.label_5.setText(QCoreApplication.translate("DialogSettings", u"Password:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_remote), QCoreApplication.translate("DialogSettings", u"Remote", None))
        self.gbox_inference.setTitle(QCoreApplication.translate("DialogSettings", u"Inference", None))
        self.cmbox_backend.setItemText(0, QCoreApplication.translate("DialogSettings", u"AUTO", None))
        self.cmbox_backend.setItemText(1, QCoreApplication.translate("DialogSettings", u"CPU", None))
        self.cmbox_backend.setItemText(2, QCoreApplication.translate("DialogSettings", u"CUDA", None))
        self.cmbox_backend.setItemText(3, QCoreApplication.translate("DialogSettings", u"Metal", None))
        self.cmbox_backend.setItemText(4, QCoreApplication.translate("DialogSettings", u"OpenCL", None))

        self.label_inf_mode.setText(QCoreApplication.translate("DialogSettings", u"Inference Mode:", None))
        self.label_backend.setText(QCoreApplication.translate("DialogSettings", u"Backend:", None))
        self.label_model_folder.setText(QCoreApplication.translate("DialogSettings", u"Model Folder:", None))
        self.cmbox_model_name.setItemText(0, QCoreApplication.translate("DialogSettings", u"SAM", None))
        self.cmbox_model_name.setItemText(1, QCoreApplication.translate("DialogSettings", u"EdgeSAM", None))
        self.cmbox_model_name.setItemText(2, QCoreApplication.translate("DialogSettings", u"SlimSAM", None))
        self.cmbox_model_name.setItemText(3, QCoreApplication.translate("DialogSettings", u"SAM2", None))
        self.cmbox_model_name.setItemText(4, QCoreApplication.translate("DialogSettings", u"SAM3", None))

        self.label_model.setText(QCoreApplication.translate("DialogSettings", u"Model:", None))
        self.cmbox_inference_mode.setItemText(0, QCoreApplication.translate("DialogSettings", u"Remote", None))
        self.cmbox_inference_mode.setItemText(1, QCoreApplication.translate("DialogSettings", u"Local", None))

        self.btn_model_dir.setText(QCoreApplication.translate("DialogSettings", u"Browse...", None))
        self.label_upload_size.setText(QCoreApplication.translate("DialogSettings", u"Upload Image Size:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_inference), QCoreApplication.translate("DialogSettings", u"Inference", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("DialogSettings", u"Project", None))
        self.btn_new_project.setText(QCoreApplication.translate("DialogSettings", u"New", None))
        self.btn_add_status.setText(QCoreApplication.translate("DialogSettings", u"Add", None))
        self.btn_del_status.setText(QCoreApplication.translate("DialogSettings", u"Delete", None))
        self.label_statuses.setText(QCoreApplication.translate("DialogSettings", u"Instances:", None))
        self.label_14.setText(QCoreApplication.translate("DialogSettings", u"Labels:", None))
        ___qtablewidgetitem = self.table_labels.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DialogSettings", u"ID", None))
        ___qtablewidgetitem1 = self.table_labels.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DialogSettings", u"Name", None))
        ___qtablewidgetitem2 = self.table_labels.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DialogSettings", u"Color", None))
        ___qtablewidgetitem3 = self.table_labels.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("DialogSettings", u"Delete", None))
        self.label_15.setText(QCoreApplication.translate("DialogSettings", u"Description:", None))
        self.btn_add_label.setText(QCoreApplication.translate("DialogSettings", u"Add", None))
        self.btn_delete_label.setText(QCoreApplication.translate("DialogSettings", u"Delete", None))
        self.btn_clear.setText(QCoreApplication.translate("DialogSettings", u"Clear", None))
        self.btn_delete_project.setText(QCoreApplication.translate("DialogSettings", u"Delete", None))
        ___qtablewidgetitem4 = self.table_statuses.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("DialogSettings", u"Status", None))
        self.label_16.setText(QCoreApplication.translate("DialogSettings", u"Name:", None))
        self.label_projects.setText(QCoreApplication.translate("DialogSettings", u"Project:", None))
        self.label_preset.setText(QCoreApplication.translate("DialogSettings", u"Load default:", None))
        self.combo_preset.setItemText(0, QCoreApplication.translate("DialogSettings", u"Empty", None))
        self.combo_preset.setItemText(1, QCoreApplication.translate("DialogSettings", u"Germination", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("DialogSettings", u"Project", None))
    # retranslateUi

