import multiprocessing
import sys

import pyqtgraph as pg
from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtGui import QFont
from pyqtgraph.Qt.QtWidgets import QApplication

from zlabel.widgets.mainwindow import MainWindow

pg.setConfigOptions(useOpenGL=True, imageAxisOrder="row-major", useCupy=False, useNumba=False)


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    app = QApplication()
    font = app.font()
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # frozen builds (Nuitka/cx_Freeze/PyInstaller) need this so the MNN process
    # pool's spawn child bootstraps instead of relaunching the GUI -> BrokenProcessPool
    multiprocessing.freeze_support()
    main()
