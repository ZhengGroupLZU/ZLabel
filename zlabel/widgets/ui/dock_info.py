# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_info.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QWidget)
import icons_rc

class Ui_ZDockInfoContent(object):
    def setupUi(self, ZDockInfoContent):
        if not ZDockInfoContent.objectName():
            ZDockInfoContent.setObjectName(u"ZDockInfoContent")
        ZDockInfoContent.resize(188, 133)
        self.gridLayout_2 = QGridLayout(ZDockInfoContent)
        self.gridLayout_2.setSpacing(2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(2, 2, 2, 2)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(2, 2, 2, 3)
        self.label_4 = QLabel(ZDockInfoContent)
        self.label_4.setObjectName(u"label_4")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)

        self.label_anno_h = QLabel(ZDockInfoContent)
        self.label_anno_h.setObjectName(u"label_anno_h")

        self.gridLayout.addWidget(self.label_anno_h, 2, 3, 1, 1)

        self.label_anno_w = QLabel(ZDockInfoContent)
        self.label_anno_w.setObjectName(u"label_anno_w")

        self.gridLayout.addWidget(self.label_anno_w, 2, 1, 1, 1)

        self.label_3 = QLabel(ZDockInfoContent)
        self.label_3.setObjectName(u"label_3")
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)

        self.label_img_width = QLabel(ZDockInfoContent)
        self.label_img_width.setObjectName(u"label_img_width")

        self.gridLayout.addWidget(self.label_img_width, 0, 1, 1, 1)

        self.label_anno_y = QLabel(ZDockInfoContent)
        self.label_anno_y.setObjectName(u"label_anno_y")

        self.gridLayout.addWidget(self.label_anno_y, 1, 3, 1, 1)

        self.label_8 = QLabel(ZDockInfoContent)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setMinimumSize(QSize(0, 0))

        self.gridLayout.addWidget(self.label_8, 2, 2, 1, 1)

        self.label_6 = QLabel(ZDockInfoContent)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMinimumSize(QSize(0, 0))

        self.gridLayout.addWidget(self.label_6, 1, 2, 1, 1)

        self.label_anno_x = QLabel(ZDockInfoContent)
        self.label_anno_x.setObjectName(u"label_anno_x")

        self.gridLayout.addWidget(self.label_anno_x, 1, 1, 1, 1)

        self.label_img_height = QLabel(ZDockInfoContent)
        self.label_img_height.setObjectName(u"label_img_height")

        self.gridLayout.addWidget(self.label_img_height, 0, 3, 1, 1)

        self.label = QLabel(ZDockInfoContent)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_5 = QLabel(ZDockInfoContent)
        self.label_5.setObjectName(u"label_5")
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)

        self.label_2 = QLabel(ZDockInfoContent)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(0, 0))

        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)

        self.label_7 = QLabel(ZDockInfoContent)
        self.label_7.setObjectName(u"label_7")
        sizePolicy.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 1)

        self.cbox_users = QComboBox(ZDockInfoContent)
        self.cbox_users.addItem("")
        self.cbox_users.setObjectName(u"cbox_users")

        self.gridLayout.addWidget(self.cbox_users, 4, 1, 1, 2)

        self.btn_delete_anno = QPushButton(ZDockInfoContent)
        self.btn_delete_anno.setObjectName(u"btn_delete_anno")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_delete_anno.sizePolicy().hasHeightForWidth())
        self.btn_delete_anno.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u":/icon/icons/delete-3.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_delete_anno.setIcon(icon)

        self.gridLayout.addWidget(self.btn_delete_anno, 4, 3, 1, 1)

        self.ledit_anno_note = QLineEdit(ZDockInfoContent)
        self.ledit_anno_note.setObjectName(u"ledit_anno_note")
        self.ledit_anno_note.setMinimumSize(QSize(0, 0))

        self.gridLayout.addWidget(self.ledit_anno_note, 3, 1, 1, 3)


        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)


        self.retranslateUi(ZDockInfoContent)

        QMetaObject.connectSlotsByName(ZDockInfoContent)
    # setupUi

    def retranslateUi(self, ZDockInfoContent):
        ZDockInfoContent.setWindowTitle(QCoreApplication.translate("ZDockInfoContent", u"DockInfo", None))
        self.label_4.setText(QCoreApplication.translate("ZDockInfoContent", u"X:", None))
        self.label_anno_h.setText("")
        self.label_anno_w.setText("")
        self.label_3.setText(QCoreApplication.translate("ZDockInfoContent", u"User:", None))
        self.label_img_width.setText("")
        self.label_anno_y.setText("")
        self.label_8.setText(QCoreApplication.translate("ZDockInfoContent", u"H:", None))
        self.label_6.setText(QCoreApplication.translate("ZDockInfoContent", u"Y:", None))
        self.label_anno_x.setText("")
        self.label_img_height.setText("")
        self.label.setText(QCoreApplication.translate("ZDockInfoContent", u"Width :", None))
        self.label_5.setText(QCoreApplication.translate("ZDockInfoContent", u"Note:", None))
        self.label_2.setText(QCoreApplication.translate("ZDockInfoContent", u"Height:", None))
        self.label_7.setText(QCoreApplication.translate("ZDockInfoContent", u"W:", None))
        self.cbox_users.setItemText(0, QCoreApplication.translate("ZDockInfoContent", u"Default User", None))

        self.btn_delete_anno.setText("")
        self.ledit_anno_note.setPlaceholderText(QCoreApplication.translate("ZDockInfoContent", u"add extra image note here", None))
    # retranslateUi

