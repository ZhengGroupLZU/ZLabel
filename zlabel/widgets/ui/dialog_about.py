# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_about.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)
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
        self.widget = QWidget(DialogAbout)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget_2 = QWidget(self.widget)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setMaximumSize(QSize(16777215, 40))
        self.horizontalLayout = QHBoxLayout(self.widget_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.widget_2)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(16777215, 50))
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(20)
        self.label.setFont(font)

        self.horizontalLayout.addWidget(self.label)


        self.verticalLayout_2.addWidget(self.widget_2)

        self.widget_3 = QWidget(self.widget)
        self.widget_3.setObjectName(u"widget_3")
        font1 = QFont()
        font1.setFamilies([u"Times New Roman"])
        font1.setPointSize(12)
        self.widget_3.setFont(font1)
        self.verticalLayout_3 = QVBoxLayout(self.widget_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_2 = QLabel(self.widget_3)
        self.label_2.setObjectName(u"label_2")
        font2 = QFont()
        font2.setFamilies([u"Times New Roman"])
        font2.setPointSize(18)
        self.label_2.setFont(font2)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_2)

        self.label_4 = QLabel(self.widget_3)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMaximumSize(QSize(16777215, 40))
        self.label_4.setLayoutDirection(Qt.LeftToRight)
        self.label_4.setStyleSheet(u"color: rgb(133, 0, 0);")
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_3.addWidget(self.label_4)


        self.verticalLayout_2.addWidget(self.widget_3)


        self.verticalLayout.addWidget(self.widget)


        self.retranslateUi(DialogAbout)

        QMetaObject.connectSlotsByName(DialogAbout)
    # setupUi

    def retranslateUi(self, DialogAbout):
        DialogAbout.setWindowTitle(QCoreApplication.translate("DialogAbout", u"about", None))
        self.label.setText(QCoreApplication.translate("DialogAbout", u"About", None))
        self.label_2.setText(QCoreApplication.translate("DialogAbout", u"ISAT with Segment anything.", None))
        self.label_4.setText(QCoreApplication.translate("DialogAbout", u"ISAT Copyright (C) 2022 yatengLG.\n"
"https://github.com/yatengLG/ISAT_with_segment_anything", None))
    # retranslateUi

