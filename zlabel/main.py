# -*- coding: utf-8 -*-
# import os

import sys

from qtpy import QtWidgets, QtCore

from zlabel.widgets.mainwindow import MainWindow


def main():
    # QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    # QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    app = QtWidgets.QApplication()
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
