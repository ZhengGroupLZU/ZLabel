# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_export.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QTextBrowser, QTextEdit,
    QVBoxLayout, QWidget)
import icons_rc

class Ui_DialogExport(object):
    def setupUi(self, DialogExport):
        if not DialogExport.objectName():
            DialogExport.setObjectName(u"DialogExport")
        DialogExport.setWindowModality(Qt.NonModal)
        DialogExport.resize(600, 227)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(12)
        DialogExport.setFont(font)
        DialogExport.setSizeGripEnabled(False)
        DialogExport.setModal(False)
        self.verticalLayout = QVBoxLayout(DialogExport)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(DialogExport)
        self.widget.setObjectName(u"widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton_save_path = QPushButton(self.widget)
        self.pushButton_save_path.setObjectName(u"pushButton_save_path")

        self.gridLayout.addWidget(self.pushButton_save_path, 3, 1, 1, 1)

        self.pushButton_label_root = QPushButton(self.widget)
        self.pushButton_label_root.setObjectName(u"pushButton_label_root")

        self.gridLayout.addWidget(self.pushButton_label_root, 2, 1, 1, 1)

        self.lineEdit_save_path = QLineEdit(self.widget)
        self.lineEdit_save_path.setObjectName(u"lineEdit_save_path")
        self.lineEdit_save_path.setEnabled(True)
        self.lineEdit_save_path.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_save_path, 3, 0, 1, 1)

        self.lineEdit_label_root = QLineEdit(self.widget)
        self.lineEdit_label_root.setObjectName(u"lineEdit_label_root")
        self.lineEdit_label_root.setEnabled(True)
        self.lineEdit_label_root.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEdit_label_root, 2, 0, 1, 1)


        self.verticalLayout.addWidget(self.widget)

        self.textBrowser = QTextBrowser(DialogExport)
        self.textBrowser.setObjectName(u"textBrowser")
        font1 = QFont()
        font1.setFamilies([u"\u5b8b\u4f53"])
        font1.setPointSize(12)
        self.textBrowser.setFont(font1)
        self.textBrowser.setLineWrapMode(QTextEdit.NoWrap)

        self.verticalLayout.addWidget(self.textBrowser)

        self.widget_3 = QWidget(DialogExport)
        self.widget_3.setObjectName(u"widget_3")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.widget_3)

        self.progressBar = QProgressBar(DialogExport)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)

        self.verticalLayout.addWidget(self.progressBar)

        self.widget_2 = QWidget(DialogExport)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout = QHBoxLayout(self.widget_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.widget_2)
        self.label.setObjectName(u"label")
        self.label.setFont(font)
        self.label.setStyleSheet(u"color: rgb(255, 0, 0);")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_cancel = QPushButton(self.widget_2)
        self.pushButton_cancel.setObjectName(u"pushButton_cancel")
        icon = QIcon()
        icon.addFile(u":/icon/icons/close-one.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_cancel.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_cancel)

        self.pushButton_apply = QPushButton(self.widget_2)
        self.pushButton_apply.setObjectName(u"pushButton_apply")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/check-one.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_apply.setIcon(icon1)

        self.horizontalLayout.addWidget(self.pushButton_apply)


        self.verticalLayout.addWidget(self.widget_2)


        self.retranslateUi(DialogExport)

        QMetaObject.connectSlotsByName(DialogExport)
    # setupUi

    def retranslateUi(self, DialogExport):
        DialogExport.setWindowTitle(QCoreApplication.translate("DialogExport", u"Export", None))
        self.pushButton_save_path.setText(QCoreApplication.translate("DialogExport", u"Save path", None))
        self.pushButton_label_root.setText(QCoreApplication.translate("DialogExport", u"Jsons root", None))
        self.lineEdit_save_path.setPlaceholderText(QCoreApplication.translate("DialogExport", u"COCO json save path", None))
        self.lineEdit_label_root.setPlaceholderText(QCoreApplication.translate("DialogExport", u"ISAT jsons root", None))
        self.textBrowser.setHtml(QCoreApplication.translate("DialogExport", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'\u5b8b\u4f53'; font-size:12pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Times New Roman';\"><br /></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("DialogExport", u"Convert ISAT jsons to COCO json.The layer attr will be lost.", None))
        self.pushButton_cancel.setText(QCoreApplication.translate("DialogExport", u"cancel", None))
        self.pushButton_apply.setText(QCoreApplication.translate("DialogExport", u"convert", None))
    # retranslateUi

