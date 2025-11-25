from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtWidgets import QDialog

from .ui import Ui_DialogShortcut


class DialogShortcut(QDialog, Ui_DialogShortcut):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)
