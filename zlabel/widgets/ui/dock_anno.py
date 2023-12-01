# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_anno.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)
import icons_rc

class Ui_ZDockAnnotationContent(object):
    def setupUi(self, ZDockAnnotationContent):
        if not ZDockAnnotationContent.objectName():
            ZDockAnnotationContent.setObjectName(u"ZDockAnnotationContent")
        ZDockAnnotationContent.resize(228, 308)
        self.verticalLayout = QVBoxLayout(ZDockAnnotationContent)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.widget = QWidget(ZDockAnnotationContent)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.button_prev_group = QPushButton(self.widget)
        self.button_prev_group.setObjectName(u"button_prev_group")
        self.button_prev_group.setMaximumSize(QSize(25, 16777215))
        icon = QIcon()
        icon.addFile(u":/icon/icons/back.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.button_prev_group.setIcon(icon)

        self.horizontalLayout.addWidget(self.button_prev_group)

        self.button_next_group = QPushButton(self.widget)
        self.button_next_group.setObjectName(u"button_next_group")
        self.button_next_group.setMaximumSize(QSize(25, 16777215))
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/next.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.button_next_group.setIcon(icon1)

        self.horizontalLayout.addWidget(self.button_next_group)

        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(3, 0))
        self.label.setMaximumSize(QSize(3, 16777215))

        self.horizontalLayout.addWidget(self.label)


        self.verticalLayout.addWidget(self.widget)

        self.listWidget = QListWidget(ZDockAnnotationContent)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout.addWidget(self.listWidget)


        self.retranslateUi(ZDockAnnotationContent)

        QMetaObject.connectSlotsByName(ZDockAnnotationContent)
    # setupUi

    def retranslateUi(self, ZDockAnnotationContent):
        ZDockAnnotationContent.setWindowTitle(QCoreApplication.translate("ZDockAnnotationContent", u"Form", None))
        self.button_prev_group.setText("")
        self.button_next_group.setText("")
        self.label.setText("")
    # retranslateUi

