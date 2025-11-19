from pyqtgraph.Qt.QtWidgets import QWidget
from pyqtgraph.Qt.QtCore import Signal

from zlabel.utils import Annotation, PolygonResult, RectangleResult, User

from .ui import Ui_ZDockInfoContent


class ZDockInfoContent(QWidget, Ui_ZDockInfoContent):
    sigNoteTextChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.ledit_anno_note.textChanged.connect(self.on_ledit_anno_note_textChanged)

    def on_ledit_anno_note_textChanged(self):
        self.sigNoteTextChanged.emit(self.ledit_anno_note.toPlainText())

    def set_info_by_anno(self, anno: Annotation | None):
        if anno is None:
            self.label_img_width.setText("")
            self.label_img_height.setText("")
        else:
            self.label_img_width.setText(f"{anno.original_width:.2f}")
            self.label_img_height.setText(f"{anno.original_height:.2f}")
            self.ledit_anno_note.setPlainText(anno.note)
