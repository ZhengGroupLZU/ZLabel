"""Simple frame counter for the status-bar FPS indicator.

Based on the FrameCounter helper from pyqtgraph's examples/utils.py.
"""

from __future__ import annotations

from time import perf_counter

from pyqtgraph.Qt.QtCore import QObject, Signal

__all__ = ["FrameCounter"]


class FrameCounter(QObject):
    """Count paint/update calls and emit an FPS value on a fixed interval.

    The first :meth:`update` starts the internal Qt timer; every timer tick
    emits :attr:`sigFpsUpdate` with frames-per-second since the previous tick.
    """

    sigFpsUpdate = Signal(float)

    def __init__(self, interval: int = 1000, parent: QObject | None = None):
        super().__init__(parent)
        self._interval = interval
        self._count = 0
        self._last_update = 0.0
        self._timer_id: int | None = None

    def update(self) -> None:
        self._count += 1
        if self._last_update == 0.0:
            self._last_update = perf_counter()
            self._timer_id = self.startTimer(self._interval)

    def timerEvent(self, event) -> None:
        now = perf_counter()
        elapsed = now - self._last_update
        fps = self._count / elapsed if elapsed > 0 else 0.0
        self.sigFpsUpdate.emit(float(fps))
        self._last_update = now
        self._count = 0

    def stop(self) -> None:
        if self._timer_id is not None:
            self.killTimer(self._timer_id)
            self._timer_id = None
