# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_new_proj.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_DialogNewProject(object):
    def setupUi(self, DialogNewProject):
        if not DialogNewProject.objectName():
            DialogNewProject.setObjectName(u"DialogNewProject")
        DialogNewProject.resize(426, 194)
        self.verticalLayout = QVBoxLayout(DialogNewProject)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.btn_select_path = QPushButton(DialogNewProject)
        self.btn_select_path.setObjectName(u"btn_select_path")

        self.gridLayout.addWidget(self.btn_select_path, 0, 2, 1, 1)

        self.label_4 = QLabel(DialogNewProject)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)

        self.label_3 = QLabel(DialogNewProject)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)

        self.btn_reset_proj_name = QPushButton(DialogNewProject)
        self.btn_reset_proj_name.setObjectName(u"btn_reset_proj_name")

        self.gridLayout.addWidget(self.btn_reset_proj_name, 1, 2, 1, 1)

        self.label = QLabel(DialogNewProject)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.btn_reset_proj_descrip = QPushButton(DialogNewProject)
        self.btn_reset_proj_descrip.setObjectName(u"btn_reset_proj_descrip")

        self.gridLayout.addWidget(self.btn_reset_proj_descrip, 2, 2, 1, 1)

        self.btn_reset_user_name = QPushButton(DialogNewProject)
        self.btn_reset_user_name.setObjectName(u"btn_reset_user_name")

        self.gridLayout.addWidget(self.btn_reset_user_name, 3, 2, 1, 1)

        self.ledit_proj_name = QLineEdit(DialogNewProject)
        self.ledit_proj_name.setObjectName(u"ledit_proj_name")

        self.gridLayout.addWidget(self.ledit_proj_name, 1, 1, 1, 1)

        self.label_2 = QLabel(DialogNewProject)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.ledit_path = QLineEdit(DialogNewProject)
        self.ledit_path.setObjectName(u"ledit_path")

        self.gridLayout.addWidget(self.ledit_path, 0, 1, 1, 1)

        self.ledit_user_name = QLineEdit(DialogNewProject)
        self.ledit_user_name.setObjectName(u"ledit_user_name")

        self.gridLayout.addWidget(self.ledit_user_name, 3, 1, 1, 1)

        self.ledit_descrip = QLineEdit(DialogNewProject)
        self.ledit_descrip.setObjectName(u"ledit_descrip")

        self.gridLayout.addWidget(self.ledit_descrip, 2, 1, 1, 1)

        self.label_5 = QLabel(DialogNewProject)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 1)

        self.ledit_user_email = QLineEdit(DialogNewProject)
        self.ledit_user_email.setObjectName(u"ledit_user_email")

        self.gridLayout.addWidget(self.ledit_user_email, 4, 1, 1, 1)

        self.btn_reset_user_email = QPushButton(DialogNewProject)
        self.btn_reset_user_email.setObjectName(u"btn_reset_user_email")

        self.gridLayout.addWidget(self.btn_reset_user_email, 4, 2, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.buttonBox = QDialogButtonBox(DialogNewProject)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(DialogNewProject)
        self.buttonBox.accepted.connect(DialogNewProject.accept)
        self.buttonBox.rejected.connect(DialogNewProject.reject)

        QMetaObject.connectSlotsByName(DialogNewProject)
    # setupUi

    def retranslateUi(self, DialogNewProject):
        DialogNewProject.setWindowTitle(QCoreApplication.translate("DialogNewProject", u"New Project", None))
        self.btn_select_path.setText(QCoreApplication.translate("DialogNewProject", u"Select", None))
        self.label_4.setText(QCoreApplication.translate("DialogNewProject", u"User Name:", None))
        self.label_3.setText(QCoreApplication.translate("DialogNewProject", u"Description:", None))
        self.btn_reset_proj_name.setText(QCoreApplication.translate("DialogNewProject", u"Reset", None))
        self.label.setText(QCoreApplication.translate("DialogNewProject", u"Path:", None))
        self.btn_reset_proj_descrip.setText(QCoreApplication.translate("DialogNewProject", u"Reset", None))
        self.btn_reset_user_name.setText(QCoreApplication.translate("DialogNewProject", u"Reset", None))
        self.label_2.setText(QCoreApplication.translate("DialogNewProject", u"Name:", None))
        self.label_5.setText(QCoreApplication.translate("DialogNewProject", u"User Email:", None))
        self.btn_reset_user_email.setText(QCoreApplication.translate("DialogNewProject", u"Reset", None))
    # retranslateUi

