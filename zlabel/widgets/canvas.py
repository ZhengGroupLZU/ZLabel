from collections import OrderedDict
import functools as ftools
import os
from typing import Dict, List
import uuid

import cv2
import pyqtgraph as pg
import pyqtgraph.functions as pf
import numpy as np
from numpy.typing import NDArray
from PIL import Image
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent, MouseDragEvent
from qtpy.QtCore import QPoint, QPointF, QRectF, QSizeF, Qt, Signal, Slot, QRect, QSize
from qtpy.QtGui import (
    QBrush,
    QColor,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPicture,
    QTransform,
)
from qtpy.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QGraphicsWidget,
)

from zlabel.utils.project import Annotation, Result, ResultType

from ..utils import DrawMode, StatusMode, ZLogger
from .graphic_objects import Rectangle, Circle, Polygon, ZHandle


class Canvas(pg.PlotWidget):
    sigPointCreated = Signal(QPointF)
    sigRectangleCreated = Signal(object)
    sigItemClicked = Signal(str)
    sigItemStateChanged = Signal(object)
    sigItemsRemoved = Signal(object)
    sigMouseMoved = Signal(object)

    def __init__(self, parent=None, background="w"):
        self.logger = ZLogger("Canvas")
        self.view_box: pg.ViewBox = ZViewBox()
        plotItem: pg.PlotItem = pg.PlotItem(viewBox=self.view_box)
        super().__init__(
            parent,
            background,
            plotItem=plotItem,
        )

        self._status_mode = StatusMode.VIEW
        self._draw_mode = DrawMode.RECTANGLE
        self._point_radius: float = 3.0
        self._color = "#000000"
        self._drawing = False
        self._z_value = 1
        self._is_resizing = False

        self.image_item = ZImageItem()
        self.current_image = None
        self.current_item: Rectangle | Circle | None = None
        self.selecting_rect: Rectangle | None = None

        self.hline = pg.InfiniteLine(
            angle=0,
            pen=pg.mkPen("#bc5215", width=1),
            movable=False,
        )
        self.vline = pg.InfiniteLine(
            angle=90,
            pen=pg.mkPen("#bc5215", width=1),
            movable=False,
        )
        self.addItem(self.hline, ignoreBounds=True)  # type: ignore
        self.addItem(self.vline, ignoreBounds=True)  # type: ignore

        self.mouse_down_pos: QPointF | None = None
        self.mouse_up_pos: QPointF | None = None
        self.tr_im = QTransform().rotate(90)
        # self.view_box.setTransform(self.tr_im)
        self.view_box.invertY()

        self.showAxis("left", False)
        self.showAxis("bottom", False)
        self.setAspectLocked(True)

    # region properties
    @ftools.cached_property
    def im_width(self):
        if self.current_image is None:
            return 0
        return self.current_image.shape[1]

    @ftools.cached_property
    def im_height(self):
        if self.current_image is None:
            return 0
        return self.current_image.shape[0]

    @property
    def selected_items(self):
        items_selected = list(
            filter(lambda it: getattr(it, "_selected", False), self.items())
        )
        return items_selected

    @property
    def point_radius(self):
        return self._point_radius

    @point_radius.setter
    def point_radius(self, v: float):
        if 0 < v < 20:
            self._point_radius = v
        else:
            raise ValueError(f"point radius must be between 0 and 20, got {v}")

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, v: str):
        self._color = v

    # endregion

    # region functions
    def setImage(self, img: str | NDArray):
        if isinstance(img, str):
            if os.path.exists(img):
                self.current_image = np.asarray(Image.open(img), dtype=np.uint8)  # type: ignore
                # img = cv2.imread(img)
            else:
                self.logger.error(f"{img} not exists")
                return
        if self.image_item:
            self.removeItem(self.image_item)
            # self.current_image = None
        self.image_item = ZImageItem(
            np.rot90(
                np.flipud(self.current_image),  # type: ignore
                axes=(1, 0),
            )  # type: ignore
        )
        # self.image_item = ZImageItem(np.rot90(self.current_image, 1, axes=(1, 0)))  # type: ignore
        # self.image_item = ZImageItem(self.current_image)
        self.image_item.setZValue(-10)
        self.addItem(self.image_item)

    def clear_image(self):
        if self.image_item:
            self.removeItem(self.image_item)

    def setStatusMode(self, mode: StatusMode):
        self._status_mode = mode

    def setDrawMode(self, mode: DrawMode):
        self._draw_mode = mode

    def get_new_rectangle_state(self):
        # logger.debug(f"{self.mouse_down_pos=}, {self.mouse_up_pos=}")
        if self.mouse_down_pos and self.mouse_up_pos:
            x0, y0 = self.mouse_down_pos.x(), self.mouse_down_pos.y()
            x1, y1 = self.mouse_up_pos.x(), self.mouse_up_pos.y()
            w, h = abs(x1 - x0), abs(y1 - y0)
            if w < 1e-3 or h < 1e-3:
                return {}
            rect = QRectF(min(x0, x1), min(y0, y1), w, h)
            # logger.debug(f"{x0=}, {y0=}, {w=}, {h=}")
            return {
                "pos": rect.topLeft().toTuple(),
                "size": rect.size().toTuple(),
                "angle": 0,
                "rect": rect,
            }  # type: ignore
        return {}

    def get_item_state(self):
        match self._draw_mode:
            case DrawMode.RECTANGLE:
                return self.get_new_rectangle_state()
            case DrawMode.POINT:
                return {}
            case _:
                return {}

    def new_rectangle(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: str | None = None,
        movable=True,
        id_=None,
    ):
        color = color or self.color
        rect = QRectF(x, y, w, h)
        rectangle = Rectangle(
            rect,
            color=color,
            movable=movable,
            id_=id_,
        )  # type: ignore
        return rectangle

    def start_drawing(self):
        match self._draw_mode:
            case DrawMode.RECTANGLE:
                self.current_item = self.new_rectangle(0, 0, 0, 0)
            case DrawMode.POINT:
                self.current_item = Circle(
                    pos=self.mouse_down_pos.toTuple(),  # type: ignore
                    radius=self.point_radius,
                )
            case DrawMode.POLYGON:
                raise NotImplementedError
            case _:
                self.current_item = None
        if self.current_item is not None:
            self.create_item(self.current_item)

    def on_item_clicked(self, item: Rectangle, ev: QMouseEvent):
        self.current_item = item
        self.sigItemClicked.emit(item.id)

    def on_item_state_changed(self, item: Rectangle):
        self.sigItemStateChanged.emit(item)

    def get_item_state_export(self, item: Rectangle):
        state = item.getState()
        return {
            "id": item.id,
            "x": state["pos"].x(),
            "y": state["pos"].y(),
            "w": state["size"].x(),
            "h": state["size"].y(),
            "angle": state["angle"],
            "score": 1.0,
        }

    def stop_drawing(self):
        match self.current_item:
            case Rectangle():
                state = self.current_item.getState()
                if state["size"].x() < 1 or state["size"].y() < 1:
                    self.remove_item(self.current_item)
                else:
                    self.current_item.sigRegionChanged.connect(
                        self.on_item_state_changed
                    )
                    self.remove_item(self.current_item)
                    self.sigRectangleCreated.emit(self.current_item)
            case Circle():
                pos = self.current_item.getState()["pos"]
                self.sigPointCreated.emit(pos)
                self.remove_item(self.current_item)
            case Polygon():
                raise NotImplementedError
            case _:
                ...
        self.current_item = None
        self.mouse_down_pos = None
        self.mouse_up_pos = None

    def map_scene_to_view(self, point: QPoint):
        pos = self.view_box.mapSceneToView(point)
        return QPointF(pos.x(), pos.y())

    # region create
    def create_item(self, item: Rectangle | Polygon | Circle):
        item.setZValue(self._z_value)
        self.addItem(item)
        item.sigClicked.connect(self.on_item_clicked)
        self._z_value += 1

    def create_item_by_result(self, result: Result):
        match result.type_id:
            case ResultType.RECTANGLE:
                rectangle = self.new_rectangle(
                    result.x,
                    result.y,
                    result.w,
                    result.h,
                    result.labels[0].color,
                    id_=result.id,
                    movable=True,
                )
                self.create_item(rectangle)
            case _:
                raise NotImplementedError

    def create_items_by_anno(self, anno: Annotation | None = None):
        if anno is None:
            return
        self.clear_all_items()
        for result in anno.results.values():
            self.create_item_by_result(result)

    # endregion
    # region remove
    def remove_selected_item(self):
        self.sigItemsRemoved.emit(self.selected_items)
        for item in self.selected_items:
            self.remove_item(item)  # type: ignore

    def remove_item(self, item: QGraphicsItem | None):
        # match item:
        #     case Rectangle() | Polygon():
        #         ...
        #     case _:
        #         ...
        if item is None:
            return
        return super().removeItem(item)

    def remove_items_by_anno(self, anno: Annotation):
        if anno is None:
            return
        ids = [r.id for r in anno.results.values()]
        self.remove_items_by_ids(ids)

    def remove_items_by_ids(self, ids: List[str]):
        for item in self.items():
            match item:
                case Rectangle() | Circle() | Polygon():
                    if item.id in ids:
                        self.remove_item(item)
                case _:
                    ...

    def clear_all_items(self):
        for item in self.items():
            match item:
                case Rectangle() | Circle() | Polygon():
                    self.remove_item(item)
                case _:
                    ...

    def clear_selections(self, exclude=[]):
        for item in self.items():
            if item in exclude:
                continue
            match item:
                case Rectangle() | Circle() | Polygon():
                    item.setSelected(False)
                    item.update()
                case _:
                    ...
        self.update()

    def clear_selections_if_no_ctrl(self, ev: QMouseEvent, exclude=[]):
        if ev.modifiers() != Qt.KeyboardModifier.ControlModifier:
            self.clear_selections(exclude)

    # endregion

    def select_item(self, id_: str):
        for item in self.items():
            match item:
                case Rectangle() | Circle() | Polygon():
                    if item.id == id_:
                        item.setSelected(True)
                    else:
                        item.setSelected(False)
                    item.update()
                case _:
                    ...
        self.update()

    def item_at_point(self, point: QPoint | QPointF):
        if isinstance(point, QPointF):
            point = point.toPoint()
        point = self.view_box.mapViewToScene(point)
        point = self.mapFromScene(point)
        items: List = self.items(point)
        for item in items:
            match item:
                case Rectangle() | Circle() | Polygon() | ZHandle():
                    return item
                case _:
                    ...
        return None

    # endregion

    # region events
    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            # print(f"ZGraphicsScene Press: {ev=}, {self._status_mode=}")
            self.mouse_down_pos = self.map_scene_to_view(ev.pos())
            match self._status_mode:
                case StatusMode.CREATE:
                    self.start_drawing()
                    ev.accept()
                    return
                case StatusMode.EDIT:
                    # Click and edit
                    item = self.item_at_point(self.mouse_down_pos)
                    if item is not None:
                        if isinstance(item, ZHandle):
                            self._is_resizing = True
                        else:
                            self._is_resizing = False
                        self.selecting_rect = None
                    else:
                        self.selecting_rect = self.new_rectangle(0, 0, 0, 0)
                        self.addItem(self.selecting_rect)
                    if not self._is_resizing:
                        self.clear_selections_if_no_ctrl(ev)
                    # ev.accept()
                    # return
                case StatusMode.VIEW:
                    self.clear_selections_if_no_ctrl(ev)
                case _:
                    ...
        return super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QMouseEvent):
        pos = self.map_scene_to_view(ev.pos())
        self.hline.setPos(pos.y())
        self.vline.setPos(pos.x())
        self.sigMouseMoved.emit(pos)

        if ev.buttons() == Qt.MouseButton.LeftButton:
            # print(f"Move: {ev=}, {self._status_mode=}")
            self.mouse_up_pos = pos
            match self._status_mode:
                case StatusMode.CREATE:
                    if self.current_item:
                        state = self.get_item_state()
                        if state:
                            self.current_item.setState(state)
                    ev.accept()
                    return
                case StatusMode.EDIT:
                    if self.selecting_rect:
                        state = self.get_new_rectangle_state()
                        if state:
                            self.selecting_rect.setState(state)
                        ev.accept()
                        return
                case StatusMode.VIEW:
                    ev.accept()
                case _:
                    ...
        return super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            # print(f"ZGraphicsScene Release: {ev=}, {self._status_mode=}")
            match self._status_mode:
                case StatusMode.CREATE:
                    self.stop_drawing()
                    ev.accept()
                    return
                case StatusMode.EDIT:
                    self.mouse_down_pos = None
                    self.mouse_up_pos = None

                    if self.selecting_rect is None or self.selecting_rect.area() < 4:
                        self.remove_item(self.selecting_rect)
                        return super().mouseReleaseEvent(ev)

                    self.remove_item(self.selecting_rect)
                    state = self.selecting_rect.getState()
                    lt = self.mapFromScene(self.view_box.mapViewToScene(state["pos"]))
                    rb = self.mapFromScene(
                        self.view_box.mapViewToScene(
                            QPoint(
                                state["pos"].x() + state["size"].x(),
                                state["pos"].y() + state["size"].y(),
                            )
                        )
                    )
                    rect = QRect(lt, rb)
                    items = self.items(
                        rect,
                        Qt.ItemSelectionMode.IntersectsItemShape,
                    )
                    for item in items:
                        if isinstance(item, Rectangle):
                            item.setSelected(True)
                            item._selected = True
                            item.update()
                    # self.logger.debug(f"{items=}, {rect=}")
                    ev.accept()
                    return
                case _:
                    ...
        # elif ev.button() == Qt.MouseButton.RightButton:
        #     if self.hs_item_at_point():
        #         self.clear_selections()
        #         ev.accept()
        #         return
        return super().mouseReleaseEvent(ev)

    def keyPressEvent(self, ev: QKeyEvent) -> None:
        if ev.key() == Qt.Key.Key_Delete:
            self.remove_selected_item()
        super().keyPressEvent(ev)

    # endregion


class ZViewBox(pg.ViewBox):
    def __init__(self, enableMenu=False, defaultPadding=0.0):
        pg.ViewBox.__init__(self, enableMenu=enableMenu, defaultPadding=defaultPadding)
        self.setMouseMode(self.PanMode)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton:
            self.autoRange()
        super().mouseClickEvent(ev)

    ## reimplement mouseDragEvent to disable continuous axis zoom
    def mouseDragEvent(self, ev, axis=None):
        if axis is not None and ev.button() == Qt.MouseButton.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev, axis=axis)


class ZImageItem(pg.ImageItem):
    def __init__(self, image: Image.Image | NDArray | None = None, **kargs):
        if isinstance(image, Image.Image):
            image = np.asarray(image, dtype=np.uint8)
        super().__init__(image, **kargs)
        self._status_mode: StatusMode = StatusMode.VIEW

    def width(self) -> int:
        return super().width() or 0

    def height(self) -> int:
        return super().height() or 0

    def viewMode(self):
        self._status_mode = StatusMode.VIEW

    def editMode(self):
        self._status_mode = StatusMode.EDIT

    def setStatusMode(self, mode: StatusMode):
        self._status_mode = mode
