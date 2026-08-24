# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_export.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QTextBrowser,
    QWidget)

class Ui_DialogExport(object):
    def setupUi(self, DialogExport):
        if not DialogExport.objectName():
            DialogExport.setObjectName(u"DialogExport")
        DialogExport.resize(520, 360)
        self.gridLayout = QGridLayout(DialogExport)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_format = QLabel(DialogExport)
        self.label_format.setObjectName(u"label_format")

        self.gridLayout.addWidget(self.label_format, 0, 0, 1, 1)

        self.cmbox_format = QComboBox(DialogExport)
        self.cmbox_format.addItem("")
        self.cmbox_format.addItem("")
        self.cmbox_format.setObjectName(u"cmbox_format")

        self.gridLayout.addWidget(self.cmbox_format, 0, 1, 1, 1)

        self.label_task = QLabel(DialogExport)
        self.label_task.setObjectName(u"label_task")

        self.gridLayout.addWidget(self.label_task, 1, 0, 1, 1)

        self.cmbox_task = QComboBox(DialogExport)
        self.cmbox_task.addItem("")
        self.cmbox_task.addItem("")
        self.cmbox_task.addItem("")
        self.cmbox_task.setObjectName(u"cmbox_task")

        self.gridLayout.addWidget(self.cmbox_task, 1, 1, 1, 1)

        self.label_output = QLabel(DialogExport)
        self.label_output.setObjectName(u"label_output")

        self.gridLayout.addWidget(self.label_output, 2, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.ledit_output = QLineEdit(DialogExport)
        self.ledit_output.setObjectName(u"ledit_output")

        self.horizontalLayout.addWidget(self.ledit_output)

        self.btn_output = QPushButton(DialogExport)
        self.btn_output.setObjectName(u"btn_output")

        self.horizontalLayout.addWidget(self.btn_output)


        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)

        self.textBrowser = QTextBrowser(DialogExport)
        self.textBrowser.setObjectName(u"textBrowser")

        self.gridLayout.addWidget(self.textBrowser, 3, 0, 1, 2)

        self.progressBar = QProgressBar(DialogExport)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)

        self.gridLayout.addWidget(self.progressBar, 4, 0, 1, 2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btn_cancel = QPushButton(DialogExport)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.horizontalLayout_2.addWidget(self.btn_cancel)

        self.btn_export = QPushButton(DialogExport)
        self.btn_export.setObjectName(u"btn_export")

        self.horizontalLayout_2.addWidget(self.btn_export)


        self.gridLayout.addLayout(self.horizontalLayout_2, 5, 1, 1, 1)


        self.retranslateUi(DialogExport)

        QMetaObject.connectSlotsByName(DialogExport)
    # setupUi

    def retranslateUi(self, DialogExport):
        DialogExport.setWindowTitle(QCoreApplication.translate("DialogExport", u"Export Dataset", None))
        self.label_format.setText(QCoreApplication.translate("DialogExport", u"Format:", None))
        self.cmbox_format.setItemText(0, QCoreApplication.translate("DialogExport", u"COCO", None))
        self.cmbox_format.setItemText(1, QCoreApplication.translate("DialogExport", u"Ultralytics YOLO", None))

        self.label_task.setText(QCoreApplication.translate("DialogExport", u"Task:", None))
        self.cmbox_task.setItemText(0, QCoreApplication.translate("DialogExport", u"Object Detection", None))
        self.cmbox_task.setItemText(1, QCoreApplication.translate("DialogExport", u"Segmentation", None))
        self.cmbox_task.setItemText(2, QCoreApplication.translate("DialogExport", u"Keypoint Detection", None))

        self.label_output.setText(QCoreApplication.translate("DialogExport", u"Output:", None))
        self.ledit_output.setPlaceholderText(QCoreApplication.translate("DialogExport", u"COCO json path / YOLO output directory", None))
        self.btn_output.setText(QCoreApplication.translate("DialogExport", u"Browse...", None))
        self.btn_cancel.setText(QCoreApplication.translate("DialogExport", u"Cancel", None))
        self.btn_export.setText(QCoreApplication.translate("DialogExport", u"Export", None))
    # retranslateUi

