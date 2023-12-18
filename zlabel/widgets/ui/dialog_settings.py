# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QTabWidget, QWidget)
import icons_rc

class Ui_DialogSettings(object):
    def setupUi(self, DialogSettings):
        if not DialogSettings.objectName():
            DialogSettings.setObjectName(u"DialogSettings")
        DialogSettings.resize(644, 414)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(12)
        DialogSettings.setFont(font)
        self.gridLayout_5 = QGridLayout(DialogSettings)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.tabWidget = QTabWidget(DialogSettings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_global = QWidget()
        self.tab_global.setObjectName(u"tab_global")
        self.gridLayout_3 = QGridLayout(self.tab_global)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.groupBox_2 = QGroupBox(self.tab_global)
        self.groupBox_2.setObjectName(u"groupBox_2")
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

        self.label_12 = QLabel(self.groupBox_2)
        self.label_12.setObjectName(u"label_12")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_12)

        self.btn_select_color = QPushButton(self.groupBox_2)
        self.btn_select_color.setObjectName(u"btn_select_color")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.btn_select_color)


        self.gridLayout.addLayout(self.formLayout_2, 0, 0, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox_2, 0, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.groupBox = QGroupBox(self.tab_global)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_4.addWidget(self.label_2, 1, 0, 1, 1)

        self.ledit_password = QLineEdit(self.groupBox)
        self.ledit_password.setObjectName(u"ledit_password")

        self.gridLayout_4.addWidget(self.ledit_password, 3, 1, 1, 1)

        self.ledit_urlprefix = QLineEdit(self.groupBox)
        self.ledit_urlprefix.setObjectName(u"ledit_urlprefix")

        self.gridLayout_4.addWidget(self.ledit_urlprefix, 1, 1, 1, 1)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_4.addWidget(self.label_5, 3, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_4.addWidget(self.label_4, 2, 0, 1, 1)

        self.ledit_username = QLineEdit(self.groupBox)
        self.ledit_username.setObjectName(u"ledit_username")

        self.gridLayout_4.addWidget(self.ledit_username, 2, 1, 1, 1)

        self.ledit_host = QLineEdit(self.groupBox)
        self.ledit_host.setObjectName(u"ledit_host")

        self.gridLayout_4.addWidget(self.ledit_host, 0, 1, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout_4, 0, 0, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 1)

        self.groupBox_3 = QGroupBox(self.tab_global)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_7 = QGridLayout(self.groupBox_3)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.ledit_encoder = QLineEdit(self.groupBox_3)
        self.ledit_encoder.setObjectName(u"ledit_encoder")

        self.gridLayout_7.addWidget(self.ledit_encoder, 1, 1, 1, 1)

        self.label_7 = QLabel(self.groupBox_3)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_7.addWidget(self.label_7, 2, 0, 1, 1)

        self.btn_encoder = QPushButton(self.groupBox_3)
        self.btn_encoder.setObjectName(u"btn_encoder")
        icon = QIcon()
        icon.addFile(u":/icon/icons/folder-open.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_encoder.setIcon(icon)

        self.gridLayout_7.addWidget(self.btn_encoder, 1, 2, 1, 1)

        self.label_3 = QLabel(self.groupBox_3)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_7.addWidget(self.label_3, 1, 0, 1, 1)

        self.btn_decoder = QPushButton(self.groupBox_3)
        self.btn_decoder.setObjectName(u"btn_decoder")
        self.btn_decoder.setIcon(icon)

        self.gridLayout_7.addWidget(self.btn_decoder, 2, 2, 1, 1)

        self.ledit_model_api = QLineEdit(self.groupBox_3)
        self.ledit_model_api.setObjectName(u"ledit_model_api")

        self.gridLayout_7.addWidget(self.ledit_model_api, 0, 1, 1, 2)

        self.ledit_decoder = QLineEdit(self.groupBox_3)
        self.ledit_decoder.setObjectName(u"ledit_decoder")

        self.gridLayout_7.addWidget(self.ledit_decoder, 2, 1, 1, 1)

        self.label_8 = QLabel(self.groupBox_3)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_7.addWidget(self.label_8, 0, 0, 1, 1)

        self.label_11 = QLabel(self.groupBox_3)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_7.addWidget(self.label_11, 3, 0, 1, 1)

        self.cmbox_loglevel = QComboBox(self.groupBox_3)
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.setObjectName(u"cmbox_loglevel")

        self.gridLayout_7.addWidget(self.cmbox_loglevel, 3, 1, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox_3, 1, 0, 1, 2)

        self.tabWidget.addTab(self.tab_global, "")
        self.tab_project = QWidget()
        self.tab_project.setObjectName(u"tab_project")
        self.gridLayoutWidget_2 = QWidget(self.tab_project)
        self.gridLayoutWidget_2.setObjectName(u"gridLayoutWidget_2")
        self.gridLayoutWidget_2.setGeometry(QRect(10, 10, 581, 171))
        self.gridLayout_6 = QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.ledit_projname = QLineEdit(self.gridLayoutWidget_2)
        self.ledit_projname.setObjectName(u"ledit_projname")

        self.gridLayout_6.addWidget(self.ledit_projname, 0, 1, 1, 2)

        self.label_9 = QLabel(self.gridLayoutWidget_2)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_6.addWidget(self.label_9, 0, 0, 1, 1)

        self.label_10 = QLabel(self.gridLayoutWidget_2)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_6.addWidget(self.label_10, 1, 0, 1, 1)

        self.ledit_prjdescrip = QLineEdit(self.gridLayoutWidget_2)
        self.ledit_prjdescrip.setObjectName(u"ledit_prjdescrip")

        self.gridLayout_6.addWidget(self.ledit_prjdescrip, 1, 1, 1, 1)

        self.tabWidget.addTab(self.tab_project, "")

        self.gridLayout_5.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.btn_cancel = QPushButton(DialogSettings)
        self.btn_cancel.setObjectName(u"btn_cancel")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/close-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_cancel.setIcon(icon1)

        self.horizontalLayout_4.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton(DialogSettings)
        self.btn_apply.setObjectName(u"btn_apply")
        icon2 = QIcon()
        icon2.addFile(u":/icon/icons/check-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_apply.setIcon(icon2)

        self.horizontalLayout_4.addWidget(self.btn_apply)


        self.gridLayout_5.addLayout(self.horizontalLayout_4, 1, 0, 1, 1)


        self.retranslateUi(DialogSettings)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DialogSettings)
    # setupUi

    def retranslateUi(self, DialogSettings):
        DialogSettings.setWindowTitle(QCoreApplication.translate("DialogSettings", u"Setting", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("DialogSettings", u"View", None))
        self.label_6.setText(QCoreApplication.translate("DialogSettings", u"Alpha:", None))
        self.label_12.setText(QCoreApplication.translate("DialogSettings", u"Color:", None))
        self.btn_select_color.setText("")
        self.groupBox.setTitle(QCoreApplication.translate("DialogSettings", u"API", None))
        self.label_2.setText(QCoreApplication.translate("DialogSettings", u"URL Prefix:", None))
        self.label_5.setText(QCoreApplication.translate("DialogSettings", u"Password:", None))
        self.label_4.setText(QCoreApplication.translate("DialogSettings", u"User Name:", None))
        self.label.setText(QCoreApplication.translate("DialogSettings", u"Host:", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("DialogSettings", u"Model", None))
        self.label_7.setText(QCoreApplication.translate("DialogSettings", u"Decoder:", None))
        self.btn_encoder.setText(QCoreApplication.translate("DialogSettings", u"Select", None))
        self.label_3.setText(QCoreApplication.translate("DialogSettings", u"Encoder:", None))
        self.btn_decoder.setText(QCoreApplication.translate("DialogSettings", u"Select", None))
        self.label_8.setText(QCoreApplication.translate("DialogSettings", u"API:", None))
        self.label_11.setText(QCoreApplication.translate("DialogSettings", u"LogLevel:", None))
        self.cmbox_loglevel.setItemText(0, QCoreApplication.translate("DialogSettings", u"DEBUG", None))
        self.cmbox_loglevel.setItemText(1, QCoreApplication.translate("DialogSettings", u"INFO", None))
        self.cmbox_loglevel.setItemText(2, QCoreApplication.translate("DialogSettings", u"WARNING", None))
        self.cmbox_loglevel.setItemText(3, QCoreApplication.translate("DialogSettings", u"ERROR", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_global), QCoreApplication.translate("DialogSettings", u"Global", None))
        self.label_9.setText(QCoreApplication.translate("DialogSettings", u"Name:", None))
        self.label_10.setText(QCoreApplication.translate("DialogSettings", u"Description:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_project), QCoreApplication.translate("DialogSettings", u"Project", None))
        self.btn_cancel.setText(QCoreApplication.translate("DialogSettings", u"Cancel", None))
        self.btn_apply.setText(QCoreApplication.translate("DialogSettings", u"Apply", None))
    # retranslateUi

