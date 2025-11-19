# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_info.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QSizePolicy, QVBoxLayout, QWidget)
import icons_rc

class Ui_ZDockInfoContent(object):
    def setupUi(self, ZDockInfoContent):
        if not ZDockInfoContent.objectName():
            ZDockInfoContent.setObjectName(u"ZDockInfoContent")
        ZDockInfoContent.resize(316, 86)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ZDockInfoContent.sizePolicy().hasHeightForWidth())
        ZDockInfoContent.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(ZDockInfoContent)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_img_width = QLabel(ZDockInfoContent)
        self.label_img_width.setObjectName(u"label_img_width")
        self.label_img_width.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.label_img_width)

        self.label = QLabel(ZDockInfoContent)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMaximumSize(QSize(10, 16777215))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.label)

        self.label_img_height = QLabel(ZDockInfoContent)
        self.label_img_height.setObjectName(u"label_img_height")

        self.horizontalLayout.addWidget(self.label_img_height)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_5 = QLabel(ZDockInfoContent)
        self.label_5.setObjectName(u"label_5")
        sizePolicy1.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.label_5)

        self.ledit_anno_note = QPlainTextEdit(ZDockInfoContent)
        self.ledit_anno_note.setObjectName(u"ledit_anno_note")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.ledit_anno_note.sizePolicy().hasHeightForWidth())
        self.ledit_anno_note.setSizePolicy(sizePolicy2)
        self.ledit_anno_note.setMinimumSize(QSize(0, 40))
        self.ledit_anno_note.setMaximumSize(QSize(16777215, 40))

        self.horizontalLayout_2.addWidget(self.ledit_anno_note)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)


        self.retranslateUi(ZDockInfoContent)

        QMetaObject.connectSlotsByName(ZDockInfoContent)
    # setupUi

    def retranslateUi(self, ZDockInfoContent):
        ZDockInfoContent.setWindowTitle(QCoreApplication.translate("ZDockInfoContent", u"DockInfo", None))
        self.label_img_width.setText("")
        self.label.setText(QCoreApplication.translate("ZDockInfoContent", u"\u00d7", None))
        self.label_img_height.setText("")
        self.label_5.setText(QCoreApplication.translate("ZDockInfoContent", u"Note:", None))
        self.ledit_anno_note.setPlaceholderText(QCoreApplication.translate("ZDockInfoContent", u"add extra image note here", None))
    # retranslateUi

