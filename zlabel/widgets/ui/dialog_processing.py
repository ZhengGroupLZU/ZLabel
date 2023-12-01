# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_processing.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QProgressBar,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_DialogProcessing(object):
    def setupUi(self, DialogProcessing):
        if not DialogProcessing.objectName():
            DialogProcessing.setObjectName(u"DialogProcessing")
        DialogProcessing.resize(338, 71)
        self.verticalLayout = QVBoxLayout(DialogProcessing)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.progressBar = QProgressBar(DialogProcessing)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)

        self.verticalLayout.addWidget(self.progressBar)

        self.label = QLabel(DialogProcessing)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)


        self.retranslateUi(DialogProcessing)

        QMetaObject.connectSlotsByName(DialogProcessing)
    # setupUi

    def retranslateUi(self, DialogProcessing):
        DialogProcessing.setWindowTitle(QCoreApplication.translate("DialogProcessing", u"Processing", None))
        self.progressBar.setFormat(QCoreApplication.translate("DialogProcessing", u"%p%", None))
        self.label.setText(QCoreApplication.translate("DialogProcessing", u"Loading...", None))
    # retranslateUi

