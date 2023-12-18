# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_shortcuts.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QHBoxLayout,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)
import icons_rc

class Ui_DialogShortcut(object):
    def setupUi(self, DialogShortcut):
        if not DialogShortcut.objectName():
            DialogShortcut.setObjectName(u"DialogShortcut")
        DialogShortcut.resize(600, 300)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogShortcut.sizePolicy().hasHeightForWidth())
        DialogShortcut.setSizePolicy(sizePolicy)
        DialogShortcut.setMinimumSize(QSize(600, 300))
        DialogShortcut.setMaximumSize(QSize(600, 300))
        font = QFont()
        font.setKerning(True)
        DialogShortcut.setFont(font)
        self.verticalLayout = QVBoxLayout(DialogShortcut)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(DialogShortcut)
        self.widget.setObjectName(u"widget")
        self.widget.setMinimumSize(QSize(0, 60))
        self.widget.setMaximumSize(QSize(16777215, 60))
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setFamilies([u"Times New Roman"])
        font1.setPointSize(20)
        font1.setBold(False)
        font1.setItalic(False)
        font1.setKerning(True)
        self.label.setFont(font1)
        self.label.setTextFormat(Qt.AutoText)

        self.horizontalLayout.addWidget(self.label)


        self.verticalLayout.addWidget(self.widget)

        self.widget_2 = QWidget(DialogShortcut)
        self.widget_2.setObjectName(u"widget_2")
        font2 = QFont()
        font2.setFamilies([u"Times New Roman"])
        font2.setPointSize(12)
        font2.setKerning(True)
        self.widget_2.setFont(font2)
        self.gridLayout = QGridLayout(self.widget_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_7 = QLabel(self.widget_2)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMaximumSize(QSize(80, 16777215))
        self.label_7.setFont(font2)
        self.label_7.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_7, 0, 1, 1, 1)

        self.label_2 = QLabel(self.widget_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font2)

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_15 = QLabel(self.widget_2)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setMaximumSize(QSize(80, 16777215))
        self.label_15.setFont(font2)
        self.label_15.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_15, 5, 1, 1, 1)

        self.label_17 = QLabel(self.widget_2)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setMaximumSize(QSize(80, 16777215))
        self.label_17.setFont(font2)
        self.label_17.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_17, 0, 3, 1, 1)

        self.label_14 = QLabel(self.widget_2)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font2)

        self.gridLayout.addWidget(self.label_14, 6, 0, 1, 1)

        self.label_16 = QLabel(self.widget_2)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setMaximumSize(QSize(80, 16777215))
        self.label_16.setFont(font2)
        self.label_16.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_16, 6, 1, 1, 1)

        self.label_11 = QLabel(self.widget_2)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font2)

        self.gridLayout.addWidget(self.label_11, 6, 2, 1, 1)

        self.label_21 = QLabel(self.widget_2)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setMaximumSize(QSize(80, 16777215))
        self.label_21.setFont(font2)
        self.label_21.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_21, 6, 3, 1, 1)

        self.label_5 = QLabel(self.widget_2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font2)

        self.gridLayout.addWidget(self.label_5, 1, 2, 1, 1)

        self.label_4 = QLabel(self.widget_2)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font2)

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)

        self.label_9 = QLabel(self.widget_2)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font2)

        self.gridLayout.addWidget(self.label_9, 5, 2, 1, 1)

        self.label_6 = QLabel(self.widget_2)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font2)

        self.gridLayout.addWidget(self.label_6, 4, 0, 1, 1)

        self.label_10 = QLabel(self.widget_2)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font2)

        self.gridLayout.addWidget(self.label_10, 4, 2, 1, 1)

        self.label_18 = QLabel(self.widget_2)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setMaximumSize(QSize(80, 16777215))
        self.label_18.setFont(font2)
        self.label_18.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_18, 1, 3, 1, 1)

        self.label_19 = QLabel(self.widget_2)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setMaximumSize(QSize(80, 16777215))
        self.label_19.setFont(font2)
        self.label_19.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_19, 4, 3, 1, 1)

        self.label_13 = QLabel(self.widget_2)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setMaximumSize(QSize(80, 16777215))
        self.label_13.setFont(font2)
        self.label_13.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_13, 4, 1, 1, 1)

        self.label_12 = QLabel(self.widget_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMaximumSize(QSize(80, 16777215))
        self.label_12.setFont(font2)
        self.label_12.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_12, 1, 1, 1, 1)

        self.label_3 = QLabel(self.widget_2)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font2)

        self.gridLayout.addWidget(self.label_3, 0, 2, 1, 1)

        self.label_22 = QLabel(self.widget_2)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setFont(font2)

        self.gridLayout.addWidget(self.label_22, 2, 0, 1, 1)

        self.label_23 = QLabel(self.widget_2)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setFont(font2)
        self.label_23.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_23, 2, 1, 1, 1)

        self.label_25 = QLabel(self.widget_2)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setFont(font2)
        self.label_25.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_25, 2, 3, 1, 1)

        self.label_24 = QLabel(self.widget_2)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setFont(font2)

        self.gridLayout.addWidget(self.label_24, 2, 2, 1, 1)

        self.label_26 = QLabel(self.widget_2)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setFont(font2)

        self.gridLayout.addWidget(self.label_26, 3, 0, 1, 1)

        self.label_27 = QLabel(self.widget_2)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setFont(font2)
        self.label_27.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_27, 3, 1, 1, 1)

        self.label_8 = QLabel(self.widget_2)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font2)

        self.gridLayout.addWidget(self.label_8, 5, 0, 1, 1)

        self.label_28 = QLabel(self.widget_2)
        self.label_28.setObjectName(u"label_28")

        self.gridLayout.addWidget(self.label_28, 3, 2, 1, 1)

        self.label_29 = QLabel(self.widget_2)
        self.label_29.setObjectName(u"label_29")
        self.label_29.setFont(font2)
        self.label_29.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_29, 3, 3, 1, 1)

        self.label_20 = QLabel(self.widget_2)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setMaximumSize(QSize(80, 16777215))
        self.label_20.setFont(font2)
        self.label_20.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_20, 5, 3, 1, 1)

        self.label_30 = QLabel(self.widget_2)
        self.label_30.setObjectName(u"label_30")

        self.gridLayout.addWidget(self.label_30, 7, 0, 1, 1)

        self.label_31 = QLabel(self.widget_2)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setFont(font2)
        self.label_31.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_31, 7, 1, 1, 1)

        self.label_32 = QLabel(self.widget_2)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout.addWidget(self.label_32, 7, 2, 1, 1)

        self.label_33 = QLabel(self.widget_2)
        self.label_33.setObjectName(u"label_33")
        self.label_33.setFont(font2)
        self.label_33.setStyleSheet(u"color: rgb(133, 0, 0);")

        self.gridLayout.addWidget(self.label_33, 7, 3, 1, 1)


        self.verticalLayout.addWidget(self.widget_2)


        self.retranslateUi(DialogShortcut)

        QMetaObject.connectSlotsByName(DialogShortcut)
    # setupUi

    def retranslateUi(self, DialogShortcut):
        DialogShortcut.setWindowTitle(QCoreApplication.translate("DialogShortcut", u"help", None))
        self.label.setText(QCoreApplication.translate("DialogShortcut", u"Shortcut", None))
        self.label_7.setText(QCoreApplication.translate("DialogShortcut", u"A", None))
        self.label_2.setText(QCoreApplication.translate("DialogShortcut", u"Prev image", None))
        self.label_15.setText(QCoreApplication.translate("DialogShortcut", u"T", None))
        self.label_17.setText(QCoreApplication.translate("DialogShortcut", u"D", None))
        self.label_14.setText(QCoreApplication.translate("DialogShortcut", u"Bit map", None))
        self.label_16.setText(QCoreApplication.translate("DialogShortcut", u"Space", None))
        self.label_11.setText(QCoreApplication.translate("DialogShortcut", u"Zoom fit", None))
        self.label_21.setText(QCoreApplication.translate("DialogShortcut", u"F", None))
        self.label_5.setText(QCoreApplication.translate("DialogShortcut", u"Draw polygon", None))
        self.label_4.setText(QCoreApplication.translate("DialogShortcut", u"Segment anything", None))
        self.label_9.setText(QCoreApplication.translate("DialogShortcut", u"To bottom", None))
        self.label_6.setText(QCoreApplication.translate("DialogShortcut", u"Delete polygon", None))
        self.label_10.setText(QCoreApplication.translate("DialogShortcut", u"Save annotation", None))
        self.label_18.setText(QCoreApplication.translate("DialogShortcut", u"C", None))
        self.label_19.setText(QCoreApplication.translate("DialogShortcut", u"S", None))
        self.label_13.setText(QCoreApplication.translate("DialogShortcut", u"Del", None))
        self.label_12.setText(QCoreApplication.translate("DialogShortcut", u"Q", None))
        self.label_3.setText(QCoreApplication.translate("DialogShortcut", u"Next image", None))
        self.label_22.setText(QCoreApplication.translate("DialogShortcut", u"Backspace", None))
        self.label_23.setText(QCoreApplication.translate("DialogShortcut", u"Z", None))
        self.label_25.setText(QCoreApplication.translate("DialogShortcut", u"E", None))
        self.label_24.setText(QCoreApplication.translate("DialogShortcut", u"Annotate finish", None))
        self.label_26.setText(QCoreApplication.translate("DialogShortcut", u"Annotate cancel", None))
        self.label_27.setText(QCoreApplication.translate("DialogShortcut", u"Esc", None))
        self.label_8.setText(QCoreApplication.translate("DialogShortcut", u"To top", None))
        self.label_28.setText(QCoreApplication.translate("DialogShortcut", u"Polygons Visible", None))
        self.label_29.setText(QCoreApplication.translate("DialogShortcut", u"V", None))
        self.label_20.setText(QCoreApplication.translate("DialogShortcut", u"B", None))
        self.label_30.setText(QCoreApplication.translate("DialogShortcut", u"Prev group", None))
        self.label_31.setText(QCoreApplication.translate("DialogShortcut", u"Tab", None))
        self.label_32.setText(QCoreApplication.translate("DialogShortcut", u"Next group", None))
        self.label_33.setText(QCoreApplication.translate("DialogShortcut", u"`", None))
    # retranslateUi

