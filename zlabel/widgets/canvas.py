import functools
import os
from collections import OrderedDict
from typing import Any

import numpy as np
import pyqtgraph as pg
from PIL import Image
from pyqtgraph.graphicsItems.ROI import Handle
from pyqtgraph.Qt.QtCore import QPoint, QPointF, QRect, QRectF, Qt, Signal
from pyqtgraph.Qt.QtGui import QKeyEvent, QMouseEvent
from pyqtgraph.Qt.QtWidgets import QGraphicsItem

from zlabel.utils import Annotation, DrawMode, PolygonResult, RectangleResult, StatusMode, ZLogger
from zlabel.utils.enums import RgbMode
from zlabel.widgets.graphic_objects import Point, Polygon, Rectangle, ZHandle


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
        background="k",
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
        self._default_color = "#000000"
        self._alpha: float = 0.5
        self._drawing = False
        self._z_value = 1
        self._is_editing_handle = False
        self._is_manual_set_state = False
        # track signal block state to avoid redundant (dis)connections
        self._signals_blocked: bool = False

        self._image_backup: np.ndarray | None = None
        # cache flipped image for rgb channel rendering
        self._image_flipped: np.ndarray | None = None
        self.image_item = pg.ImageItem()
        self.image_item.setZValue(-10)
        self.addItem(self.image_item)

        self.current_item: Rectangle | Point | Polygon | None = None
        self.selecting_item: Rectangle | None = None
        self.showing_items: OrderedDict[str, Rectangle | Polygon] = OrderedDict()
        # Committed polygon points added by user clicks during CREATE mode
        self.polygon_points_committed: list[pg.Point] = []
        # Current preview point following mouse while drawing polygon
        self.polygon_preview_point: pg.Point | None = None

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
        # Track last mouse position in view coordinates for preview updates
        self.last_mouse_pos_view: QPointF | None = None
        self.view_box.invertY()

        # self.showAxis("left", False)
        # self.showAxis("bottom", False)
        self.setAspectLocked(True)

    # region helpers
    def cancel_drawing(self):
        """Cancel current drawing without emitting creation signals.

        Removes the temporary item from scene and resets drawing buffers.
        Applies to Rectangle/Point/Polygon in CREATE mode.
        """
        if self.current_item is not None:
            try:
                self.removeItem(self.current_item)
            except Exception:
                pass
        # Reset polygon drawing buffers
        self.polygon_points_committed = []
        self.polygon_preview_point = None
        # Reset common flags
        self.current_item = None
        self._drawing = False
        self.mouse_down_pos = None
        self.mouse_up_pos = None

    def undo_last_polygon_point(self, preview_pos: QPointF | None = None):
        """Undo the last committed polygon vertex and update preview state.

        If no committed points remain, cancel the entire drawing.
        """
        if self._status_mode != StatusMode.CREATE or self._draw_mode != DrawMode.POLYGON:
            return
        if self.current_item is None:
            return
        if len(self.polygon_points_committed) > 0:
            self.polygon_points_committed.pop()
        # If no points left, cancel drawing entirely
        if len(self.polygon_points_committed) == 0:
            self.cancel_drawing()
            return
        # Keep preview following the mouse
        if preview_pos is None:
            preview_pos = self.last_mouse_pos_view
        if preview_pos is not None:
            self.polygon_preview_point = pg.Point(preview_pos.x(), preview_pos.y())
        state = self.get_drawing_polygon_state()
        if state:
            state["id"] = self.current_item.id_
            self.current_item.setState(state, update=False)

    # endregion

    # region properties
    @functools.cached_property
    def im_width(self):
        return self.image_item.width()

    @functools.cached_property
    def im_height(self):
        return self.image_item.height()

    @property
    def selected_items(self) -> list[Rectangle | Point | Polygon]:
        items_selected = list(
            filter(
                lambda it: it.isSelected() and isinstance(it, (Rectangle, Point, Polygon)),
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
    def default_color(self):
        return self._default_color

    @default_color.setter
    def default_color(self, v: str):
        self._default_color = v

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, v: float):
        if 0 < v < 1:
            self._alpha = v
        else:
            raise ValueError(f"alpha must be between 0 and 1, got {v}")

    # endregion

    # region functions
    def update_image(self, img: str | np.ndarray):
        if isinstance(img, str):
            if os.path.exists(img):
                img = np.asarray(Image.open(img), dtype=np.uint8)  # type: ignore
            else:
                self.logger.error(f"{img} not exists")
                return
        assert isinstance(img, np.ndarray), f"img must be np.ndarray, got {type(img)}"
        img = np.rot90(img, k=3, axes=(1, 0))
        self._image_backup = img.copy()
        # cache flipped version for later rgb rendering to avoid repeated flipud
        try:
            self._image_flipped = np.flipud(self._image_backup)
        except Exception:
            # fallback, keep behavior even if flip fails
            self._image_flipped = None

        self.image_item.setImage(img)

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

    def set_color(self, color: str, alpha: float = 0.5):
        self.default_color = color
        self.alpha = alpha
        for item in self.showing_items.values():
            item.setFillColor(color, alpha)

    def set_rgb(self, mode: RgbMode):
        if self._image_backup is None:
            return
        # use cached flipped image to reduce per-call cost
        flip = self._image_flipped if self._image_flipped is not None else np.flipud(self._image_backup)  # type: ignore
        # persist cache if it was missing
        if self._image_flipped is None:
            self._image_flipped = flip
        if mode == RgbMode.R:
            # self.image_item.setColorMap(pg.colormap.get("CET-L13"))
            im_filter = np.asarray([1, 0, 0])
        elif mode == RgbMode.G:
            im_filter = np.asarray([0, 1, 0])
        elif mode == RgbMode.B:
            im_filter = np.asarray([0, 0, 1])
        elif mode == RgbMode.GRAY:
            im_filter = np.asarray([0.299, 0.587, 0.114])
        elif mode == RgbMode.RGB:
            im_filter = np.asarray([1, 1, 1])
        else:
            raise NotImplementedError
        im_new = flip * im_filter  # type: ignore
        if mode == RgbMode.GRAY:
            im_new = np.sum(im_new, 2)
        self.image_item.updateImage(im_new)

    def setStatusMode(self, mode: StatusMode):
        # guard to avoid redundant text updates
        if self._status_mode == mode:
            return
        self._status_mode = mode
        self.set_mode_text()

    def setDrawMode(self, mode: DrawMode):
        # guard to avoid redundant text updates
        if self._draw_mode == mode:
            return
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
            item.setState(result.getState(), update=update)
            # item.update()

    def get_drawing_rectangle_state(self) -> dict[str, Any]:
        # logger.debug(f"{self.mouse_down_pos=}, {self.mouse_up_pos=}")
        if not (self.mouse_down_pos and self.mouse_up_pos):
            return {}
        dpos = self.mouse_up_pos - self.mouse_down_pos
        w, h = abs(dpos.x()), abs(dpos.y())
        if w < 1e-3 or h < 1e-3:
            return {}
        x = min(self.mouse_down_pos.x(), self.mouse_up_pos.x())
        y = min(self.mouse_down_pos.y(), self.mouse_up_pos.y())
        return {
            "pos": pg.Point(x, y),
            "size": pg.Point(w, h),
            "angle": 0,
        }

    def get_drawing_polygon_state(self) -> dict[str, Any]:
        """Build polygon state using committed points plus a live preview point.

        This method does not modify committed points; it only prepares a state
        for updating the current polygon during CREATE mode.
        """
        # Compose points: committed vertices + optional preview vertex
        points: list[pg.Point] = list(self.polygon_points_committed)
        if self.polygon_preview_point is not None:
            points.append(self.polygon_preview_point)

        if len(points) == 0:
            return {}

        return {
            "pos": pg.Point(0.0, 0.0),
            "size": pg.Point(1.0, 1.0),
            "angle": 0,
            "points": points,
            "closed": False,
        }

    def get_drawing_item_state(self) -> dict[str, Any]:
        if self.selecting_item is not None:
            return self.get_drawing_rectangle_state()
        match self._draw_mode:
            case DrawMode.RECTANGLE:
                return self.get_drawing_rectangle_state()
            case DrawMode.POLYGON:
                return self.get_drawing_polygon_state()
            case _:
                return {}

    def block_item_state_changed(self, v: bool = True):
        # avoid redundant (dis)connections if state unchanged
        if v == self._signals_blocked:
            return
        if v:
            for item in self.showing_items.values():
                item.sigRegionChangeStarted.disconnect(self.on_item_state_change_started)
                item.sigRegionChangeFinished.disconnect(self.on_item_state_change_finished)
        else:
            for item in self.showing_items.values():
                item.sigRegionChangeStarted.connect(self.on_item_state_change_started)
                item.sigRegionChangeFinished.connect(self.on_item_state_change_finished)
        self._signals_blocked = v

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
        color = color or self.default_color
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
            color=color or self.default_color,
            movable=movable,
            id_=id_,
            antialias=False,
        )
        # self.logger.debug(f"Created polygon {id_=}")
        return polygon

    def start_drawing(self):
        match self._draw_mode:
            case DrawMode.RECTANGLE:
                self.current_item = Rectangle(
                    QRectF(0, 0, 0, 0),
                    color=self.default_color,
                    movable=False,
                )  # type: ignore
            case DrawMode.POINT:
                self.current_item = Point(
                    pos=self.mouse_down_pos.toTuple(),  # type: ignore
                    radius=self.point_radius,
                    color=self.default_color,
                )
            case DrawMode.POLYGON:
                # Initialize polygon with first committed vertex
                first = self.mouse_down_pos
                if first is not None:
                    self.polygon_points_committed = [pg.Point(first.x(), first.y())]
                else:
                    self.polygon_points_committed = []
                self.polygon_preview_point = None

                self.current_item = Polygon(
                    positions=[p.toTuple() for p in self.polygon_points_committed],
                    closed=False,
                    color=self.default_color,
                    movable=False,
                )
            case _:
                self.current_item = None
        if self.current_item is not None:
            # self.create_item(self.current_item)
            self.addItem(self.current_item)
        self._drawing = True

    def update_drawing(self):
        if self.current_item is None:
            return
        state = self.get_drawing_item_state()
        self.current_item.setState(state, update=False)
        self.current_item.update()

    def stop_drawing(self):
        if self.current_item is None:
            return

        # Finalize state per item type before removal
        if isinstance(self.current_item, Polygon):
            # Only finalize if there are at least 3 committed vertices
            if len(self.polygon_points_committed) >= 3:
                final_state = {
                    "pos": pg.Point(0.0, 0.0),
                    "size": pg.Point(1.0, 1.0),
                    "angle": 0,
                    "points": list(self.polygon_points_committed),
                    "closed": True,
                    "id": self.current_item.id_,
                }
                self.current_item.setState(final_state, update=True)
                state = self.current_item.getState()
                self.sigPolygonCreated.emit(state)
            # Remove polygon item from scene regardless
            self.removeItem(self.current_item)
            # Reset polygon drawing buffers
            self.polygon_points_committed = []
            self.polygon_preview_point = None
        else:
            # For Rectangle/Point: emit based on current state
            state = self.current_item.getState()
            self.removeItem(self.current_item)
            match self.current_item:
                case Rectangle():
                    if state["size"].x() > 1 and state["size"].y() > 1:
                        self.sigRectangleCreated.emit(state)
                case Point():
                    self.sigPointCreated.emit(state["pos"])
                case _:
                    ...

        # Reset common flags
        self.current_item = None
        self.mouse_down_pos = None
        self.mouse_up_pos = None
        self._drawing = False

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

        # TODO: update existed items' state to avoid recreate
        # but it's strange that the items won't show after `setState`
        keys = list(self.showing_items.keys())
        for k in keys:
            item = self.showing_items.pop(k)
            self.remove_item(item)
        for result in anno.results.values():
            self.create_item_by_result(result)

        # new_keys = list(anno.results.keys())
        # old_keys = list(self.showing_items.keys())
        # done_new_keys = []
        # done_old_keys = []
        # n_old, n_new = len(old_keys), len(new_keys)
        # find_indexer: int = 0
        # n_created = 0
        # n_updated = 0
        # n_hided = 0

        # def find_free_item_by_result(r: RectangleResult | PolygonResult) -> str | None:
        #     nonlocal find_indexer
        #     while find_indexer < n_old:
        #         k = old_keys[find_indexer]
        #         find_indexer += 1
        #         item = self.showing_items[k]
        #         if (k not in done_new_keys) and (
        #             (isinstance(r, RectangleResult) and isinstance(item, Rectangle))
        #             or (isinstance(r, PolygonResult) and isinstance(item, Polygon))
        #         ):
        #             return k
        #     return None

        # # if the number of new results > existed self.rects
        # # change the state of existing rects and add new
        # for result in anno.results.values():
        #     k = find_free_item_by_result(result)
        #     if k is None:
        #         self.create_item_by_result(result)
        #         n_created += 1
        #         continue
        #     item = self.showing_items.pop(k)
        #     item.setVisible(True)
        #     item.setState(result.getState(), update=True)
        #     self.showing_items[result.id] = item
        #     done_new_keys.append(result.id)
        #     done_old_keys.append(k)
        #     n_updated += 1

        # for k in old_keys:
        #     if k not in done_old_keys:
        #         # self.showing_items[k].setVisible(False)
        #         n_hided += 1

        # self.logger.debug(
        #     "Update items finished\n"
        #     f"updated: {n_updated}\n"
        #     f"created: {n_created}\n"
        #     f"hided: {n_hided}\n"
        #     f"existed: {len(self.showing_items)}"
        # )

        self.block_item_state_changed(False)
        self.view_box.enableAutoRange()

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
    def create_item(self, item: Rectangle | Point | Polygon):
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
                color=result.labels[0].color,
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
                item.setFillColor(self.default_color)
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
                color=result.labels[0].color,
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
    def hide_item(self, item: Rectangle | Point | Polygon | None):
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
            if isinstance(item, (Rectangle, Point, Polygon)):
                item.setSelected(item.id_ == id_)
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
                case Rectangle() | Point() | Polygon():
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
        if item == self.selecting_item or not isinstance(item, (Rectangle, Polygon)):
            return
        self.sigItemStateChangeStarted.emit(item.getState())
        self.logger.debug("Item state change started")

    def on_item_state_change_finished(self, item: Rectangle | Polygon):
        if item == self.selecting_item or not isinstance(item, (Rectangle, Polygon)):
            return
        self.sigItemStateChangeFinished.emit(item.getState())
        self.logger.debug("Item state change Finished")

    def on_item_state_changed(self, item: Rectangle | Polygon):
        if item == self.selecting_item or not isinstance(item, (Rectangle, Polygon)):
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
        elif ev.button() == Qt.MouseButton.RightButton:
            # Right-click undo for polygon drawing in CREATE mode
            if self._status_mode == StatusMode.CREATE and self._draw_mode == DrawMode.POLYGON:
                preview_pos = self.map_scene_to_view(ev.pos())
                self.undo_last_polygon_point(preview_pos)
                ev.accept()
                return
            # Otherwise, let base behavior handle (e.g., autorange in ViewBox)
        elif ev.button() == Qt.MouseButton.LeftButton:
            # self.logger.debug(f"ZGraphicsScene Press: {ev=}, {self._status_mode=}")
            self.mouse_down_pos = self.map_scene_to_view(ev.pos())
            if self._status_mode == StatusMode.CREATE:
                self.clear_selections_if_no_ctrl(ev)
                # Branch by draw mode for CREATE
                if self._draw_mode == DrawMode.POLYGON:
                    if self.current_item is None:
                        # Start polygon drawing with first vertex
                        self.start_drawing()
                    else:
                        # Commit the clicked point as a new polygon vertex
                        if self.mouse_down_pos is not None:
                            self.polygon_points_committed.append(
                                pg.Point(self.mouse_down_pos.x(), self.mouse_down_pos.y())
                            )
                            # Clear preview; it will be set by mouse move
                            self.polygon_preview_point = None
                            # Update polygon item to reflect new committed vertices
                            state = self.get_drawing_polygon_state()
                            if state:
                                state["id"] = self.current_item.id_
                                self.current_item.setState(state, update=False)
                    ev.accept()
                    return
                else:
                    # RECTANGLE / POINT create flow
                    if self.current_item is None:
                        self.start_drawing()
                    else:
                        self.update_drawing()
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
                    if isinstance(item, (ZHandle | Handle)):
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
        pos: QPointF = self.map_scene_to_view(ev.pos())
        self.last_mouse_pos_view = pos
        self.hline.setPos(pos.y())
        self.vline.setPos(pos.x())
        self.sigMouseMoved.emit(pos)

        if ev.buttons() & Qt.MouseButton.MiddleButton:
            return super().mouseMoveEvent(ev)

        # Allow polygon live preview even when no mouse button is pressed
        if self._status_mode == StatusMode.CREATE and self._draw_mode == DrawMode.POLYGON and self.current_item:
            prev = self.polygon_preview_point
            # skip redundant updates when preview point unchanged
            if not (prev is not None and prev.x() == pos.x() and prev.y() == pos.y()):
                self.polygon_preview_point = pg.Point(pos.x(), pos.y())
                state = self.get_drawing_polygon_state()
                if state:
                    state["id"] = self.current_item.id_
                    self.current_item.setState(state, update=False)
            ev.accept()
            return

        if ev.buttons() == Qt.MouseButton.LeftButton:
            # self.logger.debug(f"Move: {ev=}, {self._status_mode=}")
            self.mouse_up_pos = pos
            if self._status_mode == StatusMode.CREATE:
                if self.current_item:
                    # Non-polygon create: live adjust with mouse drag
                    if self._draw_mode != DrawMode.POLYGON:
                        state = self.get_drawing_item_state()
                        if state:
                            state["id"] = self.current_item.id_
                            self.current_item.setState(state, update=False)
                ev.accept()
                return
            elif self._status_mode == StatusMode.EDIT:
                state = self.get_drawing_item_state()
                if self.selecting_item and state and isinstance(self.selecting_item, Rectangle):
                    self.selecting_item.setState(state, update=True)
                    ev.accept()
                    return
            elif self._status_mode == StatusMode.VIEW:
                ...
        return super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            # self.logger.debug(f"ZGraphicsScene Release: {ev=}, {self._status_mode=}")
            if self._status_mode == StatusMode.CREATE:
                # Finalize on release for RECTANGLE / POINT only
                if self._draw_mode in (DrawMode.RECTANGLE, DrawMode.POINT):
                    if self._drawing:
                        self.stop_drawing()
                    ev.accept()
                    return
                # POLYGON keeps drawing until Enter/Space to close
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

    def mouseDoubleClickEvent(self, ev: QMouseEvent):
        super().mouseDoubleClickEvent(ev)

    def keyPressEvent(self, ev: QKeyEvent) -> None:
        if ev.key() == Qt.Key.Key_Delete:
            self.remove_selected_items()
            ev.accept()
            return
        elif ev.key() == Qt.Key.Key_Escape:
            # ESC cancels current drawing in CREATE mode
            if self._status_mode == StatusMode.CREATE:
                self.cancel_drawing()
                ev.accept()
                return
        elif self._status_mode == StatusMode.CREATE and self._draw_mode == DrawMode.POLYGON:
            # Backspace or Ctrl+Z undo last committed vertex, keep preview
            if ev.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_X):
                self.undo_last_polygon_point(self.last_mouse_pos_view)
                ev.accept()
                return
            # 'C' behaves like left-click: commit a vertex at current mouse position
            if ev.key() == Qt.Key.Key_C:
                pos = self.last_mouse_pos_view
                if pos is not None:
                    # mimic mouse-down at current cursor location
                    self.mouse_down_pos = pos
                    if self.current_item is None:
                        # start polygon with first vertex
                        self.start_drawing()
                    else:
                        # commit a new vertex
                        self.polygon_points_committed.append(pg.Point(pos.x(), pos.y()))
                        # clear preview; will update by mouse move
                        self.polygon_preview_point = None
                        # update polygon drawing state immediately
                        state = self.get_drawing_polygon_state()
                        if state:
                            state["id"] = self.current_item.id_
                            self.current_item.setState(state, update=False)
                    ev.accept()
                    return
            # 'V' behaves like right-click: undo last vertex while keeping preview
            if ev.key() == Qt.Key.Key_V:
                self.undo_last_polygon_point(self.last_mouse_pos_view)
                ev.accept()
                return
            # Enter / Return / Space finalizes the polygon
            if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
                if self._drawing and self.current_item is not None:
                    self.stop_drawing()
                    ev.accept()
                    return
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

    # reimplement mouseDragEvent to disable continuous axis zoom
    def mouseDragEvent(self, ev, axis=None):
        if axis and ev.button() == Qt.MouseButton.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev, axis=axis)
