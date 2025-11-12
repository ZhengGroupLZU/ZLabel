import sys

import pyqtgraph as pg
from pyqtgraph.Qt.QtGui import QFont
from pyqtgraph.Qt.QtWidgets import QApplication

from zlabel.widgets.mainwindow import MainWindow

pg.setConfigOptions(useOpenGL=True, useCupy=False, useNumba=False)


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
