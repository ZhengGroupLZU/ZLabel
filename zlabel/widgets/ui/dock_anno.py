# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_anno.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHeaderView, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
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
        self.listWidget = QTreeWidget(ZDockAnnotationContent)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1")
        self.listWidget.setHeaderItem(__qtreewidgetitem)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listWidget.setHeaderHidden(True)

        self.verticalLayout.addWidget(self.listWidget)


        self.retranslateUi(ZDockAnnotationContent)

        QMetaObject.connectSlotsByName(ZDockAnnotationContent)
    # setupUi

    def retranslateUi(self, ZDockAnnotationContent):
        ZDockAnnotationContent.setWindowTitle(QCoreApplication.translate("ZDockAnnotationContent", u"Form", None))
    # retranslateUi

