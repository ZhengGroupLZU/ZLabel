from typing import List, Tuple

import pyqtgraph as pg  # type: ignore
from pyqtgraph.graphicsItems.ROI import Handle  # type: ignore
from pyqtgraph.GraphicsScene.mouseEvents import (  # type: ignore
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

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paint(self, p: QPainter, opt, widget):
        p.setBrush(self.brush)
        self.currentPen = self.pen
        if self._selected:
            self.currentPen = self.selected_pen
        # self.logger.debug(f"{self.id=}, {self._selected=}, {self.currentPen=}")
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
        # if ev.isFinish():
        #     self.setCursor(Qt.CursorShape.PointingHandCursor)
        # else:
        #     self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def remove_handles(self):
        while self.handles:
            self.removeHandle(0)

    def restore_handles(self):
        for h in self.default_scale_handles:
            handle = self.addScaleHandle(h[0], h[1])
            # if handle is not None:
            #     handle.sigHovering.connect(self.on_handle_mouse_hover)

    def addHandle(self, info, index=None):
        # overwrite default behavior, do not emit regionchanged/finished/started signal
        info["item"] = ZHandle(
            self.handleSize,
            typ=info["type"],
            pen=self.handlePen,
            hoverPen=self.handleHoverPen,  # type: ignore
            parent=self,
        )
        h = info["item"]
        if info["pos"] is None:
            info["pos"] = h.pos()
        h.setPos(info["pos"] * self.state["size"])

        ## connect the handle to this ROI
        # iid = len(self.handles)
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)
        h.setZValue(self.zValue() + 1)
        # self.stateChanged()
        return h

    def removeHandle(self, handle):
        """Remove a handle from this ROI. Argument may be either a Handle
        instance or the integer index of the handle."""
        index = self.indexOfHandle(handle)

        handle = self.handles[index]["item"]
        self.handles.pop(index)
        handle.disconnectROI(self)
        if len(handle.rois) == 0 and self.scene() is not None:
            self.scene().removeItem(handle)
        # self.stateChanged()

    def setSelected(self, s: bool):
        self._selected = s
        if s:
            self.restore_handles()
        else:
            self.remove_handles()
        return super().setSelected(s)

    def is_selected(self):
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

    # def set_visible(self, v: bool = True):
    #     state = self.getState()
    #     state["pos"] = QPointF(0, 0)
    #     state["size"] = QPointF(0, 0)
    #     self.setState(state)

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
