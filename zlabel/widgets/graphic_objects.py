from typing import List, Tuple

import pyqtgraph as pg
from pyqtgraph.GraphicsScene.mouseEvents import (
    MouseClickEvent,
    MouseDragEvent,
    HoverEvent,
)
from pyqtgraph.graphicsItems.ROI import Handle
from qtpy.QtCore import QPointF, QRectF, Qt, Signal
from qtpy.QtGui import QBrush, QColor, QKeyEvent, QPainter, QPen
from qtpy.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsPathItem
from rich import print

from zlabel.utils.project import id_uuid4

from ..utils import ZLogger

logger = ZLogger("graphic_objects")


class Rectangle(pg.RectROI):
    sigHandleHovering = Signal(bool)

    def __init__(
        self,
        rect: QRectF,
        color: str = "#f47b90",
        centered=False,
        sideScalers=False,
        id_: str | None = None,
        **args,
    ):
        super().__init__(
            rect.topLeft().toTuple(),
            rect.size().toTuple(),
            centered=centered,
            sideScalers=sideScalers,
            **args,
        )
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.id = id_ or id_uuid4()
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(0.3)
        self._selected = False
        self._handle_hovering = False
        self.brush = QBrush(self.fill_color)

        self.selected_pen: QPen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen: QPen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen
        self.handlePen = pg.mkPen(color="black", width=2)
        self.default_scale_handles = [
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

        # self.setToolTip("Rectangle")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paint(self, p: QPainter, opt, widget):
        p.setBrush(self.brush)
        self.currentPen = self.pen
        if self._selected:
            self.currentPen = self.selected_pen
        # print(f"{self.id=}, {self._selected=}, {self.currentPen=}")
        super().paint(p, opt, widget)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            if not self._selected:
                self.setSelected(True)
            else:
                self.setSelected(False)
        super().mouseClickEvent(ev)

    def mouseDragEvent(self, ev: MouseDragEvent):
        # ev.accept()
        super().mouseDragEvent(ev)
        if ev.isStart():
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif ev.isFinish():
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def remove_handles(self):
        while self.handles:
            self.removeHandle(0)

    def restore_handles(self):
        for h in self.default_scale_handles:
            handle = self.addScaleHandle(h[0], h[1])
            if handle is not None:
                handle.sigHovering.connect(self.on_handle_mouse_hover)

    def on_handle_mouse_hover(self, hovering: bool = False):
        self._handle_hovering = hovering

    @property
    def is_handle_hovering(self):
        return self._handle_hovering

    def addHandle(self, info, index=None):
        info["item"] = ZHandle(
            self.handleSize,
            typ=info["type"],
            pen=self.handlePen,
            hoverPen=self.handleHoverPen,  # type: ignore
            parent=self,
        )
        super().addHandle(info, index)

    def setSelected(self, s: bool):
        self._selected = s
        if s:
            self.restore_handles()
        else:
            self.remove_handles()
        return super().setSelected(s)

    def area(self):
        state = self.getState()
        return state["size"].x() * state["size"].y()

    # def backup_handles(self, inplace=True):
    #     handles = [
    #         {
    #             "name": h.get("name", None),
    #             "type": h.get("type", None),
    #             "center": h.get("center", None),
    #             "pos": h.get("pos", None),
    #             "item": None,
    #             "lockAspect": h.get("lockAspect", False),
    #         }
    #         for h in self.handles
    #     ]
    #     if inplace:
    #         self.handles_bakup = handles
    #     return handles


class Polygon(pg.PolyLineROI):
    def __init__(
        self,
        positions: List[Tuple[float, float]],
        color: str = "#f47b90",
        id_: str | None = None,
        **args,
    ):
        super().__init__(positions, closed=False, pos=None, **args)
        self.fill_color = QColor(color)
        self.id = id_ or id_uuid4()


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
        self._selected = False
        self.id = id_ or id_uuid4()

        self.center = QPointF(pos[0] - radius, pos[1] - radius)
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(0.3)
        self.selected_pen: QPen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen: QPen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen
        self.brush = QBrush(self.fill_color)

        self.setPos(self.center)

        while self.handles:
            self.removeHandle(0)

    def setSelected(self, s: bool):
        self._selected = s
        return super().setSelected(s)

    def paint(self, p: QPainter, opt, widget):
        p.setBrush(self.brush)
        if self._selected:
            self.currentPen = self.selected_pen
        super().paint(p, opt, widget)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            if not self._selected:
                self.setSelected(True)
            else:
                self.setSelected(False)
        super().mouseClickEvent(ev)


class ZHandle(Handle):
    sigHovering = Signal(bool)

    def __init__(
        self,
        radius,
        typ=None,
        pen=...,
        hoverPen=...,
        parent=None,
        deletable=False,
    ):
        super().__init__(radius, typ, pen, hoverPen, parent, deletable)

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
