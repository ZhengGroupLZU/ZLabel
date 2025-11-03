# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_file.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QTableWidgetItem, QVBoxLayout,
    QWidget)

from zlabel.widgets.zwidgets import ZTableWidget
import icons_rc

class Ui_ZDockFileContent(object):
    def setupUi(self, ZDockFileContent):
        if not ZDockFileContent.objectName():
            ZDockFileContent.setObjectName(u"ZDockFileContent")
        ZDockFileContent.resize(300, 387)
        ZDockFileContent.setMinimumSize(QSize(60, 0))
        ZDockFileContent.setMaximumSize(QSize(300, 16777215))
        self.verticalLayout = QVBoxLayout(ZDockFileContent)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.table_files = ZTableWidget(ZDockFileContent)
        self.table_files.setObjectName(u"table_files")
        self.table_files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_files.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_files.setSortingEnabled(False)

        self.verticalLayout.addWidget(self.table_files)

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

        self.cbox_fetch_num = QComboBox(self.widget_num)
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.addItem("")
        self.cbox_fetch_num.setObjectName(u"cbox_fetch_num")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbox_fetch_num.sizePolicy().hasHeightForWidth())
        self.cbox_fetch_num.setSizePolicy(sizePolicy)
        self.cbox_fetch_num.setMinimumSize(QSize(50, 0))
        self.cbox_fetch_num.setMaxVisibleItems(20)

        self.horizontalLayout.addWidget(self.cbox_fetch_num)

        self.ckbox_finished = QCheckBox(self.widget_num)
        self.ckbox_finished.setObjectName(u"ckbox_finished")
        self.ckbox_finished.setChecked(False)
        self.ckbox_finished.setTristate(True)

        self.horizontalLayout.addWidget(self.ckbox_finished)

        self.btn_fetch = QPushButton(self.widget_num)
        self.btn_fetch.setObjectName(u"btn_fetch")
        icon = QIcon()
        icon.addFile(u":/icon/icons/import.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_fetch.setIcon(icon)

        self.horizontalLayout.addWidget(self.btn_fetch)


        self.verticalLayout.addWidget(self.widget_num)


        self.retranslateUi(ZDockFileContent)

        self.cbox_fetch_num.setCurrentIndex(4)


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
        self.cbox_fetch_num.setItemText(0, QCoreApplication.translate("ZDockFileContent", u"10", None))
        self.cbox_fetch_num.setItemText(1, QCoreApplication.translate("ZDockFileContent", u"30", None))
        self.cbox_fetch_num.setItemText(2, QCoreApplication.translate("ZDockFileContent", u"50", None))
        self.cbox_fetch_num.setItemText(3, QCoreApplication.translate("ZDockFileContent", u"80", None))
        self.cbox_fetch_num.setItemText(4, QCoreApplication.translate("ZDockFileContent", u"100", None))
        self.cbox_fetch_num.setItemText(5, QCoreApplication.translate("ZDockFileContent", u"130", None))
        self.cbox_fetch_num.setItemText(6, QCoreApplication.translate("ZDockFileContent", u"150", None))
        self.cbox_fetch_num.setItemText(7, QCoreApplication.translate("ZDockFileContent", u"200", None))
        self.cbox_fetch_num.setItemText(8, QCoreApplication.translate("ZDockFileContent", u"300", None))
        self.cbox_fetch_num.setItemText(9, QCoreApplication.translate("ZDockFileContent", u"500", None))
        self.cbox_fetch_num.setItemText(10, QCoreApplication.translate("ZDockFileContent", u"1000", None))
        self.cbox_fetch_num.setItemText(11, QCoreApplication.translate("ZDockFileContent", u"all", None))

        self.ckbox_finished.setText(QCoreApplication.translate("ZDockFileContent", u"Finished", None))
        self.btn_fetch.setText("")
    # retranslateUi

