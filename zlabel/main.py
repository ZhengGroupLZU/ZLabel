import sys

from pyqtgraph.Qt.QtGui import QFont
from pyqtgraph.Qt.QtWidgets import QApplication

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
