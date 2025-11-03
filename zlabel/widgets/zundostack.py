from enum import Enum
from typing import List
from qtpy.QtGui import QUndoCommand

from zlabel.utils import Result, RectangleResult, PolygonResult


class ResultUndoMode(Enum):
    ADD = 0
    REMOVE = 1
    MODIFY = 2
    MERGE = 3


class ZResultUndoCmd(QUndoCommand):
    def __init__(
        self,
        mainwindow,
        results: List[RectangleResult | PolygonResult],
        mode: ResultUndoMode,
        results_old: List[RectangleResult | PolygonResult] | None = None,
    ):
        super().__init__()
        self.mw = mainwindow
        self.results = results
        self.results_old = results_old
        self.mode = mode
        # with modify, results_old must be provided
        assert results_old or self.mode != ResultUndoMode.MODIFY

    def redo(self):
        if self.mode == ResultUndoMode.ADD:
            self.mw.add_results(self.results)
        elif self.mode == ResultUndoMode.REMOVE:
            self.mw.remove_results([r.id for r in self.results])
        elif self.mode == ResultUndoMode.MODIFY:
            self.mw.modify_results(self.results)
        # TODO: add merge
        else:
            raise NotImplementedError

    def undo(self):
        if self.mode == ResultUndoMode.ADD:
            self.mw.remove_results([r.id for r in self.results])
        elif self.mode == ResultUndoMode.REMOVE:
            self.mw.add_results(self.results)
        elif self.mode == ResultUndoMode.MODIFY:
            self.mw.modify_results(self.results_old)
        # TODO: add merge
        else:
            raise NotImplementedError
