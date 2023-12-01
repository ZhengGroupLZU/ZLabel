from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

from .ui import Ui_DialogAbout


class DialogAbout(QDialog, Ui_DialogAbout):
    def __init__(self, parent):
        super(DialogAbout, self).__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)
