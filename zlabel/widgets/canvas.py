import copy
import functools as ftools
import os
from collections import OrderedDict
from typing import Any, Dict, List

import numpy as np
import pyqtgraph as pg  # type: ignore
from pyqtgraph.graphicsItems.ROI import Handle
from numpy.typing import NDArray
from PIL import Image
from qtpy.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt, Signal
from qtpy.QtGui import (
    QBrush,
    QColor,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPicture,
    QTransform,
)
from qtpy.QtWidgets import QGraphicsItem

from zlabel.utils import (
    Annotation,
    ResultType,
    id_uuid4,
    DrawMode,
    StatusMode,
    ZLogger,
    RectangleResult,
    PolygonResult,
)
from zlabel.utils.enums import RgbMode

from .graphic_objects import Circle, Polygon, Rectangle, ZHandle


class Canvas(pg.PlotWidget):
    sigPointCreated = Signal(QPointF)
    sigRectangleCreated = Signal(object)
    sigPolygonCreated = Signal(object)

    sigItemClicked = Signal(str)
    sigItemStateChanged = Signal(object)
    sigItemStateChangeFinished = Signal(object)
    sigItemStateChangeStarted = Signal(object)
    sigItemsRemoved = Signal(object)

    sigMouseMoved = Signal(QPointF)

    sigMouseBackClicked = Signal()
    sigMouseForwardClicked = Signal()

    def __init__(
        self,
        parent=None,
        background="w",
        status_mode: StatusMode = StatusMode.VIEW,
    ):
        self.logger = ZLogger("Canvas")
        self.view_box: pg.ViewBox = ZViewBox()
        plotItem: pg.PlotItem = pg.PlotItem(viewBox=self.view_box)
        super().__init__(
            parent,
            background,
            plotItem=plotItem,
        )

        self._status_mode = status_mode
        self._draw_mode = DrawMode.RECTANGLE
        self._point_radius: float = 1.5
        self._color = "#000000"
        self._drawing = False
        self._z_value = 1
        self._is_editing_handle = False
        self._is_manual_set_state = False

        self.image_item = ZImageItem()
        self.current_image: np.ndarray | None = None
        self.current_item: Rectangle | Circle | Polygon | None = None
        self.selecting_item: Rectangle | Polygon | None = None
        self.showing_items: OrderedDict[str, Rectangle | Polygon] = OrderedDict()

        self.hline = pg.InfiniteLine(
            angle=0,
            pen=pg.mkPen("#55ff00", width=1),
            movable=False,
        )
        self.vline = pg.InfiniteLine(
            angle=90,
            pen=pg.mkPen("#55ff00", width=1),
            movable=False,
        )
        self.addItem(self.hline, ignoreBounds=True)  # type: ignore
        self.addItem(self.vline, ignoreBounds=True)  # type: ignore

        self.text_item = pg.TextItem(text="", anchor=(0, 0))
        self.set_mode_text()
        self.addItem(self.text_item)

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
    def selected_items(self) -> list[Rectangle | Circle | Polygon]:
        items_selected = list(
            filter(
                lambda it: it.isSelected()
                and isinstance(it, (Rectangle, Circle, Polygon)),
                self.items(),
            )
        )
        return items_selected  # type: ignore

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
    def set_image(self, img: str | NDArray):
        if isinstance(img, str):
            if os.path.exists(img):
                self.current_image = np.asarray(Image.open(img), dtype=np.uint8)  # type: ignore
            else:
                self.logger.error(f"{img} not exists")
                return
        else:
            self.current_image = img
        if self.image_item:
            self.removeItem(self.image_item)
            # self.current_image = None
        self.image_item = ZImageItem(
            np.rot90(
                np.flipud(self.current_image),  # type: ignore
                axes=(1, 0),
            )  # type: ignore
        )
        self.image_item.setZValue(-10)
        self.addItem(self.image_item)

    def clear_image(self):
        if self.image_item:
            self.removeItem(self.image_item)

    def copy_item(self, item: Rectangle):
        state = item.getState()
        if isinstance(item, Rectangle):
            return self.new_rectangle(
                state["pos"].x(),
                state["pos"].y(),
                state["size"].x(),
                state["size"].y(),
                item.fill_color.name(),
                True,
                item.id_,
            )
        raise NotImplementedError

    def set_color(self, color: str):
        self.color = color
        for item in self.showing_items.values():
            item.setFillColor(color)

    def set_rgb(self, rgb: RgbMode):
        if rgb == RgbMode.R:
            # self.image_item.setColorMap(pg.colormap.get("CET-L13"))
            im_filter = np.asarray([1, 0, 0])
        elif rgb == RgbMode.G:
            im_filter = np.asarray([0, 1, 0])
        elif rgb == RgbMode.B:
            im_filter = np.asarray([0, 0, 1])
        elif rgb == RgbMode.GRAY:
            im_filter = np.asarray([0.299, 0.587, 0.114])
        elif rgb == RgbMode.RGB:
            im_filter = np.asarray([1, 1, 1])
        else:
            raise NotImplementedError
        im_new = np.flipud(self.current_image) * im_filter  # type: ignore
        if rgb == RgbMode.GRAY:
            im_new = np.sum(im_new, 2)
        self.image_item.updateImage(
            np.rot90(
                im_new,  # type: ignore
                axes=(1, 0),
            )  # type: ignore
        )

    def setStatusMode(self, mode: StatusMode):
        self._status_mode = mode
        self.set_mode_text()

    def setDrawMode(self, mode: DrawMode):
        self._draw_mode = mode
        self.set_mode_text()

    def set_mode_text(self):
        html = f"""
        <div style='color: red; font-size: 8pt; font-weight: bold;'>
            <p>Mode: {self._status_mode.name}</p>
            <p>Draw: {self._draw_mode.name}</p>
        </div>
        """
        self.text_item.setHtml(html)

    def set_item_state_by_result(
        self,
        result: RectangleResult | PolygonResult | None,
        update=True,
    ):
        if result is None:
            return
        if result.id in self.showing_items:
            item = self.showing_items[result.id]
            state = item.getState()
            if isinstance(result, RectangleResult):
                state["pos"] = QPointF(result.x, result.y)
                state["size"] = QPointF(result.w, result.h)
                state["angle"] = result.rotation
            elif isinstance(result, PolygonResult):
                state["points"] = result.points
            item.setState(state, update=update)
            # item.update()

    def result_to_state(self, result: RectangleResult | PolygonResult | None):
        if result is None:
            return {}
        state = {
            "id": result.id,
            "pos": QPointF(result.x, result.y),
            "size": QPointF(result.w, result.h),
            "angle": result.rotation,
        }
        if isinstance(result, PolygonResult):
            state.update(
                {
                    "points": result.points,
                    "closed": True,
                }
            )
        return state

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
            case DrawMode.POLYGON:
                return {}
            case _:
                return {}

    def block_item_state_changed(self, v: bool = True):
        if v:
            for item in self.showing_items.values():
                item.sigRegionChangeStarted.disconnect(
                    self.on_item_state_change_started
                )
                item.sigRegionChangeFinished.disconnect(
                    self.on_item_state_change_finished
                )
        else:
            for item in self.showing_items.values():
                item.sigRegionChangeStarted.connect(self.on_item_state_change_started)
                item.sigRegionChangeFinished.connect(self.on_item_state_change_finished)

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
        # create a new one
        rect = QRectF(x, y, w, h)
        rectangle = Rectangle(
            rect,
            color=color,
            movable=movable,
            id_=id_,
        )  # type: ignore
        # self.logger.debug(f"Created rect {id_=}")
        return rectangle

    def new_polygon(
        self,
        positions: list[tuple[float, float]],
        closed: bool = True,
        color: str | None = None,
        movable=True,
        id_=None,
    ):
        # create a new one
        polygon = Polygon(
            positions=positions,
            closed=closed,
            color=color or self.color,
            movable=movable,
            id_=id_,
            antialias=False,  # 显式禁用抗锯齿以提高性能
        )  # type: ignore
        # self.logger.debug(f"Created polygon {id_=}")
        return polygon

    def start_drawing(self):
        match self._draw_mode:
            case DrawMode.RECTANGLE:
                self.current_item = Rectangle(
                    QRectF(0, 0, 0, 0),
                    color=self.color,
                    movable=False,
                )  # type: ignore
            case DrawMode.POINT:
                self.current_item = Circle(
                    pos=self.mouse_down_pos.toTuple(),  # type: ignore
                    radius=self.point_radius,
                    color=self.color,
                )
            case DrawMode.POLYGON:
                self.current_item = Polygon(
                    positions=[self.mouse_down_pos.toTuple()],  # type: ignore
                    closed=False,
                    color=self.color,
                    movable=False,
                )
            case _:
                self.current_item = None
        if self.current_item is not None:
            # self.create_item(self.current_item)
            self.addItem(self.current_item)

    def stop_drawing(self):
        if self.current_item is None:
            return
        state = self.current_item.getState()
        self.removeItem(self.current_item)
        match self.current_item:
            case Rectangle():
                if state["size"].x() > 1 and state["size"].y() > 1:
                    self.sigRectangleCreated.emit(state)
            case Circle():
                self.sigPointCreated.emit(state["pos"])
            case Polygon():
                self.sigPolygonCreated.emit(state)
            case _:
                ...
        self.current_item = None
        self.mouse_down_pos = None
        self.mouse_up_pos = None

    def map_scene_to_view(self, point: QPoint):
        pos = self.view_box.mapSceneToView(point)
        return QPointF(pos.x(), pos.y())

    # region update
    def update_by_anno(self, anno: Annotation | None):
        if anno is None:
            return
        if len(self.showing_items) == 0:
            self.logger.debug("empty self.rects, create by anno")
            self.create_items_by_anno(anno)
            return

        self.view_box.disableAutoRange()
        self.block_item_state_changed(True)

        new_keys = list(anno.results.keys())
        old_keys = list(self.showing_items.keys())
        n_removed, n_created, n_updated = 0, 0, 0

        for k in old_keys:
            if k not in new_keys:
                self.remove_item(self.showing_items[k])
                n_removed += 1

        for key in new_keys:
            if key not in old_keys:
                self.create_item_by_result(anno.results[key])
                n_created += 1
            else:
                # Use a polygon-safe updater: for polygons, only update points
                # to avoid collapsing ROI when result.w/h are 0.
                self.set_item_state_by_result(anno.results[key], update=True)
                item = self.showing_items[key]
                item.setVisible(True)
                n_updated += 1

        self.block_item_state_changed(False)
        self.view_box.enableAutoRange()

        self.update()

        self.logger.debug(
            f"Update items finished\n"
            f"updated: {n_updated}\n"
            f"created: {n_created}\n"
            f"removed: {n_removed}\n"
            f"number of items: {len(self.showing_items)}"
        )

    def merge_items_by_id(self, ids: list[str]):
        items = [self.showing_items[id_] for id_ in ids]
        self.merge_items(items)

    def merge_items(self, items: list[Any] | None = None):
        items = items or self.selected_items
        if len(items) == 0:
            return
        x, y = 0x3F3F3F, 0x3F3F3F
        x1, y1 = 0.0, 0.0
        for i, item in enumerate(items):
            state = item.getState()
            xt, yt = state["pos"].x(), state["pos"].y()
            wt, ht = state["size"].x(), state["size"].y()
            x, y = min(x, xt), min(y, yt)
            x1, y1 = max(x1, xt + wt), max(y1, yt + ht)
            if i > 0:  # keep the first as merged item
                item.setSelected(False)
                self.hide_item(item)
            self.logger.debug(f"Merge: {x=}, {y=}, w={x1 - x}, h={y1 - y}")
        self.sigItemsRemoved.emit([item.id_ for item in items[1:]])
        state = items[0].getState()
        self.sigItemStateChangeStarted.emit(state)
        state["pos"] = QPointF(x, y)
        state["size"] = QPointF(x1 - x, y1 - y)
        items[0].setState(state)
        self.sigItemStateChangeFinished.emit(state)

    # endregion

    # region create
    def create_item(self, item: Rectangle | Circle | Polygon):
        item.setZValue(self._z_value)
        item.sigClicked.connect(self.on_item_clicked)
        item.sigRegionChanged.connect(self.on_item_state_changed)
        item.sigRegionChangeStarted.connect(self.on_item_state_change_started)
        item.sigRegionChangeFinished.connect(self.on_item_state_change_finished)
        if isinstance(item, (Rectangle, Polygon)):
            self.showing_items[item.id_] = item
        self.addItem(item)
        self._z_value += 1
        self.logger.debug(f"Added {item=}")

    def find_invisible_rect(self):
        keys = list(self.showing_items.keys())
        for k in keys:
            item = self.showing_items[k]
            if not item.isVisible():
                return self.showing_items.pop(k)
        return None

    def create_item_by_result(self, result: RectangleResult | PolygonResult):
        if isinstance(result, PolygonResult):
            polygon = self.new_polygon(
                positions=result.points,
                closed=True,
                id_=result.id,
                movable=True,
            )
            self.create_item(polygon)
        elif isinstance(result, RectangleResult):
            # if result.id existed in self.rects, get the item and set state
            # else if invisible item existed,
            # get a new invisible item and set state
            # else create a new rect
            item = self.showing_items.get(result.id, None) or self.find_invisible_rect()
            if item is not None:
                state = item.getState()
                state["pos"] = QPointF(result.x, result.y)
                state["size"] = QPointF(result.w, result.h)
                state["id"] = result.id
                item.setState(state)
                # item.set_fill_color(result.labels[0].color)
                item.setFillColor(self.color)
                self.showing_items[state["id"]] = item
                self.logger.debug(f"Find existed rect not visible {result.id=}")
                item.setVisible(True)
                return

            rectangle = self.new_rectangle(
                result.x,
                result.y,
                result.w,
                result.h,
                id_=result.id,
                movable=True,
            )
            self.create_item(rectangle)
        else:
            raise NotImplementedError

    def create_items_by_results(
        self,
        results: list[RectangleResult | PolygonResult] | None = None,
    ):
        if results is None:
            return
        for r in results:
            self.create_item_by_result(r)

    def create_items_by_anno(self, anno: Annotation | None = None):
        if anno is None:
            return
        self.view_box.disableAutoRange()  # for performance
        self.clear_all_items()
        for result in anno.results.values():
            self.create_item_by_result(result)
        self.view_box.enableAutoRange()

    # endregion
    # region remove
    def hide_item(self, item: Rectangle | Circle | Polygon | None):
        if item is None:
            return
        item.setVisible(False)

    def remove_selected_items(self):
        self.sigItemsRemoved.emit([it.id_ for it in self.selected_items])
        for item in self.selected_items:
            self.remove_item(item)  # type: ignore

    def remove_item(self, item: QGraphicsItem | None):
        if item is None:
            return
        if isinstance(item, (Polygon, Rectangle)) and item.id_ in self.showing_items:
            self.showing_items.pop(item.id_)
            self.logger.debug(f"remove item: {item.id_}")
        return self.removeItem(item)

    def remove_items_by_anno(self, anno: Annotation):
        if anno is None:
            return
        ids = [r.id for r in anno.results.values()]
        self.remove_items_by_ids(ids)

    def remove_items_by_ids(self, ids: list[str]):
        keys = list(self.showing_items.keys())
        for id_ in keys:
            if id_ in ids:
                self.remove_item(self.showing_items[id_])

    def clear_all_items(self):
        for item in self.showing_items.values():
            self.removeItem(item)
        self.showing_items.clear()

    def clear_selections(self, exclude: list[str] | None = None):
        for item in self.showing_items.values():
            # self.logger.debug(f"clear selection: {item.id_=}, {item.isSelected()=}")
            if item.isSelected():
                item.setSelected(False)

    def clear_selections_if_no_ctrl(
        self,
        ev: QMouseEvent,
        exclude: list[str] | None = None,
    ):
        if ev.modifiers() != Qt.KeyboardModifier.ControlModifier:
            self.clear_selections(exclude)

    # endregion

    def select_item(self, id_: str):
        for item in self.items():
            if isinstance(item, (Rectangle, Circle, Polygon)):
                if item.id_ == id_:
                    item.setSelected(True)
                else:
                    item.setSelected(False)
        self.update()

    def item_at_point(self, point: QPoint | QPointF):
        if isinstance(point, QPointF):
            point = point.toPoint()
        point = self.view_box.mapViewToScene(point)
        point = self.mapFromScene(point)
        items: list = self.items(point)
        # we need to firstly consider ZHandle for resizing
        items_ = []
        for item in items:
            match item:
                case ZHandle() | Handle():  # return the top most handle if found
                    return item
                case Rectangle() | Circle() | Polygon():
                    items_.append(item)
                case _:
                    ...
        return items_[0] if len(items_) > 0 else None

    def set_items_movable(self, movable: bool):
        for item in self.showing_items.values():
            if isinstance(item, (Rectangle, Polygon)):
                item.setMovable(movable)

    # endregion

    # region slots
    def on_item_clicked(self, item: Rectangle | Polygon, ev: QMouseEvent):
        # self.current_item = item
        if isinstance(item, (Rectangle, Polygon)):
            self.sigItemClicked.emit(item.id_)

    def on_item_state_change_started(self, item: Rectangle | Polygon):
        if item == self.selecting_item:
            return
        self.sigItemStateChangeStarted.emit(item.getState())
        # self.logger.debug("Item state change started")

    def on_item_state_change_finished(self, item: Rectangle | Polygon):
        if item == self.selecting_item:
            return
        self.sigItemStateChangeFinished.emit(item.getState())
        self.logger.debug("Item state change Finished")

    def on_item_state_changed(self, item: Rectangle | Polygon):
        if item == self.selecting_item:
            return
        self.sigItemStateChanged.emit(item.getState())
        # self.logger.debug("Item state changed")

    # endregion

    # region events
    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.BackButton:
            self.sigMouseBackClicked.emit()
        elif ev.button() == Qt.MouseButton.ForwardButton:
            self.sigMouseForwardClicked.emit()
        elif ev.button() == Qt.MouseButton.LeftButton:
            # self.logger.debug(f"ZGraphicsScene Press: {ev=}, {self._status_mode=}")
            self.mouse_down_pos = self.map_scene_to_view(ev.pos())
            if self._status_mode == StatusMode.CREATE:
                self.clear_selections_if_no_ctrl(ev)
                self.start_drawing()
                ev.accept()
                return
            elif self._status_mode == StatusMode.EDIT:
                self.set_items_movable(True)
                # Click and edit
                item = self.item_at_point(self.mouse_down_pos)  # type: ignore
                self._is_editing_handle = False
                # if there is an item at the click position, meaning
                # we are trying to edit it
                if item is not None:
                    if isinstance(item, Handle):
                        self._is_editing_handle = True
                    # elif isinstance(item, pg.ROI):
                    elif isinstance(item, (Rectangle, Polygon)):
                        self.clear_selections_if_no_ctrl(ev)
                        # set the item to selected mode is process by
                        # item.mouseClickEvent
                        # item.setSelected(True)
                        self.selecting_item = None
                    else:
                        self.selecting_item = None
                # if the item at the position is None, meaning
                # we are trying to select
                else:
                    self.selecting_item = self.new_rectangle(0, 0, 0, 0)
                    self.addItem(self.selecting_item)
                if not self._is_editing_handle:
                    self.clear_selections_if_no_ctrl(ev)
                # here, we can't accept or return event
                # or it can't move processed by parent
            elif self._status_mode == StatusMode.VIEW:
                self.clear_selections()
                self.set_items_movable(False)
                ev.ignore()
        return super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QMouseEvent):
        pos = self.map_scene_to_view(ev.pos())
        self.hline.setPos(pos.y())
        self.vline.setPos(pos.x())
        self.sigMouseMoved.emit(pos)

        if ev.buttons() == Qt.MouseButton.LeftButton:
            # self.logger.debug(f"Move: {ev=}, {self._status_mode=}")
            self.mouse_up_pos = pos
            if self._status_mode == StatusMode.CREATE:
                if self.current_item:
                    state = self.get_item_state()
                    if state:
                        state["id"] = self.current_item.id_
                        self.current_item.setState(state, update=False)
                ev.accept()
                return
            elif self._status_mode == StatusMode.EDIT:
                if self.selecting_item:
                    state = self.get_new_rectangle_state()
                    if state:
                        state["id"] = self.selecting_item.id_
                        self.selecting_item.setState(state, update=False)
                    ev.accept()
                    return
            elif self._status_mode == StatusMode.VIEW:
                ...
        return super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            # self.logger.debug(f"ZGraphicsScene Release: {ev=}, {self._status_mode=}")
            if self._status_mode == StatusMode.CREATE:
                self.stop_drawing()
                ev.accept()
                return
            elif self._status_mode == StatusMode.EDIT:
                self.mouse_down_pos = None
                self.mouse_up_pos = None

                if self.selecting_item is None or self.selecting_item.area() < 4:
                    self.remove_item(self.selecting_item)
                    return super().mouseReleaseEvent(ev)

                state = self.selecting_item.getState()
                lt = self.mapFromScene(self.view_box.mapViewToScene(state["pos"]))
                rb = self.mapFromScene(
                    self.view_box.mapViewToScene(
                        QPoint(
                            state["pos"].x() + state["size"].x(),
                            state["pos"].y() + state["size"].y(),
                        )
                    )
                )
                items = self.items(
                    QRect(lt, rb),
                    Qt.ItemSelectionMode.IntersectsItemShape,
                )
                selected_items = []
                for item in items:
                    if isinstance(item, (Rectangle, Polygon)):
                        item.setSelected(True)
                        selected_items.append(item)
                    # self.logger.debug(f"Release: {item=}, {item.isSelected()=}")

                for item in selected_items:
                    item.update()

                # self.logger.debug(f"{items=}, {rect=}")
                self.remove_item(self.selecting_item)
                self.selecting_item = None
            elif self._status_mode == StatusMode.VIEW:
                pass
        return super().mouseReleaseEvent(ev)

    def keyPressEvent(self, ev: QKeyEvent) -> None:
        if ev.key() == Qt.Key.Key_Delete:
            self.remove_selected_items()
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
        if axis and ev.button() == Qt.MouseButton.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev, axis=axis)


class ZImageItem(pg.ImageItem):
    def __init__(self, image: Image.Image | NDArray | None = None, **kargs):
        if isinstance(image, Image.Image):
            image = np.asarray(image, dtype=np.uint8)
        super().__init__(image, **kargs)
        self._status_mode: StatusMode = StatusMode.VIEW

    def viewMode(self):
        self._status_mode = StatusMode.VIEW

    def editMode(self):
        self._status_mode = StatusMode.EDIT

    def setStatusMode(self, mode: StatusMode):
        self._status_mode = mode
