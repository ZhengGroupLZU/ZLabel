import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ROI import Handle
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent, MouseClickEvent, MouseDragEvent
from pyqtgraph.Qt.QtCore import QCoreApplication, QPoint, QPointF, QRectF, Qt, QTimer, Signal
from pyqtgraph.Qt.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QTransform
from pyqtgraph.Qt.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QMenu,
    QStyleOptionGraphicsItem,
    QWidget,
)

from zlabel.utils import ZLogger, id_uuid4


class InstanceBBox(QGraphicsRectItem):
    """Dashed axis-aligned bbox + object-detection style label.

    Used for polygon instances: the bbox spans every member polygon (the union
    / maximum bounding box). The label has a solid colored background and text
    in ``{ID} {label}`` format, e.g. ``1 Normal seed``.
    """

    def __init__(self):
        super().__init__()
        self.instance_id: int = 0
        self.label: str = ""
        self.label_color: str | None = None
        self.label_bg = QGraphicsRectItem()
        self.label_bg.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.label_bg.setPen(Qt.PenStyle.NoPen)
        self.label_bg.setVisible(False)
        self.label_text = QGraphicsSimpleTextItem()
        self.label_text.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.label_text.setVisible(False)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setBrush(Qt.BrushStyle.NoBrush)

    def set_instance(self, instance_id: int, rect: QRectF, color: str | None, label: str = ""):
        self.instance_id = instance_id
        self.label = label or ""
        self.label_color = color or "#888888"
        self.setRect(rect)
        pen = QPen(QColor(self.label_color))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(0)  # cosmetic pen -> constant screen width
        self.setPen(pen)
        self._update_label_layout()
        self.setVisible(True)

    def _update_label_layout(self):
        if self.scene() is None:
            return
        # Add the top-level label items to the scene once.
        for item in (self.label_bg, self.label_text):
            if item.scene() is None:
                self.scene().addItem(item)
                item.setZValue(self.zValue() + 0.6 if item is self.label_bg else self.zValue() + 0.61)

        # Object-detection style: solid background outside the bbox top-left.
        text = " ".join(x for x in (str(self.instance_id), self.label) if x)
        self.label_text.setText(text)
        self.label_text.setBrush(QColor("#ffffff"))
        text_rect = self.label_text.boundingRect()

        # Top-level items ignoring transforms use scene coordinates directly.
        # When the canvas is rotated, choose the corner that is visually the
        # top-left on screen (smallest y, then smallest x).
        rect = self.rect()
        corners = (
            QPointF(rect.left(), rect.top()),
            QPointF(rect.right(), rect.top()),
            QPointF(rect.left(), rect.bottom()),
            QPointF(rect.right(), rect.bottom()),
        )
        top_left = min((self.mapToScene(c) for c in corners), key=lambda p: (p.y(), p.x()))
        pad_x, pad_y = 2.0, 2.0
        label_pos = QPointF(
            top_left.x() + pad_x,
            top_left.y() - text_rect.height() - pad_y,
        )
        self.label_text.setPos(label_pos)

        color = QColor(self.label_color or "#888888")
        self.label_bg.setBrush(QBrush(color))
        self.label_bg.setRect(text_rect.adjusted(-pad_x, -pad_y, pad_x, pad_y))
        self.label_bg.setPos(label_pos)
        self.label_bg.setVisible(True)
        self.label_text.setVisible(True)

    def remove_label_items(self):
        for item in (self.label_bg, self.label_text):
            if item.scene() is not None:
                item.scene().removeItem(item)

    def paint(self, painter, option, widget=None):
        # Recompute the label position using the current view transform before
        # drawing so the constant-size text stays outside the bbox top-left.
        self._update_label_layout()
        super().paint(painter, option, widget)


class ZROI(pg.ROI):
    def __init__(
        self,
        pos: Sequence[float],
        size: pg.Point | tuple[float, float] | Sequence[float] | None = None,
        angle: float = 0.0,
        invertible: bool = False,
        maxBounds: QRectF | None = None,
        snapSize: float = 1.0,
        scaleSnap: bool = False,
        translateSnap: bool = False,
        rotateSnap: bool = False,
        parent: QGraphicsItem | None = None,
        pen: QPen | None = None,
        hoverPen: QPen | None = None,
        handlePen: QPen | None = None,
        handleHoverPen: QPen | None = None,
        movable: bool = True,
        rotatable: bool = True,
        resizable: bool = True,
        removable: bool = False,
        aspectLocked: bool = False,
        antialias: bool = True,
    ):
        self.handles: list[dict[str, Any]]
        super().__init__(
            pos,
            size or pg.Point(1, 1),
            angle,
            invertible,
            maxBounds,
            snapSize,
            scaleSnap,
            translateSnap,
            rotateSnap,
            parent,
            pen,
            hoverPen,
            handlePen,
            handleHoverPen,
            movable,
            rotatable,
            resizable,
            removable,
            aspectLocked,
            antialias,
        )
        self._init_instance_label()
        self.sigRegionChanged.connect(self._update_instance_label)

    # region instance id label
    def _init_instance_label(self):
        self.instance_id: int = 0
        self.label_color: str | None = None
        self.label_text: QGraphicsSimpleTextItem | None = None

    def set_instance_label(self, instance_id: int, color: str | None):
        self.instance_id = instance_id
        self.label_color = color
        self._update_instance_label()

    def _instance_label_pos(self) -> tuple[float, float]:
        return 0.0, 0.0

    def _update_instance_label(self):
        if self.instance_id:
            if self.label_text is None:
                self.label_text = QGraphicsSimpleTextItem(self)
                self.label_text.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            self.label_text.setText(str(self.instance_id))
            if self.label_color:
                self.label_text.setBrush(QColor(self.label_color))
            self.label_text.setPos(*self._instance_label_pos())
            self.label_text.setVisible(True)
        elif self.label_text is not None:
            self.label_text.setVisible(False)

    # endregion

    @property
    def handles_created(self):
        return len(self.handles) > 0

    def indexOfHandle(self, handle: "Handle | ZHandle | int") -> int:
        """
        Return the index of *handle* in the list of this ROI's handles.
        """
        assert isinstance(handle, (Handle, ZHandle, int))
        if isinstance(handle, int):
            return handle
        for i, info in enumerate(self.handles):
            if info["item"] is handle:
                return i
        raise Exception("Cannot return handle index; not attached to this ROI")


class Rectangle(ZROI):
    def __init__(
        self,
        rect: QRectF,
        color: str = "#f47b90",
        id_: str | None = None,
        movable: bool = True,
        alpha: float = 0.3,
    ):
        self.id_: str = id_ or id_uuid4()
        super().__init__(
            rect.topLeft().toTuple(),
            rect.size().toTuple(),
            antialias=False,
            hoverPen=pg.mkPen(color="w", width=3),
            handlePen=pg.mkPen(color="yellow", width=2),
            movable=movable,
            removable=False,
        )
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.logger: ZLogger = ZLogger(__name__)
        self.alpha: float = alpha
        self.fill_color: QColor = QColor(color)
        self.fill_color.setAlphaF(self.alpha)
        self._selected: bool = False

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

        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _instance_label_pos(self) -> tuple[float, float]:
        return 2.0, 2.0

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

    def mouseDragEvent(self, ev: MouseDragEvent):
        if self.translatable:
            super().mouseDragEvent(ev)
        else:
            ev.ignore()

    def paint(self, p: QPainter, opt: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        p.setBrush(self.brush)
        p.setPen(self.hoverPen if self.isSelected() else self.currentPen)
        super().paint(p, opt, widget)

    def addHandle(self, info: dict[str, Any], index: int | None = None):
        # If a Handle was not supplied, create it now
        if "item" not in info or info["item"] is None:
            h = ZHandle(
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
        self.stateChanged()
        return h

    def removeHandles(self):
        while self.handles:
            self.removeHandle(0)

    def restoreHandles(self):
        for h in self.scale_handles:
            self.addScaleHandle(h[0], h[1])
            # if handle is not None:
            #     handle.sigHovering.connect(self.on_handle_mouse_hover)

    def setSelected(self, s: bool):
        self._selected = s
        if self.isSelected():
            self.restoreHandles()
        else:
            self.removeHandles()
        return super().setSelected(s)

    def isSelected(self):
        return self._selected

    def area(self) -> float:
        state = self.getState()
        return state["size"].x() * state["size"].y()

    def setFillColor(self, color: str, alpha: float = 0.3):
        self.fill_color = QColor(color)
        self.alpha = alpha
        self.fill_color.setAlphaF(self.alpha)
        self.brush = QBrush(self.fill_color)
        self.update()

    def setMovable(self, movable: bool):
        self.translatable = movable
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def getState(self) -> dict[str, Any]:
        return {"id": self.id_, **super().getState()}

    def saveState(self) -> dict[str, Any]:
        return {"id": self.id_, **super().saveState()}

    def setState(self, state: dict[str, Any], update: bool = True):
        super().setState(state, update)
        if state.get("id", None):
            self.id_ = state["id"]
        if self.isSelected():
            self.restoreHandles()
        else:
            self.removeHandles()


_USE_FILL_EDGE = object()


class Polygon(ZROI):
    def __init__(
        self,
        positions: list[tuple[float, float]],
        closed: bool = True,
        pos: tuple[float, float] = (0, 0),
        color: str = "#f47b90",
        id_: str | None = None,
        alpha: float = 0.3,
        use_catmull_rom_path: bool = True,
        edge_color: str | object | None = _USE_FILL_EDGE,
        **args,
    ):
        self.id_: str = id_ or id_uuid4()
        self.closed: bool = closed
        self.points = [pg.Point(p) for p in positions]
        self.state: dict[str, Any]
        super().__init__(
            pos,
            hoverPen=pg.mkPen(color="w", width=3),
            handlePen=pg.mkPen(color="yellow", width=2),
            removable=False,
            **args,
        )
        self.state["id_"] = self.id_

        self.alpha: float = alpha
        self.use_catmull_rom_path: bool = use_catmull_rom_path
        self._selected: bool = False

        self.fill_color: QColor = QColor(color)
        self.fill_color.setAlphaF(self.alpha)
        self.brush: QBrush = QBrush(self.fill_color)
        if edge_color is _USE_FILL_EDGE:
            self.edge_color: str = color or "#ffffff"
        else:
            self.edge_color: str = edge_color or "#ffffff"

    def catmull_rom_path(self, points: list[QPointF], closed: bool = True, alpha: float = 1.0):
        n = len(points)
        path = QPainterPath()
        if n == 0:
            return path
        if n == 1:
            path.moveTo(points[0])
            return path
        if n == 2:
            path.moveTo(points[0])
            path.lineTo(points[1])
            return path
        factor = alpha / 6.0
        if closed:
            path.moveTo(points[0])
            for i in range(n):
                p0 = points[(i - 1) % n]
                p1 = points[i]
                p2 = points[(i + 1) % n]
                p3 = points[(i + 2) % n]
                c1 = QPointF(p1.x() + (p2.x() - p0.x()) * factor, p1.y() + (p2.y() - p0.y()) * factor)
                c2 = QPointF(p2.x() - (p3.x() - p1.x()) * factor, p2.y() - (p3.y() - p1.y()) * factor)
                path.cubicTo(c1, c2, p2)
            path.closeSubpath()
        else:
            path.moveTo(points[0])
            for i in range(n - 1):
                p0 = points[i - 1] if i > 0 else points[i]
                p1 = points[i]
                p2 = points[i + 1]
                p3 = points[i + 2] if i + 2 < n else points[i + 1]
                c1 = QPointF(p1.x() + (p2.x() - p0.x()) * factor, p1.y() + (p2.y() - p0.y()) * factor)
                c2 = QPointF(p2.x() - (p3.x() - p1.x()) * factor, p2.y() - (p3.y() - p1.y()) * factor)
                path.cubicTo(c1, c2, p2)
        return path

    def setPoints(self, points: list[tuple[float, float]], closed: bool | None = None, update: bool = True):
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

    def clearPoints(self, finish: bool = True):
        self.points.clear()
        self.stateChanged(finish=finish)

    def setMovable(self, movable: bool):
        self.translatable = movable
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def setSelected(self, s: bool):
        self._selected = s
        super().setSelected(s)

        if s and not self.handles_created:
            self.createHandles()
        elif s and self.handles_created:
            self.showHandles()
        elif not s and self.handles_created:
            self.hideHandles()
        else:
            ...

    def isSelected(self):
        return self._selected

    def getState(self) -> dict[str, Any]:
        if self.handles:
            points = [pg.Point(h["pos"]) for h in self.handles]
        else:
            points = [pg.Point(p[0], p[1]) for p in self.points]

        return {
            **super().getState(),
            "id": self.id_,
            "points": points,
            "closed": self.closed,
        }

    def saveState(self):
        state: dict[str, Any] = {"id": self.id_, "closed": self.closed, **super().saveState()}

        if self.handles:
            state["points"] = [(h["pos"].x(), h["pos"].y()) for h in self.handles]
        else:
            state["points"] = [(p[0], p[1]) for p in self.points]

        return state

    def setState(self, state: dict[str, Any], update: bool = True):
        pos = state["pos"]
        points = [pg.Point(p) if not hasattr(p, "x") else pg.Point(p.x(), p.y()) for p in state["points"]]
        if pos.x() != 0 or pos.y() != 0:
            # legacy/moved ROIs may carry a non-zero origin; fold it back into
            # the points so stored data stays in absolute image coordinates
            points = [pg.Point(p.x() + pos.x(), p.y() + pos.y()) for p in points]
            pos = pg.Point(0, 0)
        was_selected = self.isSelected()
        if was_selected:
            # Drop stale handles first: removeHandles() would capture their
            # (now out-of-date) local positions back into self.points, so clear
            # them explicitly and re-create from the new vertex list below.
            while self.handles:
                self.removeHandle(0)
        self.setPos(pos, update=False)
        self.setSize(state["size"], update=False)
        self.setAngle(state["angle"], update=False)
        self.setPoints(points, closed=state["closed"], update=False)
        if was_selected:
            self.createHandles()
        else:
            self.removeHandles()
        self.stateChanged(finish=update)

    def setMouseHover(self, hover):
        super().setMouseHover(hover)

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
            h = ZHandle(
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

    def _instance_label_pos(self) -> tuple[float, float]:
        pts = self.getState().get("points") or []
        if pts:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            return float(min(xs)), float(min(ys))
        return 0.0, 0.0

    def _update_instance_label(self):
        # Polygon instance labels are rendered by the canvas-level InstanceBBox,
        # so individual polygon items must not draw their own number.
        pass

    def paint(self, p: QPainter, opt, widget=None):
        # w: float, h: float
        w, h = self.state["size"]  # type: ignore
        r = QRectF(0, 0, w, h).normalized()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, self._antialias)
        if self.isSelected():
            p.setPen(self.hoverPen)
        else:
            edge_pen = QPen(self.currentPen)
            edge_pen.setColor(QColor(self.edge_color))
            p.setPen(edge_pen)
        p.setBrush(self.brush)
        p.translate(r.left(), r.top())
        p.scale(r.width(), r.height())

        # Use actual handle item positions so the drawing reflects edits immediately
        points: list[QPointF]
        if len(self.handles) > 1:
            points = [QPointF(h["item"].pos().x(), h["item"].pos().y()) for h in self.handles]
        else:
            points = [QPointF(p.x(), p.y()) for p in self.points]

        if self.use_catmull_rom_path:
            path = self.catmull_rom_path(points)
            p.drawPath(path)
        else:
            polygon = QPolygonF(points)

            if self.closed:
                p.drawPolygon(polygon, fillRule=Qt.FillRule.WindingFill)
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

    def getArrayRegion(self, data, img, axes=(0, 1), returnMappedCoords=False, **kwds):
        return self._getArrayRegionForArbitraryShape(data, img, axes, returnMappedCoords, **kwds)

    def setFillColor(self, color: str, alpha: float = 0.3):
        self.fill_color = QColor(color)
        self.alpha = alpha
        self.fill_color.setAlphaF(self.alpha)
        self.brush = QBrush(self.fill_color)
        self.edge_color = color or "#ffffff"
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
                        self.createHandles()
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

    def mouseDragEvent(self, ev: MouseDragEvent):
        if self.translatable:
            return super().mouseDragEvent(ev)
        else:
            ev.ignore()
            return super().mouseDragEvent(ev)

    def createHandles(self):
        if self.handles_created:
            return

        if self.handles:
            self.removeHandles()
        for p in self.points:
            self.addFreeHandle(p, finish=False)
        self.stateChanged(finish=False)

    def removeHandles(self):
        if not self.handles_created:
            return

        self.points = [pg.Point(h["item"].pos().x(), h["item"].pos().y()) for h in self.handles]

        while self.handles:
            self.removeHandle(0)


class Point(ZROI):
    r"""
    Point ROI subclass with one scale handle and one rotation handle.


    ============== =============================================================
    **Arguments**
    pos            (length-2 sequence) The position of the ROI's origin.
    size           (length-2 sequence) The size of the ROI's bounding rectangle.
    \**args        All extra keyword arguments are passed to ROI()
    ============== =============================================================

    """

    def __init__(
        self,
        pos: tuple[float, float],
        radius: float = 1.0,
        color: str = "#f47b90",
        id_: str | None = None,
    ):
        self.path = None
        # Set before super().__init__: pg.ROI calls getState() during init.
        self.radius: float = radius
        self.visible: int = 1  # COCO keypoint visibility: 0/1/2
        super().__init__(
            pos,
            (radius * 2, radius * 2),
            aspectLocked=True,
            hoverPen=pg.mkPen(color="w", width=3),
            handlePen=pg.mkPen(color="yellow", width=2),
            removable=False,
        )
        self.sigRegionChanged.connect(self._clearPath)

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.id_ = id_ or id_uuid4()
        self._selected: bool = False

        self.center = QPointF(pos[0] - radius, pos[1] - radius)
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(0.8)
        self.brush = QBrush(self.fill_color)

        self.setPos(self.center)

    def setSelected(self, s: bool):
        self._selected = s
        return super().setSelected(s)

    def isSelected(self):
        return self._selected

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

    def _instance_label_pos(self) -> tuple[float, float]:
        return 0.0, 0.0

    def set_visible(self, v: int):
        self.visible = int(v)
        if self.visible == 2:  # occluded: hollow
            self.brush = QBrush(Qt.BrushStyle.NoBrush)
        else:
            self.fill_color.setAlphaF(0.3 if self.visible == 0 else 0.8)
            self.brush = QBrush(self.fill_color)
        self.update()

    def setMovable(self, movable: bool):
        self.translatable = movable
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_radius(self, r: float):
        """Resize the point while keeping its center fixed."""
        r = max(float(r), 1e-3)
        center = self.state["pos"] + pg.Point(self.radius, self.radius)  # type: ignore[attr-defined]
        self.radius = r
        self.setSize((r * 2, r * 2), update=False)
        self.setPos(center - pg.Point(r, r), update=False)
        self._clearPath()  # cached hit-test shape no longer matches the new size
        self.update()

    def setFillColor(self, color: QColor | str, alpha: float = 0.8):
        # Keep keypoint fill opaque regardless of the fill `alpha` used for
        # rectangles/polygons; visibility only follows the COCO visible state.
        self.fill_color = QColor(color)
        if self.visible == 2:  # occluded: hollow
            self.brush = QBrush(Qt.BrushStyle.NoBrush)
        else:
            self.fill_color.setAlphaF(0.3 if self.visible == 0 else 0.8)
            self.brush = QBrush(self.fill_color)
        self.update()

    def getState(self) -> dict[str, Any]:
        # pg.ROI.pos() and stateChanged() call getState(), possibly during
        # super().__init__(), so tolerate attributes that are not set yet.
        radius = getattr(self, "radius", 1.0)
        p = self.state["pos"]  # type: ignore[attr-defined]
        c = p + pg.Point(radius, radius)
        return {
            "id": getattr(self, "id_", ""),
            "pos": pg.Point(c.x(), c.y()),
            "visible": getattr(self, "visible", 1),
        }

    def saveState(self):
        return self.getState()

    def setState(self, state: dict[str, Any], update: bool = True):
        self.id_ = state.get("id", self.id_)
        self.set_visible(state.get("visible", self.visible))
        if "pos" in state:
            p = state["pos"]
            self.setPos(QPointF(p.x() - self.radius, p.y() - self.radius))
        self.update()

    def _clearPath(self):
        self.path = None

    def paint(self, p, opt, widget):
        r = self.boundingRect()

        p.setRenderHint(QPainter.RenderHint.Antialiasing, self._antialias)
        if self.isSelected():
            p.setPen(pg.mkPen(color="#ffff00", width=3))
        else:
            p.setPen(self.currentPen)
        p.setBrush(self.brush)
        p.scale(r.width(), r.height())  # workaround for GL bug
        r = QRectF(r.x() / r.width(), r.y() / r.height(), 1, 1)
        p.drawEllipse(r)

    def getArrayRegion(self, arr: np.ndarray, img=None, axes=(0, 1), returnMappedCoords=False, **kwds):
        """
        Return the result of :meth:`~pyqtgraph.ROI.getArrayRegion` masked by the
        point shape of the ROI. Regions outside the point are set to 0.

        See :meth:`~pyqtgraph.ROI.getArrayRegion` for a description of the
        arguments.

        Note: ``returnMappedCoords`` is not yet supported for this ROI type.
        """
        # Note: we could use the same method as used by PolyLineROI, but this
        # implementation produces a nicer mask.
        if returnMappedCoords:
            arr, mappedCoords = super().getArrayRegion(arr, img, axes, returnMappedCoords, **kwds)
        else:
            arr = super().getArrayRegion(arr, img, axes, returnMappedCoords, **kwds)
        if arr is None or arr.shape[axes[0]] == 0 or arr.shape[axes[1]] == 0:
            if returnMappedCoords:
                return arr, mappedCoords
            else:
                return arr
        w = arr.shape[axes[0]]
        h = arr.shape[axes[1]]

        # generate an ellipsoidal mask
        mask = np.fromfunction(
            lambda x, y: np.hypot(((x + 0.5) / (w / 2.0) - 1), ((y + 0.5) / (h / 2.0) - 1)) < 1,
            (w, h),
        )

        # reshape to match array axes
        if axes[0] > axes[1]:
            mask = mask.T
        shape = [(n if i in axes else 1) for i, n in enumerate(arr.shape)]
        mask = mask.reshape(shape)

        if returnMappedCoords:
            return arr * mask, mappedCoords
        else:
            return arr * mask

    def shape(self):
        if self.path is None:
            path = QPainterPath()

            # Note: Qt has a bug where very small ellipses (radius <0.001) do
            # not correctly intersect with mouse position (upper-left and
            # lower-right quadrants are not clickable).
            # path.addEllipse(self.boundingRect())

            # Workaround: manually draw the path.
            br = self.boundingRect()
            center = br.center()
            r1 = br.width() / 2.0
            r2 = br.height() / 2.0
            theta = np.linspace(0, 2 * np.pi, 24)
            x = center.x() + r1 * np.cos(theta)
            y = center.y() + r2 * np.sin(theta)
            path.moveTo(x[0], y[0])
            for i in range(1, len(x)):
                path.lineTo(x[i], y[i])
            self.path = path

        return self.path


# class Circle(pg.CircleROI):
#     def __init__(
#         self,
#         pos: tuple[float, float],
#         radius: float = 1.0,
#         color: str = "#f47b90",
#         id_: str | None = None,
#         **args,
#     ):
#         super().__init__(
#             pos,
#             radius=radius,
#             hoverPen=pg.mkPen(color="w", width=3),
#             handlePen=pg.mkPen(color="yellow", width=2),
#             removable=False,
#             **args,
#         )

#         self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
#         self.id_ = id_ or id_uuid4()

#         self.center = QPointF(pos[0] - radius, pos[1] - radius)
#         self.fill_color = QColor(color)
#         self.fill_color.setAlphaF(0.8)
#         self.brush = QBrush(self.fill_color)

#         self.setPos(self.center)

#         while self.handles:
#             self.removeHandle(0)

#     def addHandle(self, info, index=None):
#         # If a Handle was not supplied, create it now
#         if "item" not in info or info["item"] is None:
#             h = ZHandle(
#                 self.handleSize,
#                 typ=info["type"],
#                 pen=self.handlePen,
#                 hoverPen=self.handleHoverPen,
#                 parent=self,
#                 antialias=self._antialias,
#             )
#             info["item"] = h
#         else:
#             h = info["item"]
#             if info["pos"] is None:
#                 info["pos"] = h.pos()
#         h.setPos(info["pos"] * self.state["size"])

#         # connect the handle to this ROI
#         # iid = len(self.handles)
#         h.connectROI(self)
#         if index is None:
#             self.handles.append(info)
#         else:
#             self.handles.insert(index, info)

#         h.setZValue(self.zValue() + 1)
#         self.stateChanged()
#         return h

#     def paint(self, p: QPainter, opt, widget):
#         p.setBrush(self.brush)
#         if self.isSelected():
#             self.currentPen = self.hoverPen
#         super().paint(p, opt, widget)

#     def mouseClickEvent(self, ev: MouseClickEvent):
#         if ev.button() == Qt.MouseButton.LeftButton:
#             if not self.isSelected():
#                 self.setSelected(True)
#             else:
#                 self.setSelected(False)
#         super().mouseClickEvent(ev)


class ZHandle(pg.UIGraphicsItem):
    """
    Handle represents a single user-interactable point attached to an ROI. They
    are usually created by a call to one of the ROI.add___Handle() methods.

    Handles are represented as a square, diamond, or circle, and are drawn with
    fixed pixel size regardless of the scaling of the view they are displayed in.

    Handles may be dragged to change the position, size, orientation, or other
    properties of the ROI they are attached to.
    """

    # defines number of sides, start angle for each handle type
    types = {
        "t": (4, np.pi / 4),
        "f": (0, 0),  # polygon free handle: circle (sides==0 -> buildPath draws an ellipse)
        "s": (4, 0),
        "r": (12, 0),
        "sr": (12, 0),
        "rf": (12, 0),
    }

    sigClicked = Signal(object, object)  # self, event
    sigRemoveRequested = Signal(object)  # self

    def __init__(
        self,
        radius: float,
        typ: str,
        pen: tuple[int, int, int] = (200, 200, 220),
        hoverPen: tuple[int, int, int] = (255, 255, 0),
        parent: QGraphicsItem | None = None,
        deletable: bool = False,
        antialias: bool = True,
    ):
        self.rois: list[ZROI] = []
        self.radius = radius
        self.typ = typ
        self.pen = pg.mkPen(pen)
        self.hoverPen = pg.mkPen(hoverPen)
        self.currentPen = self.pen
        self.isMoving = False
        self.hovered = False
        # hit-testing disk is this many times larger than the visible circle so
        # presses near the handle still grab it for editing
        self._hit_scale = 2.0
        self._hit_shape: QPainterPath | None = None
        self.sides, self.startAng = self.types[typ]
        self.buildPath()
        self._shape = None
        self._antialias = antialias
        self.menu = self.buildMenu()

        pg.UIGraphicsItem.__init__(self, parent=parent)
        # Accept left-button clicks so pressing a vertex handle is consumed here
        # instead of falling through to the parent polygon's mouseClickEvent
        # (which toggles the selection off). Drags are already accepted by
        # hoverEvent.
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.deletable = deletable
        if deletable:
            self.setAcceptedMouseButtons(self.acceptedMouseButtons() | Qt.MouseButton.RightButton)
        self.setZValue(11)

    def connectROI(self, roi: ZROI):
        # roi is the "parent" roi, i is the index of the handle in roi.handles
        self.rois.append(roi)

    def disconnectROI(self, roi: ZROI):
        self.rois.remove(roi)

    def setDeletable(self, b: bool):
        self.deletable = b
        if b:
            self.setAcceptedMouseButtons(self.acceptedMouseButtons() | Qt.MouseButton.RightButton)
        else:
            self.setAcceptedMouseButtons(self.acceptedMouseButtons() & ~Qt.MouseButton.RightButton)

    def removeClicked(self):
        self.sigRemoveRequested.emit(self)

    def hoverEvent(self, ev: HoverEvent):
        hover = False
        if not ev.isExit():
            if ev.acceptDrags(Qt.MouseButton.LeftButton):
                hover = True
            for btn in [
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.RightButton,
                Qt.MouseButton.MiddleButton,
            ]:
                if (self.acceptedMouseButtons() & btn) and ev.acceptClicks(btn):
                    hover = True

        if hover:
            self.currentPen = self.hoverPen
            self.hovered = True
        else:
            self.currentPen = self.pen
            self.hovered = False
        self.update()

    def mouseClickEvent(self, ev: MouseClickEvent):
        # right-click cancels drag
        if ev.button() == Qt.MouseButton.RightButton and self.isMoving:
            self.isMoving = False  # prevents any further motion
            self.movePoint(self.startPos, finish=True)
            ev.accept()
        elif self.acceptedMouseButtons() & ev.button():
            ev.accept()
            if ev.button() == Qt.MouseButton.RightButton and self.deletable:
                self.raiseContextMenu(ev)
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()

    def buildMenu(self):
        menu = QMenu()
        menu.setTitle("ROI Handle")
        self.removeAction = menu.addAction("ROI Remove handle"), self.removeClicked
        return menu

    def getMenu(self):
        return self.menu

    def raiseContextMenu(self, ev):
        menu = self.scene().addParentContextMenus(self, self.getMenu(), ev)

        # Make sure it is still ok to remove this handle
        removeAllowed = all(r.checkRemoveHandle(self) for r in self.rois)
        self.removeAction.setEnabled(removeAllowed)
        pos = ev.screenPos()
        menu.popup(QPoint(int(pos.x()), int(pos.y())))

    def mouseDragEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        ev.accept()

        # Inform ROIs that a drag is happening
        #  note: the ROI is informed that the handle has moved using ROI.movePoint
        #  this is for other (more nefarious) purposes.
        # for r in self.roi:
        # r[0].pointDragEvent(r[1], ev)

        if ev.isFinish():
            if self.isMoving:
                for r in self.rois:
                    r.stateChangeFinished()
            self.isMoving = False
            self.currentPen = self.pen
            self.update()
        elif ev.isStart():
            for r in self.rois:
                r.handleMoveStarted()
            self.isMoving = True
            self.startPos = self.scenePos()
            self.cursorOffset = self.scenePos() - ev.buttonDownScenePos()
            self.currentPen = self.hoverPen

        if self.isMoving:  # note: isMoving may become False in mid-drag due to right-click.
            pos = ev.scenePos() + self.cursorOffset
            self.currentPen = self.hoverPen
            self.movePoint(pos, ev.modifiers(), finish=False)

    def movePoint(self, pos: pg.Point, modifiers: Qt.KeyboardModifier | None = None, finish: bool = True):
        if modifiers is None:
            modifiers = Qt.KeyboardModifier.NoModifier
        for r in self.rois:
            if not r.checkPointMove(self, pos, modifiers):
                return
        # print "point moved; inform %d ROIs" % len(self.roi)
        # A handle can be used by multiple ROIs; tell each to update its handle position
        for r in self.rois:
            r.movePoint(self, pos, modifiers, finish=finish, coords="scene")

    def buildPath(self):
        size = self.radius
        self.path = QPainterPath()
        if self.sides == 0:  # circle handle
            self.path.addEllipse(QRectF(-size, -size, size * 2, size * 2))
            return
        ang = self.startAng
        dt = 2 * np.pi / self.sides
        for i in range(0, self.sides):
            x = size * math.cos(ang)
            y = size * math.sin(ang)
            ang += dt
            if i == 0:
                self.path.moveTo(x, y)
            else:
                self.path.lineTo(x, y)
        self.path.closeSubpath()

    def paint(self, p, opt, widget):
        p.setRenderHints(p.RenderHint.Antialiasing, self._antialias)
        vis = self._visual_shape()
        if self.hovered:
            # prominent hover highlight: opaque white fill + outer ring
            p.setPen(self.currentPen)
            p.setBrush(Qt.GlobalColor.white)
            cb = vis.boundingRect()
            c = cb.center()
            r = max(cb.width(), cb.height()) / 2.0
            ring = QPainterPath()
            ring.addEllipse(c, r * 2, r * 2)
            p.save()
            p.setPen(pg.mkPen((255, 255, 0), width=2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(ring)
            p.restore()
        else:
            p.setPen(self.currentPen)
            fill_color = pg.mkColor(self.currentPen.color())
            fill_color.setAlphaF(0.5)
            p.setBrush(pg.mkBrush(fill_color))
        p.drawPath(vis)

    def _visual_shape(self):
        if self._shape is None:
            s = self.generateShape()
            if s is None:
                return self.path
            self._shape = s
            # beware--this can cause the view to adjust,
            # which would immediately invalidate the shape.
            self.prepareGeometryChange()
        return self._shape

    def shape(self):
        """Hit-testing shape: a larger disk around the handle so presses near
        (not just exactly on) the circle still grab the handle instead of
        falling through to the canvas and starting a selection box."""
        if self._hit_shape is None:
            vis = self._visual_shape()
            cb = vis.boundingRect()
            c = cb.center()
            r = max(cb.width(), cb.height()) / 2.0 * self._hit_scale
            hit = QPainterPath()
            hit.addEllipse(c, r, r)
            self._hit_shape = hit
            self.prepareGeometryChange()
        return self._hit_shape

    def boundingRect(self):
        self.shape()  # ensure shape is valid before measuring
        return self._hit_shape.boundingRect()

    def generateShape(self):
        dt = self.deviceTransform_()

        if dt is None:
            self._shape = self.path
            return None

        v = dt.map(QPointF(1, 0)) - dt.map(QPointF(0, 0))
        va = math.atan2(v.y(), v.x())

        dti: QTransform = pg.invertQTransform(dt)
        devPos = dt.map(QPointF(0, 0))
        tr = QTransform()
        tr.translate(devPos.x(), devPos.y())
        tr.rotateRadians(va)

        return dti.map(tr.map(self.path))

    def viewTransformChanged(self):
        pg.GraphicsObject.viewTransformChanged(self)
        self._shape = None  # invalidate shape, recompute later if requested.
        self._hit_shape = None
        self.update()
