# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_settings.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)
import icons_rc

class Ui_DialogSettings(object):
    def setupUi(self, DialogSettings):
        if not DialogSettings.objectName():
            DialogSettings.setObjectName(u"DialogSettings")
        DialogSettings.resize(644, 473)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(12)
        DialogSettings.setFont(font)
        self.gridLayout_5 = QGridLayout(DialogSettings)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.btn_cancel = QPushButton(DialogSettings)
        self.btn_cancel.setObjectName(u"btn_cancel")
        icon = QIcon()
        icon.addFile(u":/icon/icons/close-one.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_cancel.setIcon(icon)

        self.horizontalLayout_4.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton(DialogSettings)
        self.btn_apply.setObjectName(u"btn_apply")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/check-one.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_apply.setIcon(icon1)

        self.horizontalLayout_4.addWidget(self.btn_apply)


        self.gridLayout_5.addLayout(self.horizontalLayout_4, 1, 0, 1, 1)

        self.tabWidget = QTabWidget(DialogSettings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_global = QWidget()
        self.tab_global.setObjectName(u"tab_global")
        self.gridLayout_7 = QGridLayout(self.tab_global)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(5, 5, 5, 5)
        self.scrollArea = QScrollArea(self.tab_global)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 601, 692))
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.groupBox = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_4.addWidget(self.label_5, 2, 0, 1, 1)

        self.ledit_username = QLineEdit(self.groupBox)
        self.ledit_username.setObjectName(u"ledit_username")

        self.gridLayout_4.addWidget(self.ledit_username, 1, 1, 1, 1)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_4.addWidget(self.label_6, 3, 0, 1, 1)

        self.dspbox_alpha = QDoubleSpinBox(self.groupBox)
        self.dspbox_alpha.setObjectName(u"dspbox_alpha")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dspbox_alpha.sizePolicy().hasHeightForWidth())
        self.dspbox_alpha.setSizePolicy(sizePolicy)
        self.dspbox_alpha.setMinimumSize(QSize(63, 0))
        self.dspbox_alpha.setMaximum(1.000000000000000)
        self.dspbox_alpha.setSingleStep(0.100000000000000)
        self.dspbox_alpha.setValue(0.500000000000000)

        self.gridLayout_4.addWidget(self.dspbox_alpha, 3, 1, 1, 1)

        self.ledit_password = QLineEdit(self.groupBox)
        self.ledit_password.setObjectName(u"ledit_password")

        self.gridLayout_4.addWidget(self.ledit_password, 2, 1, 1, 1)

        self.ledit_host = QLineEdit(self.groupBox)
        self.ledit_host.setObjectName(u"ledit_host")
        self.ledit_host.setEnabled(True)

        self.gridLayout_4.addWidget(self.ledit_host, 0, 1, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_4.addWidget(self.label_4, 1, 0, 1, 1)

        self.label_11 = QLabel(self.groupBox)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_4.addWidget(self.label_11, 4, 0, 1, 1)

        self.cmbox_loglevel = QComboBox(self.groupBox)
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.addItem("")
        self.cmbox_loglevel.setObjectName(u"cmbox_loglevel")

        self.gridLayout_4.addWidget(self.cmbox_loglevel, 4, 1, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout_4, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy1)
        self.groupBox_4.setMinimumSize(QSize(0, 500))
        self.gridLayout_6 = QGridLayout(self.groupBox_4)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_3 = QLabel(self.groupBox_4)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_3.addWidget(self.label_3, 2, 0, 1, 1)

        self.label_10 = QLabel(self.groupBox_4)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_3.addWidget(self.label_10, 1, 0, 1, 1)

        self.label_9 = QLabel(self.groupBox_4)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_3.addWidget(self.label_9, 0, 0, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btn_add_label = QPushButton(self.groupBox_4)
        self.btn_add_label.setObjectName(u"btn_add_label")

        self.verticalLayout.addWidget(self.btn_add_label)

        self.btn_delete_label = QPushButton(self.groupBox_4)
        self.btn_delete_label.setObjectName(u"btn_delete_label")

        self.verticalLayout.addWidget(self.btn_delete_label)

        self.btn_clear = QPushButton(self.groupBox_4)
        self.btn_clear.setObjectName(u"btn_clear")

        self.verticalLayout.addWidget(self.btn_clear)

        self.verticalSpacer = QSpacerItem(20, 110, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.gridLayout_3.addLayout(self.verticalLayout, 2, 2, 1, 1)

        self.ledit_projname = QLineEdit(self.groupBox_4)
        self.ledit_projname.setObjectName(u"ledit_projname")
        self.ledit_projname.setEnabled(False)

        self.gridLayout_3.addWidget(self.ledit_projname, 0, 1, 1, 2)

        self.ledit_prjdesc = QLineEdit(self.groupBox_4)
        self.ledit_prjdesc.setObjectName(u"ledit_prjdesc")
        self.ledit_prjdesc.setEnabled(False)

        self.gridLayout_3.addWidget(self.ledit_prjdesc, 1, 1, 1, 2)

        self.table_labels = QTableWidget(self.groupBox_4)
        if (self.table_labels.columnCount() < 4):
            self.table_labels.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_labels.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table_labels.setObjectName(u"table_labels")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.table_labels.sizePolicy().hasHeightForWidth())
        self.table_labels.setSizePolicy(sizePolicy2)

        self.gridLayout_3.addWidget(self.table_labels, 2, 1, 1, 1)


        self.gridLayout_6.addLayout(self.gridLayout_3, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_4, 1, 0, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_7.addWidget(self.scrollArea, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_global, "")

        self.gridLayout_5.addWidget(self.tabWidget, 0, 0, 1, 1)


        self.retranslateUi(DialogSettings)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DialogSettings)
    # setupUi

    def retranslateUi(self, DialogSettings):
        DialogSettings.setWindowTitle(QCoreApplication.translate("DialogSettings", u"Setting", None))
        self.btn_cancel.setText(QCoreApplication.translate("DialogSettings", u"Cancel", None))
        self.btn_apply.setText(QCoreApplication.translate("DialogSettings", u"Apply", None))
        self.groupBox.setTitle(QCoreApplication.translate("DialogSettings", u"API", None))
        self.label_5.setText(QCoreApplication.translate("DialogSettings", u"Password:", None))
        self.label_6.setText(QCoreApplication.translate("DialogSettings", u"Alpha:", None))
        self.label.setText(QCoreApplication.translate("DialogSettings", u"Server Host:", None))
        self.label_4.setText(QCoreApplication.translate("DialogSettings", u"User Name:", None))
        self.label_11.setText(QCoreApplication.translate("DialogSettings", u"LogLevel:", None))
        self.cmbox_loglevel.setItemText(0, QCoreApplication.translate("DialogSettings", u"DEBUG", None))
        self.cmbox_loglevel.setItemText(1, QCoreApplication.translate("DialogSettings", u"INFO", None))
        self.cmbox_loglevel.setItemText(2, QCoreApplication.translate("DialogSettings", u"WARNING", None))
        self.cmbox_loglevel.setItemText(3, QCoreApplication.translate("DialogSettings", u"ERROR", None))

        self.groupBox_4.setTitle(QCoreApplication.translate("DialogSettings", u"Project", None))
        self.label_3.setText(QCoreApplication.translate("DialogSettings", u"Labels:", None))
        self.label_10.setText(QCoreApplication.translate("DialogSettings", u"Description:", None))
        self.label_9.setText(QCoreApplication.translate("DialogSettings", u"Name:", None))
        self.btn_add_label.setText(QCoreApplication.translate("DialogSettings", u"Add", None))
        self.btn_delete_label.setText(QCoreApplication.translate("DialogSettings", u"Delete", None))
        self.btn_clear.setText(QCoreApplication.translate("DialogSettings", u"Clear", None))
        ___qtablewidgetitem = self.table_labels.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DialogSettings", u"ID", None));
        ___qtablewidgetitem1 = self.table_labels.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DialogSettings", u"Name", None));
        ___qtablewidgetitem2 = self.table_labels.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DialogSettings", u"Color", None));
        ___qtablewidgetitem3 = self.table_labels.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("DialogSettings", u"Delete", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_global), QCoreApplication.translate("DialogSettings", u"Global", None))
    # retranslateUi

