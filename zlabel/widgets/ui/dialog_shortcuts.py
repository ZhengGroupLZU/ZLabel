# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_shortcuts.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QGroupBox,
    QKeySequenceEdit, QLabel, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)
import icons_rc

class Ui_DialogShortcut(object):
    def setupUi(self, DialogShortcut):
        if not DialogShortcut.objectName():
            DialogShortcut.setObjectName(u"DialogShortcut")
        DialogShortcut.resize(709, 585)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogShortcut.sizePolicy().hasHeightForWidth())
        DialogShortcut.setSizePolicy(sizePolicy)
        font = QFont()
        font.setKerning(True)
        DialogShortcut.setFont(font)
        self.gridLayout_6 = QGridLayout(DialogShortcut)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.label = QLabel(DialogShortcut)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setFamilies([u"Times New Roman"])
        font1.setPointSize(20)
        font1.setBold(False)
        font1.setItalic(False)
        font1.setKerning(True)
        self.label.setFont(font1)
        self.label.setTextFormat(Qt.TextFormat.AutoText)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_6.addWidget(self.label, 0, 0, 1, 1)

        self.scrollArea = QScrollArea(DialogShortcut)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 689, 529))
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_3 = QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.keySequenceEdit = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit.setObjectName(u"keySequenceEdit")
        self.keySequenceEdit.setEnabled(False)
        self.keySequenceEdit.setKeySequence(u"Ctrl+Z")
        self.keySequenceEdit.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit, 0, 3, 1, 1)

        self.label_32 = QLabel(self.groupBox)
        self.label_32.setObjectName(u"label_32")
        self.label_32.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_32, 5, 0, 1, 1)

        self.label_34 = QLabel(self.groupBox)
        self.label_34.setObjectName(u"label_34")
        self.label_34.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_34, 3, 0, 1, 1)

        self.keySequenceEdit_10 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_10.setObjectName(u"keySequenceEdit_10")
        self.keySequenceEdit_10.setEnabled(False)
        self.keySequenceEdit_10.setKeySequence(u"Del")
        self.keySequenceEdit_10.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_10, 4, 1, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        font2 = QFont()
        font2.setFamilies([u"Times New Roman"])
        font2.setPointSize(12)
        font2.setKerning(True)
        self.label_4.setFont(font2)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_4, 2, 0, 1, 1)

        self.label_40 = QLabel(self.groupBox)
        self.label_40.setObjectName(u"label_40")
        self.label_40.setFont(font2)
        self.label_40.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_40, 1, 2, 1, 1)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font2)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_3, 1, 0, 1, 1)

        self.label_28 = QLabel(self.groupBox)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_28, 5, 2, 1, 1)

        self.label_27 = QLabel(self.groupBox)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setFont(font2)
        self.label_27.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_27, 3, 2, 1, 1)

        self.keySequenceEdit_2 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_2.setObjectName(u"keySequenceEdit_2")
        self.keySequenceEdit_2.setEnabled(False)
        self.keySequenceEdit_2.setKeySequence(u"A")
        self.keySequenceEdit_2.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_2, 0, 1, 1, 1)

        self.keySequenceEdit_20 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_20.setObjectName(u"keySequenceEdit_20")
        self.keySequenceEdit_20.setEnabled(False)
        self.keySequenceEdit_20.setKeySequence(u"Ctrl+-")
        self.keySequenceEdit_20.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_20, 6, 3, 1, 1)

        self.keySequenceEdit_11 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_11.setObjectName(u"keySequenceEdit_11")
        self.keySequenceEdit_11.setEnabled(False)
        self.keySequenceEdit_11.setKeySequence(u"F")
        self.keySequenceEdit_11.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_11, 5, 1, 1, 1)

        self.keySequenceEdit_3 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_3.setObjectName(u"keySequenceEdit_3")
        self.keySequenceEdit_3.setEnabled(False)
        self.keySequenceEdit_3.setKeySequence(u"D")
        self.keySequenceEdit_3.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_3, 1, 1, 1, 1)

        self.label_26 = QLabel(self.groupBox)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setFont(font2)
        self.label_26.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_26, 4, 2, 1, 1)

        self.keySequenceEdit_4 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_4.setObjectName(u"keySequenceEdit_4")
        self.keySequenceEdit_4.setEnabled(False)
        self.keySequenceEdit_4.setKeySequence(u"Q")
        self.keySequenceEdit_4.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_4, 2, 1, 1, 1)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font2)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_42 = QLabel(self.groupBox)
        self.label_42.setObjectName(u"label_42")
        self.label_42.setFont(font2)
        self.label_42.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_42, 2, 2, 1, 1)

        self.keySequenceEdit_5 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_5.setObjectName(u"keySequenceEdit_5")
        self.keySequenceEdit_5.setEnabled(False)
        self.keySequenceEdit_5.setKeySequence(u"W")
        self.keySequenceEdit_5.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_5, 3, 1, 1, 1)

        self.keySequenceEdit_8 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_8.setObjectName(u"keySequenceEdit_8")
        self.keySequenceEdit_8.setEnabled(False)
        self.keySequenceEdit_8.setKeySequence(u"Ctrl+Del")
        self.keySequenceEdit_8.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_8, 3, 3, 1, 1)

        self.keySequenceEdit_6 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_6.setObjectName(u"keySequenceEdit_6")
        self.keySequenceEdit_6.setEnabled(False)
        self.keySequenceEdit_6.setKeySequence(u"Ctrl+Y")
        self.keySequenceEdit_6.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_6, 1, 3, 1, 1)

        self.keySequenceEdit_19 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_19.setObjectName(u"keySequenceEdit_19")
        self.keySequenceEdit_19.setEnabled(False)
        self.keySequenceEdit_19.setKeySequence(u"Ctrl++")
        self.keySequenceEdit_19.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_19, 6, 1, 1, 1)

        self.keySequenceEdit_14 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_14.setObjectName(u"keySequenceEdit_14")
        self.keySequenceEdit_14.setEnabled(False)
        self.keySequenceEdit_14.setKeySequence(u"Ctrl+S")
        self.keySequenceEdit_14.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_14, 4, 3, 1, 1)

        self.label_22 = QLabel(self.groupBox)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setFont(font2)
        self.label_22.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_22, 0, 2, 1, 1)

        self.keySequenceEdit_9 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_9.setObjectName(u"keySequenceEdit_9")
        self.keySequenceEdit_9.setEnabled(False)
        self.keySequenceEdit_9.setKeySequence(u"V")
        self.keySequenceEdit_9.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_9, 5, 3, 1, 1)

        self.label_35 = QLabel(self.groupBox)
        self.label_35.setObjectName(u"label_35")
        self.label_35.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_35, 6, 2, 1, 1)

        self.label_33 = QLabel(self.groupBox)
        self.label_33.setObjectName(u"label_33")
        self.label_33.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_33, 6, 0, 1, 1)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font2)
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_6, 4, 0, 1, 1)

        self.keySequenceEdit_7 = QKeySequenceEdit(self.groupBox)
        self.keySequenceEdit_7.setObjectName(u"keySequenceEdit_7")
        self.keySequenceEdit_7.setEnabled(False)
        self.keySequenceEdit_7.setKeySequence(u"Ctrl+Return")
        self.keySequenceEdit_7.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.keySequenceEdit_7, 2, 3, 1, 1)


        self.gridLayout_3.addLayout(self.gridLayout_2, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_4 = QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_38 = QLabel(self.groupBox_2)
        self.label_38.setObjectName(u"label_38")
        self.label_38.setFont(font2)
        self.label_38.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_38, 1, 0, 1, 1)

        self.label_39 = QLabel(self.groupBox_2)
        self.label_39.setObjectName(u"label_39")
        self.label_39.setFont(font2)
        self.label_39.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_39, 0, 2, 1, 1)

        self.keySequenceEdit_13 = QKeySequenceEdit(self.groupBox_2)
        self.keySequenceEdit_13.setObjectName(u"keySequenceEdit_13")
        self.keySequenceEdit_13.setEnabled(False)
        self.keySequenceEdit_13.setKeySequence(u"E")
        self.keySequenceEdit_13.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.keySequenceEdit_13, 1, 1, 1, 1)

        self.label_36 = QLabel(self.groupBox_2)
        self.label_36.setObjectName(u"label_36")
        self.label_36.setFont(font2)
        self.label_36.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_36, 0, 0, 1, 1)

        self.keySequenceEdit_12 = QKeySequenceEdit(self.groupBox_2)
        self.keySequenceEdit_12.setObjectName(u"keySequenceEdit_12")
        self.keySequenceEdit_12.setEnabled(False)
        self.keySequenceEdit_12.setKeySequence(u"M")
        self.keySequenceEdit_12.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.keySequenceEdit_12, 0, 1, 1, 1)

        self.keySequenceEdit_15 = QKeySequenceEdit(self.groupBox_2)
        self.keySequenceEdit_15.setObjectName(u"keySequenceEdit_15")
        self.keySequenceEdit_15.setEnabled(False)
        self.keySequenceEdit_15.setKeySequence(u"R")
        self.keySequenceEdit_15.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.keySequenceEdit_15, 0, 3, 1, 1)

        self.label_41 = QLabel(self.groupBox_2)
        self.label_41.setObjectName(u"label_41")
        self.label_41.setFont(font2)
        self.label_41.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_41, 1, 2, 1, 1)

        self.keySequenceEdit_16 = QKeySequenceEdit(self.groupBox_2)
        self.keySequenceEdit_16.setObjectName(u"keySequenceEdit_16")
        self.keySequenceEdit_16.setEnabled(False)
        self.keySequenceEdit_16.setKeySequence(u"P")
        self.keySequenceEdit_16.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.keySequenceEdit_16, 1, 3, 1, 1)

        self.label_43 = QLabel(self.groupBox_2)
        self.label_43.setObjectName(u"label_43")
        self.label_43.setFont(font2)
        self.label_43.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_43, 4, 2, 1, 1)

        self.keySequenceEdit_17 = QKeySequenceEdit(self.groupBox_2)
        self.keySequenceEdit_17.setObjectName(u"keySequenceEdit_17")
        self.keySequenceEdit_17.setEnabled(False)
        self.keySequenceEdit_17.setKeySequence(u"O")
        self.keySequenceEdit_17.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.keySequenceEdit_17, 4, 3, 1, 1)

        self.label_44 = QLabel(self.groupBox_2)
        self.label_44.setObjectName(u"label_44")
        self.label_44.setFont(font2)
        self.label_44.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_44, 4, 0, 1, 1)

        self.keySequenceEdit_18 = QKeySequenceEdit(self.groupBox_2)
        self.keySequenceEdit_18.setObjectName(u"keySequenceEdit_18")
        self.keySequenceEdit_18.setEnabled(False)
        self.keySequenceEdit_18.setKeySequence(u"G")
        self.keySequenceEdit_18.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.keySequenceEdit_18, 4, 1, 1, 1)

        self.label_48 = QLabel(self.groupBox_2)
        self.label_48.setObjectName(u"label_48")
        self.label_48.setFont(font2)
        self.label_48.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_48, 5, 0, 1, 1)

        self.label_49 = QLabel(self.groupBox_2)
        self.label_49.setObjectName(u"label_49")
        self.label_49.setFont(font2)
        self.label_49.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_49, 5, 1, 1, 3)


        self.gridLayout_4.addLayout(self.gridLayout_5, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_2)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_7 = QGridLayout(self.groupBox_3)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_8 = QGridLayout()
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.label_46 = QLabel(self.groupBox_3)
        self.label_46.setObjectName(u"label_46")
        self.label_46.setFont(font2)
        self.label_46.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_8.addWidget(self.label_46, 2, 0, 1, 1)

        self.keySequenceEdit_21 = QKeySequenceEdit(self.groupBox_3)
        self.keySequenceEdit_21.setObjectName(u"keySequenceEdit_21")
        self.keySequenceEdit_21.setEnabled(False)
        self.keySequenceEdit_21.setKeySequence(u"X")
        self.keySequenceEdit_21.setClearButtonEnabled(True)

        self.gridLayout_8.addWidget(self.keySequenceEdit_21, 1, 1, 1, 1)

        self.label_37 = QLabel(self.groupBox_3)
        self.label_37.setObjectName(u"label_37")
        self.label_37.setFont(font2)
        self.label_37.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_8.addWidget(self.label_37, 0, 0, 1, 1)

        self.label_47 = QLabel(self.groupBox_3)
        self.label_47.setObjectName(u"label_47")
        self.label_47.setFont(font2)
        self.label_47.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_8.addWidget(self.label_47, 3, 0, 1, 1)

        self.label_45 = QLabel(self.groupBox_3)
        self.label_45.setObjectName(u"label_45")
        self.label_45.setFont(font2)
        self.label_45.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_8.addWidget(self.label_45, 1, 0, 1, 1)

        self.keySequenceEdit_22 = QKeySequenceEdit(self.groupBox_3)
        self.keySequenceEdit_22.setObjectName(u"keySequenceEdit_22")
        self.keySequenceEdit_22.setEnabled(False)
        self.keySequenceEdit_22.setKeySequence(u"C")
        self.keySequenceEdit_22.setClearButtonEnabled(True)

        self.gridLayout_8.addWidget(self.keySequenceEdit_22, 0, 1, 1, 1)

        self.keySequenceEdit_23 = QKeySequenceEdit(self.groupBox_3)
        self.keySequenceEdit_23.setObjectName(u"keySequenceEdit_23")
        self.keySequenceEdit_23.setEnabled(False)
        self.keySequenceEdit_23.setKeySequence(u"Space")
        self.keySequenceEdit_23.setClearButtonEnabled(True)

        self.gridLayout_8.addWidget(self.keySequenceEdit_23, 2, 1, 1, 1)

        self.keySequenceEdit_24 = QKeySequenceEdit(self.groupBox_3)
        self.keySequenceEdit_24.setObjectName(u"keySequenceEdit_24")
        self.keySequenceEdit_24.setEnabled(False)
        self.keySequenceEdit_24.setKeySequence(u"Esc")
        self.keySequenceEdit_24.setClearButtonEnabled(True)

        self.gridLayout_8.addWidget(self.keySequenceEdit_24, 3, 1, 1, 1)

        self.label_50 = QLabel(self.groupBox_3)
        self.label_50.setObjectName(u"label_50")
        self.label_50.setFont(font2)
        self.label_50.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_8.addWidget(self.label_50, 4, 0, 1, 1)

        self.keySequenceEdit_25 = QKeySequenceEdit(self.groupBox_3)
        self.keySequenceEdit_25.setObjectName(u"keySequenceEdit_25")
        self.keySequenceEdit_25.setEnabled(False)
        self.keySequenceEdit_25.setKeySequence(u"Backspace")
        self.keySequenceEdit_25.setClearButtonEnabled(True)

        self.gridLayout_8.addWidget(self.keySequenceEdit_25, 4, 1, 1, 1)

        self.label_51 = QLabel(self.groupBox_3)
        self.label_51.setObjectName(u"label_51")
        self.label_51.setFont(font2)
        self.label_51.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_8.addWidget(self.label_51, 5, 0, 1, 1)

        self.label_52 = QLabel(self.groupBox_3)
        self.label_52.setObjectName(u"label_52")
        self.label_52.setFont(font2)
        self.label_52.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_8.addWidget(self.label_52, 5, 1, 1, 1)


        self.gridLayout_7.addLayout(self.gridLayout_8, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_3, 1, 0, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_6.addWidget(self.scrollArea, 1, 0, 1, 1)


        self.retranslateUi(DialogShortcut)

        QMetaObject.connectSlotsByName(DialogShortcut)
    # setupUi

    def retranslateUi(self, DialogShortcut):
        DialogShortcut.setWindowTitle(QCoreApplication.translate("DialogShortcut", u"help", None))
        self.label.setText(QCoreApplication.translate("DialogShortcut", u"ZLabel Shortcut", None))
        self.groupBox.setTitle(QCoreApplication.translate("DialogShortcut", u"General", None))
        self.label_32.setText(QCoreApplication.translate("DialogShortcut", u"Auto Range:", None))
        self.label_34.setText(QCoreApplication.translate("DialogShortcut", u"Enable OpenCV:", None))
        self.label_4.setText(QCoreApplication.translate("DialogShortcut", u"Enable SAM:", None))
        self.label_40.setText(QCoreApplication.translate("DialogShortcut", u"Redo:", None))
        self.label_3.setText(QCoreApplication.translate("DialogShortcut", u"Next image:", None))
        self.label_28.setText(QCoreApplication.translate("DialogShortcut", u"Show/Hide:", None))
        self.label_27.setText(QCoreApplication.translate("DialogShortcut", u"Clear:", None))
        self.label_26.setText(QCoreApplication.translate("DialogShortcut", u"Save:", None))
        self.label_2.setText(QCoreApplication.translate("DialogShortcut", u"Prev image:", None))
        self.label_42.setText(QCoreApplication.translate("DialogShortcut", u"Finish:", None))
        self.label_22.setText(QCoreApplication.translate("DialogShortcut", u"Undo:", None))
        self.label_35.setText(QCoreApplication.translate("DialogShortcut", u"Zoom Out:", None))
        self.label_33.setText(QCoreApplication.translate("DialogShortcut", u"Zoom In:", None))
        self.label_6.setText(QCoreApplication.translate("DialogShortcut", u"Delete:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("DialogShortcut", u"Drawing", None))
        self.label_38.setText(QCoreApplication.translate("DialogShortcut", u"Edit Mode:", None))
        self.label_39.setText(QCoreApplication.translate("DialogShortcut", u"Draw Rectangle:", None))
        self.label_36.setText(QCoreApplication.translate("DialogShortcut", u"View Mode:", None))
        self.label_41.setText(QCoreApplication.translate("DialogShortcut", u"Draw Point:", None))
        self.label_43.setText(QCoreApplication.translate("DialogShortcut", u"Draw Polygon:", None))
        self.label_44.setText(QCoreApplication.translate("DialogShortcut", u"Merge Rectangles:", None))
        self.label_48.setText(QCoreApplication.translate("DialogShortcut", u"Switch Current Label:", None))
        self.label_49.setText(QCoreApplication.translate("DialogShortcut", u"Numbers 1-9", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("DialogShortcut", u"Drawing Polygon", None))
        self.label_46.setText(QCoreApplication.translate("DialogShortcut", u"Finish Current Polygon:", None))
        self.label_37.setText(QCoreApplication.translate("DialogShortcut", u"Create Point:", None))
        self.label_47.setText(QCoreApplication.translate("DialogShortcut", u"Cancel Current Drawing:", None))
        self.label_45.setText(QCoreApplication.translate("DialogShortcut", u"Delete Previous Point:", None))
        self.label_50.setText(QCoreApplication.translate("DialogShortcut", u"Delete Hovered Vertex:", None))
        self.label_51.setText(QCoreApplication.translate("DialogShortcut", u"Finish by Double-click:", None))
        self.label_52.setText(QCoreApplication.translate("DialogShortcut", u"Double-click", None))
    # retranslateUi

