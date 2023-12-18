import copy
import functools as ftools
import os
from collections import OrderedDict
from typing import Any, Dict, List

import numpy as np
import pyqtgraph as pg  # type: ignore
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

from zlabel.utils import Annotation, Result, ResultType, id_uuid4, DrawMode, StatusMode, ZLogger
from zlabel.utils.enums import RgbMode

from .graphic_objects import Circle, Polygon, Rectangle, ZHandle


class Canvas(pg.PlotWidget):
    sigPointCreated = Signal(QPointF)
    sigRectangleCreated = Signal(object)

    sigItemClicked = Signal(str)
    sigItemStateChanged = Signal(object)
    sigItemStateChangeFinished = Signal(object)
    sigItemStateChangeStarted = Signal(object)
    sigItemsRemoved = Signal(object)

    sigMouseMoved = Signal(QPointF)

    sigMouseBackClicked = Signal()
    sigMouseForwardClicked = Signal()

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
        self._point_radius: float = 1.5
        self._color = "#000000"
        self._drawing = False
        self._z_value = 1
        self._is_resizing = False
        self._is_manual_set_state = False

        self.image_item = ZImageItem()
        self.current_image = None
        self.current_item: Rectangle | Circle | None = None
        self.selecting_rect: Rectangle | None = None
        self.rects: OrderedDict[str, Rectangle] = OrderedDict()

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
    def selected_items(self):
        items_selected = list(filter(lambda it: getattr(it, "_selected", False), self.items()))
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
        for item in self.rects.values():
            item.set_fill_color(color)

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

    def set_item_state_by_result(self, result: Result | None, update=True):
        if result is None:
            return
        if result.id in self.rects:
            item = self.rects[result.id]
            state = item.getState()
            state["pos"] = QPointF(result.x, result.y)
            state["size"] = QPointF(result.w, result.h)
            state["angle"] = result.rotation
            item.setState(state, update=update)
            # item.update()

    def result_to_state(self, result: Result | None):
        if result is None:
            return {}
        state = {
            "id": result.id,
            "pos": QPointF(result.x, result.y),
            "size": QPointF(result.w, result.h),
            "angle": result.rotation,
        }
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
            case _:
                return {}

    def block_item_state_changed(self, v: bool = True):
        if v:
            for item in self.rects.values():
                item.sigRegionChangeStarted.disconnect(self.on_item_state_change_started)
                item.sigRegionChangeFinished.disconnect(self.on_item_state_change_finished)
        else:
            for item in self.rects.values():
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
        self.logger.debug(f"Created rect {id_=}")
        return rectangle

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
                raise NotImplementedError
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
                raise NotImplementedError
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
        if len(self.rects) == 0:
            self.logger.debug("empty self.rects, create by anno")
            self.create_items_by_anno(anno)
            return
        self.block_item_state_changed(True)
        res_keys = list(anno.results.keys())
        old_keys = list(self.rects.keys())
        done_keys = []
        n_old = len(old_keys)
        n_new = len(res_keys)
        # if the number of new results > existed self.rects
        # change the state of existing rects and add new
        idx = 0
        for newk in res_keys:
            # update old items
            if idx < n_old:
                oldk = old_keys[idx]
                state = self.result_to_state(anno.results[newk])
                getk = oldk
                if newk in self.rects:
                    getk = newk
                done_keys.append(getk)
                item = self.rects.pop(getk)
                item.setState(state)
                item.setVisible(True)
                self.rects[newk] = item
                idx += 1
            # create new items
            else:
                self.logger.debug(f"Creating {anno.results[newk]}")
                self.create_item_by_result(anno.results[newk])
        for k in old_keys:
            if k not in done_keys:
                item = self.rects[k]
                item.setVisible(False)
                # self.hide_item(item)
        self.block_item_state_changed(False)
        self.logger.debug(
            f"Update items finished\nupdated: {idx}\ncreated: {n_new - idx}\nhided: {n_old - idx}\nexisted: {len(self.rects)}"
        )

    def metge_items_by_id(self, ids: List[str]):
        items = [self.rects[id_] for id_ in ids]
        self.merge_items(items)

    def merge_items(self, items: List[Any] | None = None):
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
            self.logger.debug(f"Merge: {x=}, {y=}, w={x1-x}, h={y1-y}")
        self.sigItemsRemoved.emit([item.id_ for item in items[1:]])
        state = items[0].getState()
        self.sigItemStateChangeStarted.emit(state)
        state["pos"] = QPointF(x, y)
        state["size"] = QPointF(x1 - x, y1 - y)
        items[0].setState(state)
        self.sigItemStateChangeFinished.emit(state)

    # endregion

    # region create
    def create_item(self, item: Rectangle | Circle):
        item.setZValue(self._z_value)
        item.sigClicked.connect(self.on_item_clicked)
        item.sigRegionChanged.connect(self.on_item_state_changed)
        item.sigRegionChangeStarted.connect(self.on_item_state_change_started)
        item.sigRegionChangeFinished.connect(self.on_item_state_change_finished)
        if isinstance(item, Rectangle):
            self.rects[item.id_] = item
        self.addItem(item)
        self._z_value += 1
        self.logger.debug(f"Added {item.id_}")

    def find_invisible_rect(self):
        keys = list(self.rects.keys())
        for k in keys:
            item = self.rects[k]
            if not item.isVisible():
                return self.rects.pop(k)
        return None

    def create_item_by_result(self, result: Result):
        match result.type_id:
            case ResultType.RECTANGLE:
                # if result.id existed in self.rects, get the item and set state
                # else if invisible item existed,
                # get a new invisible item and set state
                # else create a new rect
                item = self.rects.get(result.id, None) or self.find_invisible_rect()
                if item is not None:
                    state = item.getState()
                    state["pos"] = QPointF(result.x, result.y)
                    state["size"] = QPointF(result.w, result.h)
                    state["id"] = result.id
                    item.setState(state)
                    # item.set_fill_color(result.labels[0].color)
                    item.set_fill_color(self.color)
                    self.rects[state["id"]] = item
                    self.logger.debug(f"Find existed rect not visible {result.id=}")
                    item.setVisible(True)
                    return

                rectangle = self.new_rectangle(
                    result.x,
                    result.y,
                    result.w,
                    result.h,
                    self.color,
                    id_=result.id,
                    movable=True,
                )
                self.create_item(rectangle)
            case _:
                raise NotImplementedError

    def create_items_by_results(self, results: List[Result] | None = None):
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
    def hide_item(self, item: Rectangle | None):
        if item is None:
            return
        # state = item.getState()
        # state["pos"] = QPointF(0, 0)
        # state["size"] = QPointF(0, 0)
        # item.setState(state)
        item.setVisible(False)

    def remove_selected_items(self):
        self.sigItemsRemoved.emit([it.id_ for it in self.selected_items])
        for item in self.selected_items:
            self.remove_item(item)  # type: ignore

    def remove_item(self, item: QGraphicsItem | None):
        if item is None:
            return
        if isinstance(item, Rectangle) and item.id_ in self.rects:
            self.rects.pop(item.id_)
            self.logger.debug(f"remove item: {item.id_}")
        return self.removeItem(item)

    def remove_items_by_anno(self, anno: Annotation):
        if anno is None:
            return
        ids = [r.id for r in anno.results.values()]
        self.remove_items_by_ids(ids)

    def remove_items_by_ids(self, ids: List[str]):
        keys = list(self.rects.keys())
        for id_ in keys:
            if id_ in ids:
                self.remove_item(self.rects[id_])

    def clear_all_items(self):
        for item in self.rects.values():
            self.removeItem(item)
        self.rects.clear()

    def clear_selections(self, exclude=[]):
        for item in self.rects.values():
            if item.is_selected():
                item.setSelected(False)
                item.update()

    def clear_selections_if_no_ctrl(self, ev: QMouseEvent, exclude=[]):
        if ev.modifiers() != Qt.KeyboardModifier.ControlModifier:
            self.clear_selections(exclude)

    # endregion

    def select_item(self, id_: str):
        for item in self.items():
            match item:
                case Rectangle() | Circle() | Polygon():
                    if item.id_ == id_:
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
        # we need to firstly consider ZHandle for resizing
        items_ = []
        for item in items:
            match item:
                case ZHandle():  # return the top most handle if found
                    return item
                case Rectangle() | Circle() | Polygon():
                    items_.append(item)
                case _:
                    ...
        return items_[0] if len(items_) > 0 else None

    # endregion

    # region slots
    def on_item_clicked(self, item: Rectangle, ev: QMouseEvent):
        # self.current_item = item
        if isinstance(item, Rectangle):
            self.sigItemClicked.emit(item.id_)

    def on_item_state_change_started(self, item: Rectangle):
        if item != self.selecting_rect:
            self.sigItemStateChangeStarted.emit(item.getState())
            self.logger.debug("Item state change started")

    def on_item_state_change_finished(self, item: Rectangle):
        if item != self.selecting_rect:
            self.sigItemStateChangeFinished.emit(item.getState())
            self.logger.debug("Item state change Finished")

    def on_item_state_changed(self, item: Rectangle):
        if item != self.selecting_rect:
            self.sigItemStateChanged.emit(item.getState())

    def get_item_state_export(self, item: Rectangle):
        state = item.getState()
        return {
            "id": item.id_,
            "x": state["pos"].x(),
            "y": state["pos"].y(),
            "w": state["size"].x(),
            "h": state["size"].y(),
            "angle": state["angle"],
            "score": 1.0,
        }

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
                # Click and edit
                item = self.item_at_point(self.mouse_down_pos)  # type: ignore
                self._is_resizing = False
                if item is not None:
                    if isinstance(item, ZHandle):
                        self._is_resizing = True
                    self.selecting_rect = None
                else:
                    self.selecting_rect = self.new_rectangle(0, 0, 0, 0)
                    self.addItem(self.selecting_rect)
                if not self._is_resizing:
                    self.clear_selections_if_no_ctrl(ev)
                # here, we can't accept or return event
                # or it can't move processed by parent
            elif self._status_mode == StatusMode.VIEW:
                self.clear_selections_if_no_ctrl(ev)
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
                if self.selecting_rect:
                    state = self.get_new_rectangle_state()
                    if state:
                        state["id"] = self.selecting_rect.id_
                        self.selecting_rect.setState(state, update=False)
                    ev.accept()
                    return
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

                if self.selecting_rect is None or self.selecting_rect.area() < 4:
                    self.remove_item(self.selecting_rect)
                    return super().mouseReleaseEvent(ev)

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
                        item.update()
                # self.logger.debug(f"{items=}, {rect=}")
                self.remove_item(self.selecting_rect)
                self.selecting_rect = None
        # elif ev.button() == Qt.MouseButton.RightButton:
        #     if self.hs_item_at_point():
        #         self.clear_selections()
        #         ev.accept()
        #         return
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

    # def width(self) -> int:
    #     return super().width() or 0

    # def height(self) -> int:
    #     return super().height() or 0

    def viewMode(self):
        self._status_mode = StatusMode.VIEW

    def editMode(self):
        self._status_mode = StatusMode.EDIT

    def setStatusMode(self, mode: StatusMode):
        self._status_mode = mode
