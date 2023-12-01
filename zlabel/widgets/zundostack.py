from enum import Enum
from typing import List
from qtpy.QtGui import QUndoStack, QUndoCommand

from zlabel.utils.project import Result


class ResultUndoMode(Enum):
    ADD = 0
    REMOVE = 1


class ZResultUndoCmd(QUndoCommand):
    def __init__(self, mainwindow, results: List[Result], mode: ResultUndoMode):
        super().__init__()
        self.mw = mainwindow
        self.results = results
        self.mode = mode

    def redo(self):
        if self.mode == ResultUndoMode.ADD:
            self.mw.add_results(self.results)
        elif self.mode == ResultUndoMode.REMOVE:
            self.mw.remove_results([r.id for r in self.results])
        else:
            raise NotImplementedError

    def undo(self):
        if self.mode == ResultUndoMode.ADD:
            self.mw.remove_results([r.id for r in self.results])
        elif self.mode == ResultUndoMode.REMOVE:
            self.mw.add_results(self.results)
        else:
            raise NotImplementedError
