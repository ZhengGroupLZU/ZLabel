# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_import.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QTextBrowser,
    QTextEdit, QVBoxLayout, QWidget)
import icons_rc

class Ui_DialogImport(object):
    def setupUi(self, DialogImport):
        if not DialogImport.objectName():
            DialogImport.setObjectName(u"DialogImport")
        DialogImport.setWindowModality(Qt.NonModal)
        DialogImport.resize(600, 257)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(12)
        DialogImport.setFont(font)
        DialogImport.setSizeGripEnabled(False)
        DialogImport.setModal(False)
        self.verticalLayout = QVBoxLayout(DialogImport)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(DialogImport)
        self.widget.setObjectName(u"widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton_save_root = QPushButton(self.widget)
        self.pushButton_save_root.setObjectName(u"pushButton_save_root")

        self.gridLayout.addWidget(self.pushButton_save_root, 3, 1, 1, 1)

        self.pushButton_label_path = QPushButton(self.widget)
        self.pushButton_label_path.setObjectName(u"pushButton_label_path")

        self.gridLayout.addWidget(self.pushButton_label_path, 2, 1, 1, 1)

        self.lineEdit_save_root = QLineEdit(self.widget)
        self.lineEdit_save_root.setObjectName(u"lineEdit_save_root")
        self.lineEdit_save_root.setEnabled(True)
        self.lineEdit_save_root.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_save_root, 3, 0, 1, 1)

        self.lineEdit_label_path = QLineEdit(self.widget)
        self.lineEdit_label_path.setObjectName(u"lineEdit_label_path")
        self.lineEdit_label_path.setEnabled(True)
        self.lineEdit_label_path.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_label_path, 2, 0, 1, 1)


        self.verticalLayout.addWidget(self.widget)

        self.widget_3 = QWidget(DialogImport)
        self.widget_3.setObjectName(u"widget_3")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.checkBox_keepcrowd = QCheckBox(self.widget_3)
        self.checkBox_keepcrowd.setObjectName(u"checkBox_keepcrowd")

        self.horizontalLayout_2.addWidget(self.checkBox_keepcrowd)


        self.verticalLayout.addWidget(self.widget_3)

        self.widget_4 = QWidget(DialogImport)
        self.widget_4.setObjectName(u"widget_4")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.widget_4)

        self.textBrowser = QTextBrowser(DialogImport)
        self.textBrowser.setObjectName(u"textBrowser")
        font1 = QFont()
        font1.setFamilies([u"\u5b8b\u4f53"])
        font1.setPointSize(12)
        self.textBrowser.setFont(font1)
        self.textBrowser.setLineWrapMode(QTextEdit.NoWrap)

        self.verticalLayout.addWidget(self.textBrowser)

        self.progressBar = QProgressBar(DialogImport)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)

        self.verticalLayout.addWidget(self.progressBar)

        self.widget_2 = QWidget(DialogImport)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout = QHBoxLayout(self.widget_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.widget_2)
        self.label.setObjectName(u"label")
        self.label.setFont(font)
        self.label.setStyleSheet(u"color: rgb(255, 0, 0);")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_cancel = QPushButton(self.widget_2)
        self.pushButton_cancel.setObjectName(u"pushButton_cancel")
        icon = QIcon()
        icon.addFile(u":/icon/icons/close-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_cancel.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_cancel)

        self.pushButton_apply = QPushButton(self.widget_2)
        self.pushButton_apply.setObjectName(u"pushButton_apply")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/check-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_apply.setIcon(icon1)

        self.horizontalLayout.addWidget(self.pushButton_apply)


        self.verticalLayout.addWidget(self.widget_2)


        self.retranslateUi(DialogImport)

        QMetaObject.connectSlotsByName(DialogImport)
    # setupUi

    def retranslateUi(self, DialogImport):
        DialogImport.setWindowTitle(QCoreApplication.translate("DialogImport", u"Import", None))
        self.pushButton_save_root.setText(QCoreApplication.translate("DialogImport", u"Save root", None))
        self.pushButton_label_path.setText(QCoreApplication.translate("DialogImport", u"Json path", None))
        self.lineEdit_save_root.setPlaceholderText(QCoreApplication.translate("DialogImport", u"ISAT jsons save root", None))
        self.lineEdit_label_path.setPlaceholderText(QCoreApplication.translate("DialogImport", u"COCO json path", None))
        self.checkBox_keepcrowd.setText(QCoreApplication.translate("DialogImport", u"Keep crowd", None))
        self.label.setText(QCoreApplication.translate("DialogImport", u"Convert COCO json to ISAT jsons.All layer attr is 1.", None))
        self.pushButton_cancel.setText(QCoreApplication.translate("DialogImport", u"cancel", None))
        self.pushButton_apply.setText(QCoreApplication.translate("DialogImport", u"convert", None))
    # retranslateUi

