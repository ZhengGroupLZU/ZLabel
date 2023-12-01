# -*- coding: utf-8 -*-
# @Author  : LG
# import os

from qtpy import QtWidgets
from . import MainWindow
import sys


def main():
    app = QtWidgets.QApplication([""])
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
