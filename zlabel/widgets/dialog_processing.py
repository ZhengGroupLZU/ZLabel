from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

from .ui import Ui_DialogProcessing


class DialogProcessing(QDialog, Ui_DialogProcessing):
    def __init__(self, parent):
        super(DialogProcessing, self).__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)
