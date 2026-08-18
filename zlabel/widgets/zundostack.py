from enum import Enum

from pyqtgraph.Qt.QtGui import QUndoCommand

from zlabel.utils import PointResult, PolygonResult, RectangleResult


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
        results: list[PointResult | RectangleResult | PolygonResult],
        mode: ResultUndoMode,
        results_old: list[PointResult | RectangleResult | PolygonResult] | None = None,
        target_anno=None,
        instances_old: dict[int, str] | None = None,
        instances_new: dict[int, str] | None = None,
    ):
        super().__init__()
        self.mw = mainwindow
        self.results = results
        self.results_old = results_old
        self.mode = mode
        # cell-move (renumber/swap) ops mutate an arbitrary frame's anno; when
        # ``target_anno`` is set, redo/undo write the results and the per-instance
        # status map directly into it (bypassing the crt_anno canvas path).
        self.target_anno = target_anno
        self.instances_old = instances_old or {}
        self.instances_new = instances_new or {}
        # with modify, results_old must be provided
        assert results_old or self.mode != ResultUndoMode.MODIFY or self.mode == ResultUndoMode.MODIFY_NO_UPDATE

    def _apply(self, results_snapshot, instances_snapshot):
        for r in results_snapshot:
            self.target_anno.results[r.id] = r
        self.target_anno.instances.clear()
        self.target_anno.instances.update(instances_snapshot)
        self.mw._refresh_tracks()
        if self.mw.proj.crt_anno is self.target_anno:
            self.mw._refresh_anno_tree()

    def redo(self):
        if self.target_anno is not None:
            self._apply(self.results, self.instances_new)
            return
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
        if self.target_anno is not None:
            self._apply(self.results_old, self.instances_old)
            return
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
