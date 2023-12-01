# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_file.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_ZDockFileContent(object):
    def setupUi(self, ZDockFileContent):
        if not ZDockFileContent.objectName():
            ZDockFileContent.setObjectName(u"ZDockFileContent")
        ZDockFileContent.resize(100, 300)
        self.verticalLayout = QVBoxLayout(ZDockFileContent)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.listw_files = QListWidget(ZDockFileContent)
        self.listw_files.setObjectName(u"listw_files")

        self.verticalLayout.addWidget(self.listw_files)

        self.widget_num = QWidget(ZDockFileContent)
        self.widget_num.setObjectName(u"widget_num")
        self.horizontalLayout = QHBoxLayout(self.widget_num)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.ledit_jump = QLineEdit(self.widget_num)
        self.ledit_jump.setObjectName(u"ledit_jump")

        self.horizontalLayout.addWidget(self.ledit_jump)

        self.label_current = QLabel(self.widget_num)
        self.label_current.setObjectName(u"label_current")

        self.horizontalLayout.addWidget(self.label_current)

        self.label = QLabel(self.widget_num)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.label_all = QLabel(self.widget_num)
        self.label_all.setObjectName(u"label_all")

        self.horizontalLayout.addWidget(self.label_all)


        self.verticalLayout.addWidget(self.widget_num)


        self.retranslateUi(ZDockFileContent)

        QMetaObject.connectSlotsByName(ZDockFileContent)
    # setupUi

    def retranslateUi(self, ZDockFileContent):
        ZDockFileContent.setWindowTitle(QCoreApplication.translate("ZDockFileContent", u"Form", None))
#if QT_CONFIG(tooltip)
        self.ledit_jump.setToolTip(QCoreApplication.translate("ZDockFileContent", u"Jump to the image. Input name or index.", None))
#endif // QT_CONFIG(tooltip)
        self.ledit_jump.setPlaceholderText(QCoreApplication.translate("ZDockFileContent", u"Jump to", None))
        self.label_current.setText("")
        self.label.setText(QCoreApplication.translate("ZDockFileContent", u"/", None))
        self.label_all.setText("")
    # retranslateUi

