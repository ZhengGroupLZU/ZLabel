import math
from typing import Any

import pyqtgraph as pg  # type: ignore
from pyqtgraph.graphicsItems.ROI import ROI, Handle
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent, MouseClickEvent
from pyqtgraph.Qt.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from pyqtgraph.Qt.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF
from pyqtgraph.Qt.QtWidgets import QGraphicsItem
from rich import print  # noqa: F401

from zlabel.utils import ZLogger, id_uuid4


class Rectangle(pg.RectROI):
    def __init__(
        self,
        rect: QRectF,
        color: str = "#f47b90",
        centered: bool = False,
        sideScalers: bool = False,
        id_: str | None = None,
        movable: bool = True,
        alpha: float = 0.3,
        **args,
    ):
        self.id_: str = id_ or id_uuid4()
        super().__init__(
            rect.topLeft().toTuple(),
            rect.size().toTuple(),
            centered=centered,
            sideScalers=sideScalers,
            antialias=False,
            hoverPen=pg.mkPen(color="w", width=3),
            handlePen=pg.mkPen(color="yellow", width=2),
            movable=movable,
            **args,
        )
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.logger: ZLogger = ZLogger(__name__)
        self.alpha: float = alpha
        self.fill_color: QColor = QColor(color)
        self.fill_color.setAlphaF(self.alpha)
        self._selected: bool = False
        self._update_pending: bool = False

        self.brush: QBrush = QBrush(self.fill_color)
        self.hoverPen.setStyle(Qt.PenStyle.DashLine)

        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

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
        self.removeHandles()
        self.restoreHandles()
        self.hideHandles()

        if self.translatable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            if self.translatable:
                if not self._selected:
                    self.setSelected(True)
                else:
                    self.setSelected(False)
            else:
                ev.ignore()
                return
        super().mouseClickEvent(ev)

    def mouseDragEvent(self, ev):
        if self.translatable:
            super().mouseDragEvent(ev)
        else:
            ev.ignore()

    def paint(self, p: QPainter, opt, widget):
        p.setBrush(self.brush)
        p.setPen(self.hoverPen if self.isSelected() else self.currentPen)
        super().paint(p, opt, widget)

    def removeHandles(self):
        while self.handles:
            self.removeHandle(0)

    def restoreHandles(self):
        for h in self.scale_handles:
            self.addScaleHandle(h[0], h[1])
            # if handle is not None:
            #     handle.sigHovering.connect(self.on_handle_mouse_hover)

    def showHandles(self):
        for h in self.handles:
            h["item"].show()

    def hideHandles(self):
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

    def setFillColor(self, color: str, alpha: float = 0.3):
        self.fill_color = QColor(color)
        self.alpha = alpha
        self.fill_color.setAlphaF(self.alpha)
        self.brush = QBrush(self.fill_color)
        self.scheduleUpdate()

    def scheduleUpdate(self):
        if not self._update_pending:
            self._update_pending = True
            QTimer.singleShot(0, self._doUpdate)

    def _doUpdate(self):
        self._update_pending = False
        self.update()

    def setMovable(self, movable: bool):
        self.translatable = movable
        if self.translatable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def getState(self):
        return {"id": self.id_, **super().getState()}

    def setState(self, state: dict[str, Any], update=True):
        super().setState(state, update)
        if state.get("id", None):
            self.id_ = state["id"]
        if self.isSelected():
            self.showHandles()
        else:
            self.hideHandles()


class Polygon(pg.ROI):
    def __init__(
        self,
        positions: list[tuple[float, float]],
        closed: bool = True,
        pos: tuple[float, float] = (0, 0),
        color: str = "#f47b90",
        id_: str | None = None,
        alpha: float = 0.3,
        **args,
    ):
        self.id_: str = id_ or id_uuid4()
        self.closed: bool = closed
        self.points = [pg.Point(p) for p in positions]
        ROI.__init__(
            self,
            pos,
            size=pg.Point([1, 1]),
            hoverPen=pg.mkPen(color="w", width=3),
            handlePen=pg.mkPen(color="yellow", width=2),
            **args,
        )
        self.state["id_"] = self.id_

        self.alpha: float = alpha
        self._selected: bool = False
        self._update_pending: bool = False

        self.fill_color: QColor = QColor(color)
        self.fill_color.setAlphaF(self.alpha)
        self.brush: QBrush = QBrush(self.fill_color)

    @property
    def handles_created(self):
        return len(self.handles) > 0

    def setPoints(self, points, closed: bool | None = None, update=True):
        """
        Set the complete sequence of points displayed by this ROI.

        ============= =========================================================
        **Arguments**
        points        List of (x,y) tuples specifying handle locations to set.
        closed        If bool, then this will set whether the ROI is closed
                      (the last point is connected to the first point). If
                      None, then the closed mode is left unchanged.
        ============= =========================================================

        """
        self.closed = closed or self.closed
        self.points = [pg.Point(p) for p in points]

        self.stateChanged(finish=update)

    def clearPoints(self, finish=True):
        self.points.clear()
        self.stateChanged(finish=finish)

    def setMovable(self, movable: bool):
        self.translatable = movable
        if self.translatable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def setSelected(self, s: bool):
        self._selected = s
        super().setSelected(s)

        if s and not self.handles_created:
            self._createHandles()
        elif s and self.handles_created:
            self.showHandles()
        elif not s and self.handles_created:
            self._removeHandles()

    def isSelected(self):
        return self._selected

    def getState(self):
        if self.handles:
            points = [pg.Point(h.pos()) for h in self.getHandles()]
        else:
            points = [pg.Point(p[0], p[1]) for p in self.points]

        return {
            **ROI.getState(self),
            "id": self.id_,
            "points": points,
            "closed": self.closed,
        }

    def saveState(self):
        state: dict[str, Any] = ROI.saveState(self)
        state["closed"] = self.closed
        state["id"] = self.id_

        if self.handles:
            state["points"] = [tuple(h.pos()) for h in self.getHandles()]
        else:
            state["points"] = [(p[0], p[1]) for p in self.points]

        return state

    def setState(self, state, update: bool = True):
        self.setPos(state["pos"], update=False)
        self.setSize(state["size"], update=False)
        self.setAngle(state["angle"], update=False)
        self.setPoints(state["points"], closed=state["closed"], update=False)
        if self.isSelected():
            self._createHandles()
        else:
            self._removeHandles()
        self.stateChanged(finish=update)

    def setMouseHover(self, hover):
        ROI.setMouseHover(self, hover)

    def addFreeHandle(
        self,
        pos=None,
        axes=None,
        item=None,
        name=None,
        index=None,
        finish=False,
    ):
        """
        Add a new free handle to the ROI. Dragging free handles has no effect
        on the position or shape of the ROI.

        =================== ====================================================
        **Arguments**
        pos                 (length-2 sequence) The position of the handle
                            relative to the shape of the ROI. A value of (0,0)
                            indicates the origin, whereas (1, 1) indicates the
                            upper-right corner, regardless of the ROI's size.
        item                The Handle instance to add. If None, a new handle
                            will be created.
        name                The name of this handle (optional). Handles are
                            identified by name when calling
                            getLocalHandlePositions and getSceneHandlePositions.
        =================== ====================================================
        """
        if pos is not None:
            pos = pg.Point(pos)
        return self.addHandle(
            {"name": name, "type": "f", "pos": pos, "item": item},
            index=index,
            finish=finish,
        )

    def addHandle(self, info, index=None, finish=False):
        # If a Handle was not supplied, create it now
        if "item" not in info or info["item"] is None:
            h = Handle(
                self.handleSize,
                typ=info["type"],
                pen=self.handlePen,
                hoverPen=self.handleHoverPen,
                parent=self,
                antialias=self._antialias,
            )
            info["item"] = h
        else:
            h = info["item"]
            if info["pos"] is None:
                info["pos"] = h.pos()
        h.setPos(info["pos"] * self.state["size"])

        # connect the handle to this ROI
        # iid = len(self.handles)
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)

        h.setZValue(self.zValue() + 1)
        h.sigRemoveRequested.connect(self.removeHandle)
        self.stateChanged(finish=finish)
        return h

    def removeHandle(self, handle, finish=False):
        """Remove a handle from this ROI. Argument may be either a Handle
        instance or the integer index of the handle."""
        index = self.indexOfHandle(handle)

        handle = self.handles[index]["item"]
        self.handles.pop(index)
        handle.disconnectROI(self)
        if len(handle.rois) == 0 and self.scene() is not None:
            self.scene().removeItem(handle)
        self.stateChanged(finish=finish)
        handle.sigRemoveRequested.disconnect(self.removeHandle)

    def hideHandles(self):
        for h in self.handles:
            h["item"].hide()

    def showHandles(self):
        for h in self.handles:
            h["item"].show()

    def paint(self, p: QPainter, opt, widget=None):
        # w: float, h: float
        w, h = self.state["size"]  # type: ignore
        r = QRectF(0, 0, w, h).normalized()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, self._antialias)
        p.setPen(self.hoverPen if self.isSelected() else self.currentPen)
        p.setBrush(self.brush)
        p.translate(r.left(), r.top())
        p.scale(r.width(), r.height())

        if len(self.handles) > 1:
            # Use actual handle item positions so the drawing reflects edits immediately
            polygon = QPolygonF([QPointF(h["item"].pos().x(), h["item"].pos().y()) for h in self.handles])
        else:
            polygon = QPolygonF([QPointF(p[0], p[1]) for p in self.points])
        if self.closed:
            p.drawPolygon(polygon)
        else:
            p.drawPolyline(polygon)

    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        p = QPainterPath()

        points_to_use = []
        if self.points:
            points_to_use = [QPointF(p[0], p[1]) for p in self.points]
        elif len(self.handles) > 0:
            points_to_use = [h["item"].pos() for h in self.handles]

        if not points_to_use:
            return p

        p.moveTo(points_to_use[0])
        for i in range(1, len(points_to_use)):
            p.lineTo(points_to_use[i])
        if self.closed and len(points_to_use) > 2:
            p.lineTo(points_to_use[0])
        return p

    def area(self) -> float:
        """area = 1/2 * |Σ(x_i * y_{i+1} - x_{i+1} * y_i)|"""
        if self.points:
            points = self.points
        elif len(self.handles) >= 3:
            points = [(h["item"].pos().x(), h["item"].pos().y()) for h in self.handles]
        else:
            return 0.0

        if not self.closed or len(points) < 3:
            return 0.0

        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]

        return abs(area) / 2.0

    def getArrayRegion(self, *args, **kwds):
        return self._getArrayRegionForArbitraryShape(*args, **kwds)

    def setPen(self, *args, **kwds):
        ROI.setPen(self, *args, **kwds)

    def setFillColor(self, color: str, alpha: float = 0.3):
        self.fill_color = QColor(color)
        self.alpha = alpha
        self.fill_color.setAlphaF(self.alpha)
        self.brush = QBrush(self.fill_color)
        self.scheduleUpdate()

    def scheduleUpdate(self):
        if not self._update_pending:
            self._update_pending = True
            QTimer.singleShot(0, self._doUpdate)

    def _doUpdate(self):
        self._update_pending = False
        self.update()

    def _point_to_line_distance(
        self,
        point: QPointF,
        line_start: QPointF,
        line_end: QPointF,
    ) -> tuple[float, QPointF]:
        line_vec = QPointF(line_end.x() - line_start.x(), line_end.y() - line_start.y())
        point_vec = QPointF(point.x() - line_start.x(), point.y() - line_start.y())

        line_len_sq = line_vec.x() * line_vec.x() + line_vec.y() * line_vec.y()

        if line_len_sq == 0:
            distance = math.sqrt((point.x() - line_start.x()) ** 2 + (point.y() - line_start.y()) ** 2)
            return distance, line_start

        t = (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y()) / line_len_sq

        t = max(0.0, min(1.0, t))

        closest_point = QPointF(line_start.x() + t * line_vec.x(), line_start.y() + t * line_vec.y())

        distance = math.sqrt((point.x() - closest_point.x()) ** 2 + (point.y() - closest_point.y()) ** 2)

        return distance, closest_point

    def _find_closest_edge(
        self,
        click_pos: QPointF,
        tolerance: float = 5.0,
    ) -> tuple[int, QPointF] | None:
        if self.points:
            points = [QPointF(p[0], p[1]) for p in self.points]
        elif len(self.handles) >= 2:
            points = [h["item"].pos() for h in self.handles]
        else:
            return None

        min_distance = float("inf")
        closest_edge_index = -1
        closest_point: QPointF | None = None

        num_points = len(points)
        for i in range(num_points):
            if not self.closed and i == num_points - 1:
                break

            start_point = points[i]
            end_point = points[(i + 1) % num_points]

            distance, nearest_point = self._point_to_line_distance(click_pos, start_point, end_point)

            if distance < min_distance and distance <= tolerance:
                min_distance = distance
                closest_edge_index = i
                closest_point = nearest_point

        if closest_edge_index >= 0 and closest_point is not None:
            return closest_edge_index, closest_point
        return None

    def _insert_point_at_edge(self, edge_index: int, new_point: QPointF):
        if edge_index < 0 or edge_index >= len(self.handles):
            return

        self.addFreeHandle(pos=new_point, index=edge_index + 1)
        # current_points = []
        # for handle in self.handles:
        #     pos = handle["item"].pos()
        #     current_points.append((pos.x(), pos.y()))

        # new_points = (
        #     current_points[: edge_index + 1]
        #     + [(new_point.x(), new_point.y())]
        #     + current_points[edge_index + 1 :]
        # )

        # self.setPoints(new_points, closed=self.closed)

        if self.isSelected():
            self.showHandles()

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            if ev.double() and self.translatable:
                click_pos = ev.pos()
                edge_info = self._find_closest_edge(click_pos, tolerance=10.0)

                if edge_info:
                    edge_index, insert_point = edge_info
                    if not self.handles_created:
                        self._createHandles()
                    self._insert_point_at_edge(edge_index, insert_point)
                    self.stateChangeFinished()
                    ev.accept()
                    return

            if self.translatable:
                if not self._selected:
                    self.setSelected(True)
                else:
                    self.setSelected(False)
                self.sigClicked.emit(self, ev)
            else:
                ev.ignore()
                return

        super().mouseClickEvent(ev)

    def mouseDragEvent(self, ev):
        if self.translatable:
            return super().mouseDragEvent(ev)
        else:
            ev.ignore()
            return super().mouseDragEvent(ev)

    def _createHandles(self):
        if self.handles_created:
            return

        if self.handles:
            self._removeHandles()
        for p in self.points:
            self.addFreeHandle(p, finish=False)
        self.stateChanged(finish=False)

    def _removeHandles(self):
        if not self.handles_created:
            return

        self.points = [pg.Point(h["item"].pos().x(), h["item"].pos().y()) for h in self.handles]

        while self.handles:
            self.removeHandle(0)


class Circle(pg.CircleROI):
    def __init__(
        self,
        pos: tuple[float, float],
        radius: float = 1.0,
        color: str = "#f47b90",
        id_: str | None = None,
        **args,
    ):
        super().__init__(
            pos,
            radius=radius,
            hoverPen=pg.mkPen(color="w", width=3),
            handlePen=pg.mkPen(color="yellow", width=2),
            **args,
        )

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.id_ = id_ or id_uuid4()

        self.center = QPointF(pos[0] - radius, pos[1] - radius)
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(0.8)
        self.brush = QBrush(self.fill_color)

        self.setPos(self.center)

        while self.handles:
            self.removeHandle(0)

    def paint(self, p: QPainter, opt, widget):
        p.setBrush(self.brush)
        if self.isSelected():
            self.currentPen = self.hoverPen
        super().paint(p, opt, widget)

    def mouseClickEvent(self, ev: MouseClickEvent):
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
        self.polygon_parent = None
        self.vertex_index = None

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
