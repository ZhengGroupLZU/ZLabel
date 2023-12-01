# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_category_choice.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)
import icons_rc

class Ui_DialogCategoryChoice(object):
    def setupUi(self, DialogCategoryChoice):
        if not DialogCategoryChoice.objectName():
            DialogCategoryChoice.setObjectName(u"DialogCategoryChoice")
        DialogCategoryChoice.resize(350, 399)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(12)
        DialogCategoryChoice.setFont(font)
        self.verticalLayout = QVBoxLayout(DialogCategoryChoice)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.listWidget = QListWidget(DialogCategoryChoice)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout.addWidget(self.listWidget)

        self.widget_3 = QWidget(DialogCategoryChoice)
        self.widget_3.setObjectName(u"widget_3")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.widget_3)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(60, 0))
        self.label_2.setMaximumSize(QSize(60, 16777215))

        self.horizontalLayout_3.addWidget(self.label_2)

        self.lineEdit_category = QLineEdit(self.widget_3)
        self.lineEdit_category.setObjectName(u"lineEdit_category")
        self.lineEdit_category.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lineEdit_category.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineEdit_category)

        self.label = QLabel(self.widget_3)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(50, 0))
        self.label.setMaximumSize(QSize(50, 16777215))

        self.horizontalLayout_3.addWidget(self.label)

        self.lineEdit_group = QLineEdit(self.widget_3)
        self.lineEdit_group.setObjectName(u"lineEdit_group")
        self.lineEdit_group.setMinimumSize(QSize(60, 0))
        self.lineEdit_group.setMaximumSize(QSize(60, 16777215))
        self.lineEdit_group.setInputMethodHints(Qt.ImhDigitsOnly)
        self.lineEdit_group.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.lineEdit_group)


        self.verticalLayout.addWidget(self.widget_3)

        self.widget_5 = QWidget(DialogCategoryChoice)
        self.widget_5.setObjectName(u"widget_5")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_5)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.widget_5)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(60, 0))
        self.label_3.setMaximumSize(QSize(60, 16777215))

        self.horizontalLayout_5.addWidget(self.label_3)

        self.lineEdit_note = QLineEdit(self.widget_5)
        self.lineEdit_note.setObjectName(u"lineEdit_note")
        self.lineEdit_note.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.lineEdit_note)

        self.label_4 = QLabel(self.widget_5)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(50, 0))
        self.label_4.setMaximumSize(QSize(50, 16777215))

        self.horizontalLayout_5.addWidget(self.label_4)

        self.label_layer = QLabel(self.widget_5)
        self.label_layer.setObjectName(u"label_layer")
        self.label_layer.setMinimumSize(QSize(60, 0))
        self.label_layer.setMaximumSize(QSize(60, 16777215))
        self.label_layer.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_layer)


        self.verticalLayout.addWidget(self.widget_5)

        self.widget = QWidget(DialogCategoryChoice)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.widget)

        self.widget_2 = QWidget(DialogCategoryChoice)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.checkBox_iscrowded = QCheckBox(self.widget_2)
        self.checkBox_iscrowded.setObjectName(u"checkBox_iscrowded")

        self.horizontalLayout_2.addWidget(self.checkBox_iscrowded)

        self.horizontalSpacer_2 = QSpacerItem(97, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.pushButton_cancel = QPushButton(self.widget_2)
        self.pushButton_cancel.setObjectName(u"pushButton_cancel")
        icon = QIcon()
        icon.addFile(u":/icon/icons/close-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_cancel.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.pushButton_cancel)

        self.pushButton_apply = QPushButton(self.widget_2)
        self.pushButton_apply.setObjectName(u"pushButton_apply")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/check-one.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_apply.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.pushButton_apply)


        self.verticalLayout.addWidget(self.widget_2)


        self.retranslateUi(DialogCategoryChoice)

        QMetaObject.connectSlotsByName(DialogCategoryChoice)
    # setupUi

    def retranslateUi(self, DialogCategoryChoice):
        DialogCategoryChoice.setWindowTitle("")
        self.label_2.setText(QCoreApplication.translate("DialogCategoryChoice", u"category:", None))
        self.label.setText(QCoreApplication.translate("DialogCategoryChoice", u"group:", None))
        self.lineEdit_group.setText("")
        self.lineEdit_group.setPlaceholderText(QCoreApplication.translate("DialogCategoryChoice", u"group id", None))
        self.label_3.setText(QCoreApplication.translate("DialogCategoryChoice", u"note:", None))
        self.lineEdit_note.setPlaceholderText(QCoreApplication.translate("DialogCategoryChoice", u"add extra note here", None))
        self.label_4.setText(QCoreApplication.translate("DialogCategoryChoice", u"layer:", None))
        self.label_layer.setText("")
        self.checkBox_iscrowded.setText(QCoreApplication.translate("DialogCategoryChoice", u"is crowded", None))
        self.pushButton_cancel.setText(QCoreApplication.translate("DialogCategoryChoice", u"cancel", None))
        self.pushButton_apply.setText(QCoreApplication.translate("DialogCategoryChoice", u"apply", None))
    # retranslateUi

