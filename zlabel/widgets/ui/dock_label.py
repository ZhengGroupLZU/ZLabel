# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_label.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QListWidgetItem, QSizePolicy,
    QVBoxLayout, QWidget)

from zlabel.widgets.zwidgets import ZListWidget

class Ui_ZDockLabelContent(object):
    def setupUi(self, ZDockLabelContent):
        if not ZDockLabelContent.objectName():
            ZDockLabelContent.setObjectName(u"ZDockLabelContent")
        ZDockLabelContent.resize(106, 308)
        self.verticalLayout = QVBoxLayout(ZDockLabelContent)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.listw_labels = ZListWidget(ZDockLabelContent)
        self.listw_labels.setObjectName(u"listw_labels")
        self.listw_labels.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.listw_labels.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.verticalLayout.addWidget(self.listw_labels)


        self.retranslateUi(ZDockLabelContent)

        QMetaObject.connectSlotsByName(ZDockLabelContent)
    # setupUi

    def retranslateUi(self, ZDockLabelContent):
        ZDockLabelContent.setWindowTitle(QCoreApplication.translate("ZDockLabelContent", u"Form", None))
    # retranslateUi

