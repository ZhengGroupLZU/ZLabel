# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_about.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)
import icons_rc

class Ui_DialogAbout(object):
    def setupUi(self, DialogAbout):
        if not DialogAbout.objectName():
            DialogAbout.setObjectName(u"DialogAbout")
        DialogAbout.resize(550, 280)
        DialogAbout.setMinimumSize(QSize(550, 280))
        DialogAbout.setMaximumSize(QSize(550, 280))
        self.verticalLayout = QVBoxLayout(DialogAbout)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_2 = QLabel(DialogAbout)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(71)
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.label_4 = QLabel(DialogAbout)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMaximumSize(QSize(16777215, 40))
        font1 = QFont()
        font1.setPointSize(12)
        self.label_4.setFont(font1)
        self.label_4.setLayoutDirection(Qt.LeftToRight)
        self.label_4.setStyleSheet(u"color: rgb(133, 0, 0);")
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout.addWidget(self.label_4)


        self.retranslateUi(DialogAbout)

        QMetaObject.connectSlotsByName(DialogAbout)
    # setupUi

    def retranslateUi(self, DialogAbout):
        DialogAbout.setWindowTitle(QCoreApplication.translate("DialogAbout", u"about", None))
        self.label_2.setText(QCoreApplication.translate("DialogAbout", u"ZLabel", None))
        self.label_4.setText(QCoreApplication.translate("DialogAbout", u"ZLabel Copyright (C) 2023 Rainyl@ZhengGroup.", None))
    # retranslateUi

