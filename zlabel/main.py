# -*- coding: utf-8 -*-
# import os

import sys

from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QFont

from zlabel.widgets.mainwindow import MainWindow


def main():
    app = QApplication()
    font = app.font()
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
