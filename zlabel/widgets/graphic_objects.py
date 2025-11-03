from typing import List, Tuple

import pyqtgraph as pg  # type: ignore
from pyqtgraph.graphicsItems.ROI import ROI, Handle
from pyqtgraph.GraphicsScene.mouseEvents import (
    HoverEvent,
    MouseClickEvent,
    MouseDragEvent,
)
from qtpy.QtCore import QPointF, QRectF, Qt, Signal
from qtpy.QtGui import QBrush, QColor, QKeyEvent, QPainter, QPen
from qtpy.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsPathItem
from rich import print

from zlabel.utils import id_uuid4, ZLogger


class Rectangle(pg.RectROI):
    def __init__(
        self,
        rect: QRectF,
        color: str = "#f47b90",
        centered=False,
        sideScalers=False,
        id_: str | None = None,
        **args,
    ):
        self.id_ = id_ or id_uuid4()
        super().__init__(
            rect.topLeft().toTuple(),
            rect.size().toTuple(),
            centered=centered,
            sideScalers=sideScalers,
            **args,
        )
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.logger = ZLogger(__name__)
        self.alpha_ = 0.1
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(self.alpha_)
        self._selected = False
        self.brush = QBrush(self.fill_color)

        self.selected_pen: QPen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen: QPen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen
        self.handlePen = pg.mkPen(color="black", width=2)
        self.scale_handles = [
            [[0.0, 0.0], [1.0, 1.0]],
            [[0.0, 0.5], [1.0, 0.5]],
            [[0.0, 1.0], [1.0, 0.0]],
            [[0.5, 0.0], [0.5, 1.0]],
            [[0.5, 1.0], [0.5, 0.0]],
            [[1.0, 0.0], [0.0, 1.0]],
            [[1.0, 0.5], [0.0, 0.5]],
            [[1.0, 1.0], [0.0, 0.0]],
        ]
        self.remove_handles()
        self.restore_handles()
        self.hide_handles()

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # def paint(self, p: QPainter, opt, widget):
    #     p.setBrush(self.brush)
    #     self.currentPen = self.pen
    #     if self._selected:
    #         self.currentPen = self.selected_pen
    #     # self.logger.debug(f"{self.id=}, {self._selected=}, {self.currentPen=}")
    #     super().paint(p, opt, widget)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            if not self._selected:
                self.setSelected(True)
            else:
                self.setSelected(False)
        super().mouseClickEvent(ev)

    def remove_handles(self):
        while self.handles:
            self.removeHandle(0)

    def restore_handles(self):
        for h in self.scale_handles:
            self.addScaleHandle(h[0], h[1])
            # if handle is not None:
            #     handle.sigHovering.connect(self.on_handle_mouse_hover)

    def show_handles(self):
        for h in self.handles:
            h["item"].show()

    def hide_handles(self):
        for h in self.handles:
            h["item"].hide()

    def setSelected(self, s: bool):
        self._selected = s
        return super().setSelected(s)

    def isSelected(self):
        return self._selected

    def area(self):
        state = self.getState()
        return state["size"].x() * state["size"].y()

    def set_fill_color(self, color: str):
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(self.alpha_)
        self.brush = QBrush(self.fill_color)
        self.pen = pg.mkPen(color, width=1)
        self.update()

    def getState(self):
        state = super().getState()
        state["id"] = self.id_
        return state

    def setState(self, state, update=True):
        super().setState(state, update)
        self.id_ = state["id"]
        self.hide_handles()


class Polygon(pg.PolyLineROI):
    def __init__(
        self,
        positions: List[Tuple[float, float]],
        closed: bool = False,
        pos: Tuple[float, float] | None = None,
        color: str = "#f47b90",
        id_: str | None = None,
        **args,
    ):
        self.id_ = id_ or id_uuid4()
        super().__init__(positions, closed=closed, pos=pos, **args)

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.logger = ZLogger(__name__)
        self.alpha_ = 0.1
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(self.alpha_)
        self.brush = QBrush(self.fill_color)
        self._selected = False

        self.selected_pen: QPen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen: QPen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen
        self.handlePen = pg.mkPen(color="black", width=2)

        self.hide_handles()

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            if not self.isSelected():
                self.setSelected(True)
            else:
                self.setSelected(False)
        super().mouseClickEvent(ev)

    # def paint(self, p: QPainter, opt, widget):  # type: ignore
    #     p.setBrush(self.brush)
    #     self.currentPen = self.pen
    #     if self.isSelected():
    #         self.currentPen = self.selected_pen
    #     super().paint(p, opt, widget)

    def set_fill_color(self, color: str):
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(self.alpha_)
        self.brush = QBrush(self.fill_color)
        self.pen = pg.mkPen(color, width=1)
        self.update()

    def show_handles(self):
        for h in self.handles:
            h["item"].show()

    def hide_handles(self):
        for h in self.handles:
            h["item"].hide()

    def setSelected(self, s: bool):
        self._selected = s
        return super().setSelected(s)

    def isSelected(self):
        return self._selected

    def getState(self):
        state = super().getState()
        state["id"] = getattr(self, "id_", None)
        return state

    def setState(self, state, update=False):  # update is not used
        super().setState(state)
        self.id_ = state["id"]
        self.hide_handles()


class Circle(pg.CircleROI):
    def __init__(
        self,
        pos: Tuple[float, float],
        radius: float = 1.0,
        color: str = "#f47b90",
        id_: str | None = None,
        **args,
    ):
        super().__init__(pos, radius=radius, **args)

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.id_ = id_ or id_uuid4()

        self.center = QPointF(pos[0] - radius, pos[1] - radius)
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(0.8)
        self.selected_pen: QPen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen: QPen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen
        self.brush = QBrush(self.fill_color)

        self.setPos(self.center)

        while self.handles:
            self.removeHandle(0)

    def paint(self, p: QPainter, opt, widget):
        p.setBrush(self.brush)
        if self.isSelected():
            self.currentPen = self.selected_pen
        super().paint(p, opt, widget)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            if not self.isSelected():
                self.setSelected(True)
            else:
                self.setSelected(False)
        super().mouseClickEvent(ev)


class ZHandle(Handle):
    sigHovering = Signal(bool)

    def __init__(
        self,
        radius: float,
        type=None,
        pen: QPen | None = None,
        hoverPen: QPen | None = None,
        parent=None,
        deletable: bool = False,
    ):
        super().__init__(radius, type, pen, hoverPen, parent, deletable)

    def hoverEvent(self, ev: HoverEvent):
        if ev.isEnter():
            self.sigHovering.emit(True)
        elif ev.isExit():
            self.sigHovering.emit(False)
        super().hoverEvent(ev)

    def paint(self, p, opt, widget):
        p.setRenderHints(p.RenderHint.Antialiasing, True)
        p.setPen(self.currentPen)
        fill_color = pg.mkColor(self.currentPen.color())
        fill_color.setAlphaF(0.5)
        brush = pg.mkBrush(fill_color)
        p.setBrush(brush)

        p.drawPath(self.shape())
