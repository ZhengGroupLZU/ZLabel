# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_label.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QLineEdit,
    QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

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
        self.listw_labels.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listw_labels.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.listw_labels)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, -1, 0)
        self.btn_decrease = QPushButton(ZDockLabelContent)
        self.btn_decrease.setObjectName(u"btn_decrease")
        self.btn_decrease.setMaximumSize(QSize(20, 16777215))

        self.horizontalLayout.addWidget(self.btn_decrease)

        self.ledit_add_label = QLineEdit(ZDockLabelContent)
        self.ledit_add_label.setObjectName(u"ledit_add_label")
        self.ledit_add_label.setMaximumSize(QSize(16777215, 16777215))
        self.ledit_add_label.setLayoutDirection(Qt.LeftToRight)
        self.ledit_add_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.ledit_add_label)

        self.btn_increase = QPushButton(ZDockLabelContent)
        self.btn_increase.setObjectName(u"btn_increase")
        self.btn_increase.setMaximumSize(QSize(20, 16777215))

        self.horizontalLayout.addWidget(self.btn_increase)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(ZDockLabelContent)

        QMetaObject.connectSlotsByName(ZDockLabelContent)
    # setupUi

    def retranslateUi(self, ZDockLabelContent):
        ZDockLabelContent.setWindowTitle(QCoreApplication.translate("ZDockLabelContent", u"Form", None))
#if QT_CONFIG(statustip)
        self.btn_decrease.setStatusTip(QCoreApplication.translate("ZDockLabelContent", u"Current group -", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(whatsthis)
        self.btn_decrease.setWhatsThis(QCoreApplication.translate("ZDockLabelContent", u"Current group -", None))
#endif // QT_CONFIG(whatsthis)
        self.btn_decrease.setText(QCoreApplication.translate("ZDockLabelContent", u"-", None))
#if QT_CONFIG(statustip)
        self.ledit_add_label.setStatusTip(QCoreApplication.translate("ZDockLabelContent", u"Current group", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(whatsthis)
        self.ledit_add_label.setWhatsThis(QCoreApplication.translate("ZDockLabelContent", u"Current group", None))
#endif // QT_CONFIG(whatsthis)
        self.ledit_add_label.setText("")
#if QT_CONFIG(statustip)
        self.btn_increase.setStatusTip(QCoreApplication.translate("ZDockLabelContent", u"Current group +", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(whatsthis)
        self.btn_increase.setWhatsThis(QCoreApplication.translate("ZDockLabelContent", u"Current group +", None))
#endif // QT_CONFIG(whatsthis)
        self.btn_increase.setText(QCoreApplication.translate("ZDockLabelContent", u"+", None))
    # retranslateUi

