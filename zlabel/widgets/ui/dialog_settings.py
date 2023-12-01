# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QTabWidget, QToolButton, QVBoxLayout, QWidget)
import icons_rc

class Ui_DialogSettings(object):
    def setupUi(self, DialogSettings):
        if not DialogSettings.objectName():
            DialogSettings.setObjectName(u"DialogSettings")
        DialogSettings.resize(607, 369)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(12)
        DialogSettings.setFont(font)
        self.tabWidget = QTabWidget(DialogSettings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(9, 9, 581, 291))
        self.tab_global = QWidget()
        self.tab_global.setObjectName(u"tab_global")
        self.groupBox = QGroupBox(self.tab_global)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(20, 10, 279, 184))
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.cbox_status_mode = QComboBox(self.groupBox)
        self.cbox_status_mode.addItem("")
        self.cbox_status_mode.addItem("")
        self.cbox_status_mode.addItem("")
        self.cbox_status_mode.setObjectName(u"cbox_status_mode")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.cbox_status_mode)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.cbox_draw_mode = QComboBox(self.groupBox)
        self.cbox_draw_mode.addItem("")
        self.cbox_draw_mode.addItem("")
        self.cbox_draw_mode.addItem("")
        self.cbox_draw_mode.addItem("")
        self.cbox_draw_mode.addItem("")
        self.cbox_draw_mode.addItem("")
        self.cbox_draw_mode.setObjectName(u"cbox_draw_mode")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.cbox_draw_mode)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.cbox_click_mode = QComboBox(self.groupBox)
        self.cbox_click_mode.addItem("")
        self.cbox_click_mode.addItem("")
        self.cbox_click_mode.setObjectName(u"cbox_click_mode")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.cbox_click_mode)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_4)

        self.cbox_map_mode = QComboBox(self.groupBox)
        self.cbox_map_mode.addItem("")
        self.cbox_map_mode.addItem("")
        self.cbox_map_mode.addItem("")
        self.cbox_map_mode.setObjectName(u"cbox_map_mode")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.cbox_map_mode)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_5)

        self.cbox_contour_mode = QComboBox(self.groupBox)
        self.cbox_contour_mode.addItem("")
        self.cbox_contour_mode.addItem("")
        self.cbox_contour_mode.addItem("")
        self.cbox_contour_mode.setObjectName(u"cbox_contour_mode")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.cbox_contour_mode)


        self.gridLayout_2.addLayout(self.formLayout, 0, 0, 1, 1)

        self.groupBox_2 = QGroupBox(self.tab_global)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(320, 40, 168, 89))
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.dspbox_alpha = QDoubleSpinBox(self.groupBox_2)
        self.dspbox_alpha.setObjectName(u"dspbox_alpha")
        self.dspbox_alpha.setMaximum(1.000000000000000)
        self.dspbox_alpha.setSingleStep(0.100000000000000)
        self.dspbox_alpha.setValue(0.500000000000000)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.dspbox_alpha)

        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_7)

        self.spbox_vertex_size = QSpinBox(self.groupBox_2)
        self.spbox_vertex_size.setObjectName(u"spbox_vertex_size")
        self.spbox_vertex_size.setMinimum(1)
        self.spbox_vertex_size.setMaximum(10)
        self.spbox_vertex_size.setValue(3)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.spbox_vertex_size)


        self.gridLayout.addLayout(self.formLayout_2, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_global, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.groupBox_3 = QGroupBox(self.tab)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(10, 10, 201, 101))
        self.gridLayout_3 = QGridLayout(self.groupBox_3)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_8 = QLabel(self.groupBox_3)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.cbox_project = QComboBox(self.groupBox_3)
        self.cbox_project.setObjectName(u"cbox_project")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.cbox_project)

        self.label_9 = QLabel(self.groupBox_3)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_9)

        self.cbox_user = QComboBox(self.groupBox_3)
        self.cbox_user.setObjectName(u"cbox_user")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.cbox_user)


        self.gridLayout_3.addLayout(self.formLayout_3, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.widget = QWidget(self.tab_2)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(0, 10, 589, 284))
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_2 = QWidget(self.widget)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.widget_2)

        self.category_list_widget = QListWidget(self.widget)
        self.category_list_widget.setObjectName(u"category_list_widget")

        self.verticalLayout.addWidget(self.category_list_widget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.category_input = QLineEdit(self.widget)
        self.category_input.setObjectName(u"category_input")

        self.horizontalLayout.addWidget(self.category_input)

        self.color_button = QToolButton(self.widget)
        self.color_button.setObjectName(u"color_button")
        self.color_button.setStyleSheet(u"background-color: rgb(0, 255, 0);")

        self.horizontalLayout.addWidget(self.color_button)

        self.add_button = QPushButton(self.widget)
        self.add_button.setObjectName(u"add_button")
        self.add_button.setMinimumSize(QSize(150, 0))
        self.add_button.setSizeIncrement(QSize(0, 0))

        self.horizontalLayout.addWidget(self.add_button)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_import = QPushButton(self.widget)
        self.pushButton_import.setObjectName(u"pushButton_import")
        icon = QIcon()
        icon.addFile(u":/icon/icons/afferent-three.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_import.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.pushButton_import)

        self.pushButton_export = QPushButton(self.widget)
        self.pushButton_export.setObjectName(u"pushButton_export")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/efferent-three.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_export.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.pushButton_export)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.cancel_button = QPushButton(self.widget)
        self.cancel_button.setObjectName(u"cancel_button")
        icon2 = QIcon()
        icon2.addFile(u":/icon/icons/close-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.cancel_button.setIcon(icon2)

        self.horizontalLayout_2.addWidget(self.cancel_button)

        self.apply_button = QPushButton(self.widget)
        self.apply_button.setObjectName(u"apply_button")
        icon3 = QIcon()
        icon3.addFile(u":/icon/icons/check-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.apply_button.setIcon(icon3)

        self.horizontalLayout_2.addWidget(self.apply_button)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.tabWidget.addTab(self.tab_2, "")
        self.horizontalLayoutWidget = QWidget(DialogSettings)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(20, 320, 571, 28))
        self.horizontalLayout_4 = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.btn_cancel = QPushButton(self.horizontalLayoutWidget)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setIcon(icon2)

        self.horizontalLayout_4.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton(self.horizontalLayoutWidget)
        self.btn_apply.setObjectName(u"btn_apply")
        self.btn_apply.setIcon(icon3)

        self.horizontalLayout_4.addWidget(self.btn_apply)


        self.retranslateUi(DialogSettings)

        self.tabWidget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(DialogSettings)
    # setupUi

    def retranslateUi(self, DialogSettings):
        DialogSettings.setWindowTitle(QCoreApplication.translate("DialogSettings", u"Setting", None))
        self.groupBox.setTitle(QCoreApplication.translate("DialogSettings", u"Modes", None))
        self.cbox_status_mode.setItemText(0, QCoreApplication.translate("DialogSettings", u"VIEW", None))
        self.cbox_status_mode.setItemText(1, QCoreApplication.translate("DialogSettings", u"CREATE", None))
        self.cbox_status_mode.setItemText(2, QCoreApplication.translate("DialogSettings", u"EDIT", None))

        self.label.setText(QCoreApplication.translate("DialogSettings", u"Status Mode:", None))
        self.label_2.setText(QCoreApplication.translate("DialogSettings", u"Draw Mode:", None))
        self.cbox_draw_mode.setItemText(0, QCoreApplication.translate("DialogSettings", u"POINT", None))
        self.cbox_draw_mode.setItemText(1, QCoreApplication.translate("DialogSettings", u"RECTANGLE", None))
        self.cbox_draw_mode.setItemText(2, QCoreApplication.translate("DialogSettings", u"POLYGON", None))
        self.cbox_draw_mode.setItemText(3, QCoreApplication.translate("DialogSettings", u"SAM", None))
        self.cbox_draw_mode.setItemText(4, QCoreApplication.translate("DialogSettings", u"SAM_RECT", None))
        self.cbox_draw_mode.setItemText(5, QCoreApplication.translate("DialogSettings", u"SAM_POLYGON", None))

        self.label_3.setText(QCoreApplication.translate("DialogSettings", u"Click Mode:", None))
        self.cbox_click_mode.setItemText(0, QCoreApplication.translate("DialogSettings", u"POSITIVE", None))
        self.cbox_click_mode.setItemText(1, QCoreApplication.translate("DialogSettings", u"NEGATIVE", None))

        self.label_4.setText(QCoreApplication.translate("DialogSettings", u"Map Mode:", None))
        self.cbox_map_mode.setItemText(0, QCoreApplication.translate("DialogSettings", u"LABEL", None))
        self.cbox_map_mode.setItemText(1, QCoreApplication.translate("DialogSettings", u"SEMANTIC", None))
        self.cbox_map_mode.setItemText(2, QCoreApplication.translate("DialogSettings", u"INSTANCE", None))

        self.label_5.setText(QCoreApplication.translate("DialogSettings", u"Contour Mode:", None))
        self.cbox_contour_mode.setItemText(0, QCoreApplication.translate("DialogSettings", u"SAVE_MAX_ONLY", None))
        self.cbox_contour_mode.setItemText(1, QCoreApplication.translate("DialogSettings", u"SAVE_EXTERNAL", None))
        self.cbox_contour_mode.setItemText(2, QCoreApplication.translate("DialogSettings", u"SAVE_ALL", None))

        self.groupBox_2.setTitle(QCoreApplication.translate("DialogSettings", u"View", None))
        self.label_6.setText(QCoreApplication.translate("DialogSettings", u"Alpha:", None))
        self.label_7.setText(QCoreApplication.translate("DialogSettings", u"Vertex Size:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_global), QCoreApplication.translate("DialogSettings", u"Global", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("DialogSettings", u"Current", None))
        self.label_8.setText(QCoreApplication.translate("DialogSettings", u"Project", None))
        self.label_9.setText(QCoreApplication.translate("DialogSettings", u"User", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("DialogSettings", u"Project", None))
        self.color_button.setText("")
        self.add_button.setText(QCoreApplication.translate("DialogSettings", u"Add new label", None))
        self.pushButton_import.setText(QCoreApplication.translate("DialogSettings", u"Import", None))
        self.pushButton_export.setText(QCoreApplication.translate("DialogSettings", u"Export", None))
        self.cancel_button.setText(QCoreApplication.translate("DialogSettings", u"Cancel", None))
        self.apply_button.setText(QCoreApplication.translate("DialogSettings", u"Apply", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("DialogSettings", u"Tab 2", None))
        self.btn_cancel.setText(QCoreApplication.translate("DialogSettings", u"Cancel", None))
        self.btn_apply.setText(QCoreApplication.translate("DialogSettings", u"Apply", None))
    # retranslateUi

