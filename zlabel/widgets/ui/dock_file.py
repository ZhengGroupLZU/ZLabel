# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dock_file.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
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
    QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QTableWidgetItem,
    QVBoxLayout, QWidget)

from zlabel.widgets.zwidgets import ZTableWidget
import icons_rc

class Ui_ZDockFileContent(object):
    def setupUi(self, ZDockFileContent):
        if not ZDockFileContent.objectName():
            ZDockFileContent.setObjectName(u"ZDockFileContent")
        ZDockFileContent.resize(300, 515)
        self.gridLayout_2 = QGridLayout(ZDockFileContent)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.table_files = ZTableWidget(ZDockFileContent)
        self.table_files.setObjectName(u"table_files")
        self.table_files.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_files.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_files.setSortingEnabled(False)

        self.verticalLayout.addWidget(self.table_files)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(3)
        self.gridLayout.setVerticalSpacing(1)
        self.ckbox_finished = QCheckBox(ZDockFileContent)
        self.ckbox_finished.setObjectName(u"ckbox_finished")
        self.ckbox_finished.setChecked(False)
        self.ckbox_finished.setTristate(True)

        self.gridLayout.addWidget(self.ckbox_finished, 3, 0, 1, 2)

        self.btn_fetch = QPushButton(ZDockFileContent)
        self.btn_fetch.setObjectName(u"btn_fetch")
        icon = QIcon()
        icon.addFile(u":/icon/icons/import.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_fetch.setIcon(icon)

        self.gridLayout.addWidget(self.btn_fetch, 3, 2, 1, 1)

        self.cbox_fetch_num = QComboBox(ZDockFileContent)
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
        self.cbox_fetch_num.setMaxVisibleItems(20)

        self.gridLayout.addWidget(self.cbox_fetch_num, 1, 2, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_current = QLabel(ZDockFileContent)
        self.label_current.setObjectName(u"label_current")
        self.label_current.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.label_current)

        self.label = QLabel(ZDockFileContent)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(10, 16777215))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label)

        self.label_all = QLabel(ZDockFileContent)
        self.label_all.setObjectName(u"label_all")

        self.horizontalLayout_2.addWidget(self.label_all)


        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 1, 1, 1)

        self.ledit_jump = QLineEdit(ZDockFileContent)
        self.ledit_jump.setObjectName(u"ledit_jump")
        self.ledit_jump.setMaximumSize(QSize(500, 16777215))

        self.gridLayout.addWidget(self.ledit_jump, 1, 0, 1, 1)

        self.cmbox_project = QComboBox(ZDockFileContent)
        self.cmbox_project.setObjectName(u"cmbox_project")

        self.gridLayout.addWidget(self.cmbox_project, 0, 0, 1, 3)


        self.verticalLayout.addLayout(self.gridLayout)


        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)


        self.retranslateUi(ZDockFileContent)

        self.cbox_fetch_num.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ZDockFileContent)
    # setupUi

    def retranslateUi(self, ZDockFileContent):
        ZDockFileContent.setWindowTitle(QCoreApplication.translate("ZDockFileContent", u"Form", None))
#if QT_CONFIG(tooltip)
        self.ckbox_finished.setToolTip(QCoreApplication.translate("ZDockFileContent", u"Which kind of tasks to fetch.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.ckbox_finished.setStatusTip(QCoreApplication.translate("ZDockFileContent", u"Which kind of tasks to fetch.", None))
#endif // QT_CONFIG(statustip)
        self.ckbox_finished.setText(QCoreApplication.translate("ZDockFileContent", u"Unfinished", None))
#if QT_CONFIG(tooltip)
        self.btn_fetch.setToolTip(QCoreApplication.translate("ZDockFileContent", u"Fetch tasks.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.btn_fetch.setStatusTip(QCoreApplication.translate("ZDockFileContent", u"Fetch tasks.", None))
#endif // QT_CONFIG(statustip)
        self.btn_fetch.setText(QCoreApplication.translate("ZDockFileContent", u"Fetch", None))
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

#if QT_CONFIG(tooltip)
        self.cbox_fetch_num.setToolTip(QCoreApplication.translate("ZDockFileContent", u"How many tasks to get.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.cbox_fetch_num.setStatusTip(QCoreApplication.translate("ZDockFileContent", u"How many tasks to get.", None))
#endif // QT_CONFIG(statustip)
        self.label_current.setText("")
        self.label.setText(QCoreApplication.translate("ZDockFileContent", u"/", None))
        self.label_all.setText("")
#if QT_CONFIG(tooltip)
        self.ledit_jump.setToolTip(QCoreApplication.translate("ZDockFileContent", u"Jump to the image. Input name or index.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.ledit_jump.setStatusTip(QCoreApplication.translate("ZDockFileContent", u"Jump to the image. Input name or index.", None))
#endif // QT_CONFIG(statustip)
        self.ledit_jump.setPlaceholderText(QCoreApplication.translate("ZDockFileContent", u"Jump to", None))
    # retranslateUi

