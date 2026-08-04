from enum import Enum

from pyqtgraph.Qt.QtGui import QUndoCommand

from zlabel.utils import PolygonResult, RectangleResult


class ResultUndoMode(Enum):
    ADD = 0
    REMOVE = 1
    MODIFY = 2
    MERGE = 3
    MODIFY_NO_UPDATE = 4


class ZResultUndoCmd(QUndoCommand):
    def __init__(
        self,
        mainwindow,
        results: list[RectangleResult | PolygonResult],
        mode: ResultUndoMode,
        results_old: list[RectangleResult | PolygonResult] | None = None,
    ):
        super().__init__()
        self.mw = mainwindow
        self.results = results
        self.results_old = results_old
        self.mode = mode
        # with modify, results_old must be provided
        assert results_old or self.mode != ResultUndoMode.MODIFY or self.mode == ResultUndoMode.MODIFY_NO_UPDATE

    def redo(self):
        if self.mode == ResultUndoMode.ADD:
            self.mw.add_results(self.results)
        elif self.mode == ResultUndoMode.REMOVE:
            self.mw.remove_results([r.id for r in self.results])
        elif self.mode == ResultUndoMode.MODIFY:
            self.mw.modify_results(self.results, update=True)
        elif self.mode == ResultUndoMode.MODIFY_NO_UPDATE:
            self.mw.modify_results(self.results, update=False)
        # TODO: add merge
        else:
            raise NotImplementedError

    def undo(self):
        if self.mode == ResultUndoMode.ADD:
            self.mw.remove_results([r.id for r in self.results])
        elif self.mode == ResultUndoMode.REMOVE:
            self.mw.add_results(self.results)
        elif self.mode == ResultUndoMode.MODIFY:
            self.mw.modify_results(self.results_old, update=False)
        elif self.mode == ResultUndoMode.MODIFY_NO_UPDATE:
            self.mw.modify_results(self.results_old, update=True)
        # TODO: add merge
        else:
            raise NotImplementedError
