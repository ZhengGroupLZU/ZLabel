import functools
import html
import math
import os
from collections import OrderedDict
from typing import Any

import numpy as np
import pyqtgraph as pg
from PIL import Image
from pyqtgraph.graphicsItems.ROI import Handle
from pyqtgraph.Qt.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer, Signal
from pyqtgraph.Qt.QtGui import QCursor, QKeyEvent, QMouseEvent, QPainterPath, QPixmap, QTransform
from pyqtgraph.Qt.QtWidgets import QGraphicsItem

from zlabel.utils import Annotation, DrawMode, PointResult, PolygonResult, RectangleResult, StatusMode, ZLogger
from zlabel.utils.enums import RgbMode
from zlabel.utils.polygon_ops import merge_polygons as merge_polygons_util
from zlabel.widgets.gl_image_item import GLImageItem
from zlabel.widgets.graphic_objects import InstanceBBox, Point, Polygon, Rectangle, ZHandle
from zlabel.widgets.magnifier import MagnifierOverlay
from zlabel.widgets.zworker import PreparedImage, build_display_pyramid

# Display-layer pyramid: images with a long edge above this are downsampled for
# display only. Annotation coordinates, prompts and results all stay in full
# image space (the ImageItem is scaled up to cover the full-res rect), so only
# the texture/arrays held by the canvas shrink.
DISPLAY_MAX_SIDE = 2560


class Canvas(pg.PlotWidget):
    sigPointCreated = Signal(object)
    sigRectangleCreated = Signal(object)
    sigPolygonCreated = Signal(object)

    sigItemClicked = Signal(str)
    sigItemStateChanged = Signal(object)
    sigItemStateChangeFinished = Signal(object)
    sigItemStateChangeStarted = Signal(object)
    sigItemsRemoved = Signal(object)
    sigSelectionChanged = Signal()

    sigMouseMoved = Signal(QPointF)

    sigMouseBackClicked = Signal()
    sigMouseForwardClicked = Signal()

    def __init__(
        self,
        parent=None,
        background="k",
        status_mode: StatusMode = StatusMode.VIEW,
        enable_catmull_rom: bool = False,
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
        self._polygon_enable_catmull_rom = enable_catmull_rom
        self._point_radius: float = 5.4  # visual radius in view pixels
        self._default_color = "#000000"
        self._alpha: float = 0.3
        self._edit_fill_alpha: float = 0.05
        self._draw_fill_alpha: float = 0.05
        self._drawing = False
        self._z_value = 1
        self._is_editing_handle = False
        self._is_manual_set_state = False
        # track signal block state to avoid redundant (dis)connections
        self._signals_blocked: bool = False
        # items whose state-change signals are currently connected (idempotent
        # connect/disconnect so update_by_anno can't double-connect items)
        self._state_signal_items: set[int] = set()
        self._last_point_zoom: float = 0.0
        self._magnifier_enabled: bool = False
        self._magnifier_zoom: float = 2.0
        self._magnifier: MagnifierOverlay | None = None
        self._magnifier_min_zoom: float = 1.0
        self._magnifier_max_zoom: float = 10.0
        self._magnifier_diameter: int = 200
        self._last_viewport_pos: QPoint | None = None
        self._last_magnifier_pos: QPoint | None = None
        self._display_max_side: int = DISPLAY_MAX_SIDE
        self.view_box.sigRangeChanged.connect(self._update_points_scale)
        self.view_box.sigRightClickFit.connect(self.fit_view)
        self.viewport().installEventFilter(self)

        self._image_backup: np.ndarray | None = None
        # per-mode display arrays (R/G/B/GRAY/RGB) computed once, so switching
        # channels never re-runs an elementwise multiply over the full image
        self._rgb_cache: dict[RgbMode, np.ndarray] = {}
        # the RgbMode currently uploaded to the ImageItem (avoids redundant
        # updateImage() calls after pyramid level switches)
        self._displayed_rgb_mode: RgbMode | None = None
        # explicit display levels (avoids pyqtgraph's full-image min/max scan)
        self._image_levels: tuple[float, float] | None = None
        # full-resolution image size (h, w) and display scale (full/display)
        self._image_hw: tuple[int, int] = (0, 0)
        self._img_scale: float = 1.0
        # view rotation: image + annotations are rotated inside this group; the
        # mouse mapping undoes it so saved coords stay in image space.
        self._rotation: int = 0
        self._rotation_tr = QTransform()
        self._content_group = pg.ItemGroup()
        self.addItem(self._content_group)
        self.image_item = GLImageItem(axisOrder="row-major")
        self.image_item.setZValue(-10)
        self.image_item.setParentItem(self._content_group)
        # The custom pyramid picks the level closest to the view resolution;
        # ImageItem's built-in downsample would run on every zoom/pan frame and
        # add a CPU mean()/rescale pass on top of it, so disable it here.
        self.image_item.setAutoDownsample(False)

        self.current_item: Rectangle | Point | Polygon | None = None
        self.selecting_item: Rectangle | None = None
        self.showing_items: OrderedDict[str, Rectangle | Point | Polygon] = OrderedDict()
        self._instance_bbox_items: dict[int, InstanceBBox] = {}
        # Committed polygon points added by user clicks during CREATE mode
        self.polygon_points_committed: list[pg.Point] = []
        # Current preview point following mouse while drawing polygon
        self.polygon_preview_point: pg.Point | None = None

        self.hline = pg.InfiniteLine(
            angle=0,
            pen=pg.mkPen("#55ff00", width=3),
            movable=False,
        )
        self.vline = pg.InfiniteLine(
            angle=90,
            pen=pg.mkPen("#55ff00", width=3),
            movable=False,
        )
        self.addItem(self.hline, ignoreBounds=True)  # type: ignore
        self.addItem(self.vline, ignoreBounds=True)  # type: ignore

        self.text_item = pg.TextItem(text="", anchor=(0, 0))
        self._text_path = ""
        self._text_label = ""
        self.set_mode_text()
        self.addItem(self.text_item)
        self._batch_update_depth = 0
        self._refresh_bboxes_pending = False
        self._pyramid_levels: list[np.ndarray] = []
        self._pyramid_levels_count: int = 5
        self._active_pyramid_idx = 0
        self._rgb_mode: RgbMode | None = None
        self._level_timer = QTimer(self)
        self._level_timer.setSingleShot(True)
        self._level_timer.setInterval(30)
        self._level_timer.timeout.connect(self._update_display_level)
        self.view_box.sigRangeChanged.connect(self._schedule_level_update)

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
                lambda it: it.isSelected() and it.isVisible() and isinstance(it, (Rectangle, Point, Polygon)),
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

    def _view_zoom(self) -> float:
        """Current zoom: view pixels per scene unit (higher when zoomed in)."""
        vb = self.view_box
        w = vb.width()
        xr = vb.viewRange()[0]
        width = xr[1] - xr[0]
        if w <= 0 or width <= 0:
            return 1.0
        return w / width

    def _point_scene_radius(self) -> float:
        """Scene radius for keypoints: keeps a constant on-screen size."""
        return self.point_radius / self._view_zoom()

    def _update_points_scale(self):
        """Rescale keypoints so their on-screen size stays constant while zooming."""
        zoom = self._view_zoom()
        if abs(zoom - self._last_point_zoom) < 1e-6:
            return  # pure pan, no rescale needed
        self._last_point_zoom = zoom
        radius = self.point_radius / zoom
        for item in self.showing_items.values():
            if isinstance(item, Point):
                item.set_radius(radius)

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

    @property
    def effective_alpha(self) -> float:
        """Fill alpha used for the current mode.

        Drawing (CREATE) and editing use 0.05; other modes use the configured
        alpha so loading/rebuilding annotations keeps the stored appearance.
        """
        if self._status_mode == StatusMode.EDIT:
            return self._edit_fill_alpha
        if self._status_mode == StatusMode.CREATE:
            return self._draw_fill_alpha
        return self._alpha

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
        h, w = img.shape[:2]
        self._image_hw = (h, w)
        # Multi-level display pyramid: low-res textures for zoomed-out pan/zoom,
        # higher-res levels when zoomed in so the view stays crisp.
        self._pyramid_levels = build_display_pyramid(img, self._display_max_side, self._pyramid_levels_count)
        self._active_pyramid_idx = -1
        self._activate_pyramid_level(self._closest_pyramid_level(self._display_max_side))

    @staticmethod
    def _levels_for(img: np.ndarray) -> tuple[float, float]:
        """Display levels without scanning the full image (only uint8 camera
        photos are handled specially; other dtypes are sampled down)."""
        if img.dtype == np.uint8:
            return (0, 255)
        small = img[:: max(1, img.shape[0] // 256), :: max(1, img.shape[1] // 256)]
        return float(small.min()), float(small.max())

    def set_prepared_image(self, prepared: PreparedImage):
        """Apply a display-ready image computed off the UI thread."""
        self._image_hw = prepared.full_hw
        self._pyramid_levels = list(prepared.pyramid) if prepared.pyramid else [prepared.display]
        self._active_pyramid_idx = -1
        active = prepared.active_idx if 0 <= prepared.active_idx < len(self._pyramid_levels) else 0
        self._activate_pyramid_level(active)

    def _closest_pyramid_level(self, target_side: int) -> int:
        if not self._pyramid_levels:
            return 0
        return min(
            range(len(self._pyramid_levels)),
            key=lambda i: abs(max(self._pyramid_levels[i].shape[:2]) - target_side),
        )

    def _activate_pyramid_level(self, idx: int):
        """Switch the ImageItem to pyramid level ``idx`` (keeps full-res coords)."""
        if not self._pyramid_levels:
            return
        idx = max(0, min(idx, len(self._pyramid_levels) - 1))
        if idx == self._active_pyramid_idx and self._image_backup is not None:
            return
        self._active_pyramid_idx = idx
        arr = self._pyramid_levels[idx]
        self._image_backup = arr
        self._rgb_cache = {}
        self._image_levels = self._levels_for(arr)
        h, w = self._image_hw
        max_full = max(h, w)
        level_max = max(arr.shape[:2])
        self._img_scale = max_full / level_max if level_max else 1.0
        display = self._rgb_image(self._rgb_mode) if self._rgb_mode is not None else arr
        if display is None:
            display = arr
        self.image_item.setImage(
            display,
            autoLevels=False,
            autoRange=False,
            levels=self._image_levels,
        )
        self._displayed_rgb_mode = self._rgb_mode
        self.image_item.setScale(self._img_scale)
        self._apply_rotation()

    def _schedule_level_update(self):
        self._level_timer.start()

    def _update_display_level(self):
        """Pick the pyramid level matching the current zoom (throttled)."""
        if len(self._pyramid_levels) <= 1 or self._image_backup is None:
            return
        if self.scene() is None or self.view_box.scene() is None:
            # view is being closed / not attached to a scene anymore
            return
        try:
            vp = self.view_box.viewPixelSize()
        except (RuntimeError, TypeError):
            # view is being closed / not attached to a scene anymore
            return
        if vp is None or vp[0] <= 0:
            return
        vpw = vp[0]
        h, w = self._image_hw
        max_full = max(h, w)
        best = len(self._pyramid_levels) - 1
        for i, arr in enumerate(self._pyramid_levels):
            level_scale = max_full / max(arr.shape[:2])
            if level_scale <= vpw:
                best = i
                break
        if best == self._active_pyramid_idx:
            return
        if best > self._active_pyramid_idx:
            self._activate_pyramid_level(best)
        else:
            active_scale = max_full / max(self._pyramid_levels[self._active_pyramid_idx].shape[:2])
            if active_scale * 2 < vpw:
                self._activate_pyramid_level(best)

    def _rgb_image(self, mode: RgbMode) -> np.ndarray | None:
        """Per-mode display array, computed lazily and cached (R/G/B are views;
        only GRAY needs a real reduction, done once)."""
        if self._image_backup is None:
            return None
        cached = self._rgb_cache.get(mode)
        if cached is not None:
            return cached
        base = self._image_backup
        if mode == RgbMode.RGB:
            arr = base
        elif mode == RgbMode.R:
            arr = np.ascontiguousarray(base[..., 0])
        elif mode == RgbMode.G:
            arr = np.ascontiguousarray(base[..., 1])
        elif mode == RgbMode.B:
            arr = np.ascontiguousarray(base[..., 2])
        elif mode == RgbMode.GRAY:
            gray = np.sum(base * np.asarray([0.299, 0.587, 0.114]), 2)
            arr = gray.astype(np.uint8)
        else:
            raise NotImplementedError
        self._rgb_cache[mode] = arr
        return arr

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
            item.setFillColor(color, self.effective_alpha)

    def set_rgb(self, mode: RgbMode):
        self._rgb_mode = mode
        if self._image_backup is None:
            return
        if mode == self._displayed_rgb_mode:
            return
        arr = self._rgb_image(mode)
        if arr is None:
            return
        # autoLevels=False keeps the fixed levels (no full-image scan per toggle)
        self.image_item.updateImage(arr, autoLevels=False, levels=self._image_levels)
        self._displayed_rgb_mode = mode

    def _update_cursor(self):
        """Cursor for the current mode/draw tool."""
        if self._status_mode in (StatusMode.VIEW, StatusMode.EDIT):
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif self._draw_mode == DrawMode.POLYGON:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def set_status_mode(self, mode: StatusMode):
        # guard to avoid redundant text updates
        if self._status_mode == mode:
            return
        was_edit = self._status_mode == StatusMode.EDIT
        self._status_mode = mode
        self._update_cursor()
        if was_edit and mode != StatusMode.EDIT:
            self._apply_fill_alpha(self._alpha)
        elif mode == StatusMode.EDIT and not was_edit:
            self._apply_fill_alpha(self._edit_fill_alpha)
        self.set_mode_text()

    def _apply_fill_alpha(self, alpha: float):
        """Update the fill alpha of every annotation item."""
        for item in self.showing_items.values():
            item.setFillColor(item.fill_color.name(), alpha)

    def set_enable_catmull_rom(self, enable: bool):
        if self._polygon_enable_catmull_rom == enable:
            return
        self._polygon_enable_catmull_rom = enable

    def set_draw_mode(self, mode: DrawMode):
        # guard to avoid redundant text updates
        if self._draw_mode == mode:
            return
        self._draw_mode = mode
        self._update_cursor()
        self.set_mode_text()

    def set_mode_text(self):
        mode = self._status_mode.name if self._status_mode is not None else "None"
        draw = self._draw_mode.name if self._draw_mode is not None else "None"
        html_text = f"""
        <div style='color: red; font-size: 8pt; font-weight: bold;'>
            <p>Mode: {mode}</p>
            <p>Draw: {draw}</p>
            <p>File: {html.escape(self._text_path)}</p>
            <p>Label: {html.escape(self._text_label)}</p>
        </div>
        """
        self.text_item.setHtml(html_text)

    def set_text_info(self, path: str = "", label: str = ""):
        """Show the current file path and selected label in the overlay text."""
        self._text_path = path
        self._text_label = label
        self.set_mode_text()

    def set_item_state_by_result(
        self,
        result: PointResult | RectangleResult | PolygonResult | None,
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
        # Drawing rect lives in scene space (window-aligned): map the pressed /
        # current image-pixel points into the (rotated) content group's scene.
        d0 = self._img_to_scene(self.mouse_down_pos)
        d1 = self._img_to_scene(self.mouse_up_pos)
        dpos = d1 - d0
        w, h = abs(dpos.x()), abs(dpos.y())
        if w < 1e-3 or h < 1e-3:
            return {}
        # min/max keeps the press point as one fixed corner and the opposite
        # corner exactly under the mouse, in any drag direction.
        x = min(d0.x(), d1.x())
        y = min(d0.y(), d1.y())
        return {
            "pos": pg.Point(x, y),
            "size": pg.Point(w, h),
            "angle": 0,
        }

    def _img_to_scene(self, p: QPointF) -> QPointF:
        """Map an image-pixel point into view/data coordinates (matches the
        crosshair, which uses ViewBox.mapSceneToView) via the rotation transform."""
        return self._rotation_tr.map(QPointF(p.x(), p.y()))

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
            case DrawMode.POINT:
                if self.current_item is not None:
                    return self.current_item.getState()
                return {}
            case DrawMode.POLYGON:
                return self.get_drawing_polygon_state()
            case _:
                return {}

    def _connect_item_state_signals(self, item: Rectangle | Point | Polygon):
        if id(item) in self._state_signal_items:
            return
        item.sigRegionChanged.connect(self.on_item_state_changed)
        item.sigRegionChangeStarted.connect(self.on_item_state_change_started)
        item.sigRegionChangeFinished.connect(self.on_item_state_change_finished)
        self._state_signal_items.add(id(item))

    def _disconnect_item_state_signals(self, item: Rectangle | Point | Polygon):
        if id(item) not in self._state_signal_items:
            return
        item.sigRegionChanged.disconnect(self.on_item_state_changed)
        item.sigRegionChangeStarted.disconnect(self.on_item_state_change_started)
        item.sigRegionChangeFinished.disconnect(self.on_item_state_change_finished)
        self._state_signal_items.discard(id(item))

    def block_item_state_changed(self, v: bool = True):
        # avoid redundant (dis)connections if state unchanged
        if v == self._signals_blocked:
            return
        if v:
            for item in self.showing_items.values():
                self._disconnect_item_state_signals(item)
        else:
            for item in self.showing_items.values():
                self._connect_item_state_signals(item)
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
            alpha=self.effective_alpha,
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
            edge_color=color,
            alpha=self.effective_alpha,
            movable=movable,
            id_=id_,
            antialias=False,
            use_catmull_rom_path=self._polygon_enable_catmull_rom,
        )
        # self.logger.debug(f"Created polygon {id_=}")
        return polygon

    def start_drawing(self):
        match self._draw_mode:
            case DrawMode.RECTANGLE:
                self.current_item = Rectangle(
                    QRectF(0, 0, 0, 0),
                    color=self.default_color,
                    alpha=self._draw_fill_alpha,
                    movable=False,
                )  # type: ignore
            case DrawMode.POINT:
                self.current_item = Point(
                    pos=self.mouse_down_pos.toTuple(),  # type: ignore
                    radius=self._point_scene_radius(),
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
                    edge_color=None,
                    alpha=self._draw_fill_alpha,
                    movable=False,
                    use_catmull_rom_path=self._polygon_enable_catmull_rom,
                )
            case _:
                self.current_item = None
        if self.current_item is not None:
            # self.create_item(self.current_item)
            self.addItem(self.current_item)
            # Rectangle is drawn in scene space so its edges stay parallel to the
            # window under view rotation; points/polygons stay in the rotated group.
            if not isinstance(self.current_item, Rectangle):
                self.current_item.setParentItem(self._content_group)
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
                        # Drawing rect is in scene/data space (window-aligned); the
                        # formal item lives in the rotated content group and rotates
                        # around its anchor, so map the data top-left back to image
                        # coords as the anchor (size is preserved by rotation).
                        inv, _ = self._rotation_tr.inverted()
                        anchor = inv.map(QPointF(state["pos"].x(), state["pos"].y()))
                        state["pos"] = pg.Point(anchor.x(), anchor.y())
                        state["angle"] = -self._rotation
                        self.sigRectangleCreated.emit(state)
                case Point():
                    self.sigPointCreated.emit(state)
                case _:
                    ...

        # Reset common flags
        self.current_item = None
        self.mouse_down_pos = None
        self.mouse_up_pos = None
        self._drawing = False

    def map_scene_to_view(self, point: QPointF):
        pos = self.view_box.mapSceneToView(point)
        if not self._rotation_tr.isIdentity():
            inv, _ = self._rotation_tr.inverted()
            p = inv.map(QPointF(pos.x(), pos.y()))
            return QPointF(p.x(), p.y())
        return QPointF(pos.x(), pos.y())

    # region rotation
    def set_rotation(self, angle: int):
        """Rotate the displayed image+annotations around the image center.

        Stored coords stay in the un-rotated image space; only the view changes.
        """
        self._rotation = int(angle) % 360
        self._apply_rotation()

    def _apply_rotation(self):
        if self._image_backup is not None:
            # keep the data coordinate system fixed so mouse mapping stays stable
            self.view_box.disableAutoRange()
        if self._rotation:
            # rotate around the full-resolution image center (the downsampled
            # ImageItem is scaled to cover the full-res rect)
            h, w = self._image_hw
            cx, cy = w / 2, h / 2
            self._rotation_tr = QTransform().translate(cx, cy).rotate(self._rotation).translate(-cx, -cy)
        else:
            self._rotation_tr = QTransform()
        self._content_group.setTransform(self._rotation_tr)

    def fit_view(self):
        """Zoom/pan so the whole image (including any view rotation) fills the canvas."""
        if self._image_backup is None:
            return
        # Map the image corners through the (possibly rotated) content group into
        # view/data coordinates. Explicit corner mapping avoids ItemGroup bounds
        # caching issues after switching images/rotations.
        rect = self.image_item.boundingRect()
        corners = [
            QPointF(rect.x(), rect.y()),
            QPointF(rect.x() + rect.width(), rect.y()),
            QPointF(rect.x() + rect.width(), rect.y() + rect.height()),
            QPointF(rect.x(), rect.y() + rect.height()),
        ]
        pts = []
        for c in corners:
            d = self.view_box.mapSceneToView(self.image_item.mapToScene(c))
            pts.append((d.x(), d.y()))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        self.view_box.setRange(
            xRange=[min(xs), max(xs)],
            yRange=[min(ys), max(ys)],
            padding=0.05,
        )

    # endregion

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
        self.begin_batch_update()

        # TODO: update existed items' state to avoid recreate
        # but it's strange that the items won't show after `setState`
        keys = list(self.showing_items.keys())
        try:
            for k in keys:
                item = self.showing_items.pop(k)
                self.remove_item(item)
            for result in anno.results.values():
                self.create_item_by_result(result)
        finally:
            self.end_batch_update()

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

        self.refresh_instance_bboxes()
        self.block_item_state_changed(False)
        self.view_box.enableAutoRange()

    def begin_batch_update(self):
        """Suppress per-item instance-bbox rebuilds until end_batch_update()."""
        self._batch_update_depth += 1

    def end_batch_update(self):
        """Re-enable instance-bbox rebuilds and run the single pending refresh."""
        if self._batch_update_depth > 0:
            self._batch_update_depth -= 1
        if self._batch_update_depth == 0 and self._refresh_bboxes_pending:
            self._refresh_bboxes_pending = False
            self.refresh_instance_bboxes()

    def refresh_instance_bboxes(self):
        """Rebuild the per-instance dashed bboxes shown for polygon instances.

        Only instances containing at least one polygon get an overlay; the box
        is the union (maximum) axis-aligned bbox of all member annotations.
        During a batch update the rebuild is deferred to end_batch_update() so
        per-item state events do not trigger O(instances * items) rescans.
        """
        if self._batch_update_depth > 0:
            self._refresh_bboxes_pending = True
            return
        for item in self._instance_bbox_items.values():
            self.removeItem(item)
        self._instance_bbox_items.clear()

        # two linear passes, same rule as before: an overlay only exists for
        # instances containing at least one polygon, and the union includes all
        # member annotations (rectangle/point included)
        polygon_iids = {
            getattr(item, "instance_id", 0)
            for item in self.showing_items.values()
            if item.isVisible() and isinstance(item, Polygon) and getattr(item, "instance_id", 0)
        }
        groups: dict[int, dict[str, Any]] = {}
        for item in self.showing_items.values():
            if not item.isVisible():
                continue
            iid = getattr(item, "instance_id", 0)
            if not iid or iid not in polygon_iids:
                continue
            entry = groups.get(iid)
            if entry is None:
                entry = groups[iid] = {"xs": [], "ys": [], "color": None}
            if entry["color"] is None:
                entry["color"] = getattr(item, "label_color", None) or item.fill_color.name()
            if isinstance(item, Polygon):
                pts = item.getState().get("points") or []
                entry["xs"].extend(float(p[0]) for p in pts)
                entry["ys"].extend(float(p[1]) for p in pts)
            elif isinstance(item, Rectangle):
                st = item.getState()
                x = float(st["pos"].x())
                y = float(st["pos"].y())
                w = float(st["size"].x())
                h = float(st["size"].y())
                ang = math.radians(float(st.get("angle", 0.0)))
                cos_a, sin_a = math.cos(ang), math.sin(ang)
                for lx, ly in ((0.0, 0.0), (w, 0.0), (0.0, h), (w, h)):
                    entry["xs"].append(x + lx * cos_a - ly * sin_a)
                    entry["ys"].append(y + lx * sin_a + ly * cos_a)
            elif isinstance(item, Point):
                st = item.getState()
                entry["xs"].append(float(st["pos"].x()))
                entry["ys"].append(float(st["pos"].y()))
        for iid, entry in groups.items():
            xs = entry["xs"]
            ys = entry["ys"]
            if not xs or not ys:
                continue
            rect = QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
            bbox = InstanceBBox()
            bbox.set_instance(iid, rect, entry["color"])
            bbox.setZValue(self._z_value + 0.5)
            self.addItem(bbox)
            bbox.setParentItem(self._content_group)
            self._instance_bbox_items[iid] = bbox

    def merge_items_by_id(self, ids: list[str]):
        items = [self.showing_items[id_] for id_ in ids]
        self.merge_items(items)

    def merge_rectangles(self, rectangles: list[Rectangle]):
        x0, y0 = 0x3F3F3F, 0x3F3F3F
        x1, y1 = 0.0, 0.0
        for i, rect in enumerate(rectangles):
            state = rect.getState()
            x0 = min(x0, state["pos"].x())
            y0 = min(y0, state["pos"].y())
            x1 = max(x1, state["pos"].x() + state["size"].x())
            y1 = max(y1, state["pos"].y() + state["size"].y())

            if i > 0:  # keep the first as merged item
                rect.setSelected(False)
                self.hide_item(rect)
            self.logger.debug(f"Merge: {x0=}, {y0=}, w={x1 - x0}, h={y1 - y0}")
        self.sigItemsRemoved.emit([item.id_ for item in rectangles[1:]])
        state = rectangles[0].getState()
        self.sigItemStateChangeStarted.emit(state)
        state["pos"] = QPointF(x0, y0)
        state["size"] = QPointF(x1 - x0, y1 - y0)
        rectangles[0].setState(state)
        self.refresh_instance_bboxes()
        self.sigItemStateChangeFinished.emit(rectangles[0].saveState())

    def merge_polygons(self, polygons: list[Polygon]):
        if not polygons:
            return

        polygons[0].removeHandles()
        merged_polygon = merge_polygons_util([list(p.saveState()["points"]) for p in polygons])

        # collect ids of polygons that will be hidden (keep first as primary)
        remove_ids = [p.id_ for p in polygons[1:]] if len(polygons) > 1 else []
        if remove_ids:
            self.sigItemsRemoved.emit(remove_ids)
        for i, p in enumerate(polygons):
            if i > 0:
                p.setSelected(False)
                self.hide_item(p)

        state = polygons[0].getState()
        state["points"] = merged_polygon
        state["closed"] = True
        polygons[0].setState(state, update=True)
        self.refresh_instance_bboxes()

        self.sigItemStateChangeFinished.emit(polygons[0].saveState())

    def merge_items(self, items: list[Any] | None = None):
        items = items or self.selected_items
        if len(items) == 0:
            return
        if all(isinstance(item, Rectangle) for item in items):
            self.merge_rectangles(items)
        elif all(isinstance(item, Polygon) for item in items):
            self.merge_polygons(items)
        else:
            self.logger.warning("Can't merge items")

    # endregion

    # region create
    def create_item(self, item: Rectangle | Point | Polygon):
        item.setZValue(self._z_value)
        item.sigClicked.connect(self.on_item_clicked)
        self._connect_item_state_signals(item)
        if isinstance(item, (Rectangle, Point, Polygon)):
            self.showing_items[item.id_] = item
        self.addItem(item)
        item.setParentItem(self._content_group)
        self._z_value += 1
        # force an immediate repaint so a freshly drawn/created annotation shows
        # right away (scene-change coalescing can otherwise defer the view
        # update until the next auto-range pass / image refresh)
        self.update()
        self.logger.debug(f"Added {item=}")

    def find_invisible_rect(self):
        keys = list(self.showing_items.keys())
        for k in keys:
            item = self.showing_items[k]
            if not item.isVisible():
                return self.showing_items.pop(k)
        return None

    def create_item_by_result(self, result: PointResult | RectangleResult | PolygonResult):
        color = result.labels[0].color if result.labels else None
        if isinstance(result, PointResult):
            point = Point(
                pos=(result.x, result.y),
                radius=self._point_scene_radius(),
                color=color,
                id_=result.id,
            )
            point.set_visible(result.visible)
            self.create_item(point)
            point.set_instance_label(result.instance_id, color)
            self.refresh_instance_bboxes()
        elif isinstance(result, PolygonResult):
            polygon = self.new_polygon(
                positions=result.points,
                closed=True,
                id_=result.id,
                movable=True,
                color=color,
            )
            self.create_item(polygon)
            polygon.set_instance_label(result.instance_id, color)
            self.refresh_instance_bboxes()
        elif isinstance(result, RectangleResult):
            # if result.id existed in self.rects, get the item and set state
            # else if invisible item existed,
            # get a new invisible item and set state
            # else create a new rect
            item = self.showing_items.get(result.id, None) or self.find_invisible_rect()
            if item is not None:
                # Reusing a hidden rect must not emit state-change signals: they
                # would push a spurious MODIFY undo command and corrupt the
                # result data while the item is still keyed by its old id.
                self._disconnect_item_state_signals(item)
                try:
                    state = item.getState()
                    state["pos"] = QPointF(result.x, result.y)
                    state["size"] = QPointF(result.w, result.h)
                    state["id"] = result.id
                    if result.rotation:
                        state["angle"] = result.rotation
                    item.setState(state)
                    item.setFillColor(color or self.default_color)
                    item.setVisible(True)
                    item.set_instance_label(result.instance_id, color)
                finally:
                    self._connect_item_state_signals(item)
                self.showing_items[state["id"]] = item
                self.logger.debug(f"Find existed rect not visible {result.id=}")
                self.update()
                self.refresh_instance_bboxes()
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
            if result.rotation:
                st = rectangle.getState()
                st["angle"] = result.rotation
                rectangle.setState(st)
            self.create_item(rectangle)
            rectangle.set_instance_label(result.instance_id, color)
            self.refresh_instance_bboxes()
        else:
            raise NotImplementedError

    def create_items_by_results(
        self,
        results: list[PointResult | RectangleResult | PolygonResult] | None = None,
    ):
        if results is None:
            return
        self.begin_batch_update()
        try:
            for r in results:
                self.create_item_by_result(r)
        finally:
            self.end_batch_update()

    def create_items_by_anno(self, anno: Annotation | None = None):
        if anno is None:
            return
        self.view_box.disableAutoRange()  # for performance
        self.begin_batch_update()
        try:
            self.clear_all_items()
            for result in anno.results.values():
                self.create_item_by_result(result)
        finally:
            self.end_batch_update()
        self.view_box.enableAutoRange()

    # endregion
    # region remove
    def hide_item(self, item: Rectangle | Point | Polygon | None):
        if item is None:
            return
        item.setVisible(False)

    def remove_selected_items(self):
        self.begin_batch_update()
        try:
            self.sigItemsRemoved.emit([it.id_ for it in self.selected_items])
            for item in self.selected_items:
                self.remove_item(item)  # type: ignore
        finally:
            self.refresh_instance_bboxes()
            self.end_batch_update()

    def remove_item(self, item: QGraphicsItem | None):
        if item is None:
            return
        if isinstance(item, (Point, Polygon, Rectangle)) and item.id_ in self.showing_items:
            self.showing_items.pop(item.id_)
            self._disconnect_item_state_signals(item)
            self.logger.debug(f"remove item: {item.id_}")
        return self.removeItem(item)

    def remove_items_by_anno(self, anno: Annotation):
        if anno is None:
            return
        ids = [r.id for r in anno.results.values()]
        self.remove_items_by_ids(ids)

    def remove_items_by_ids(self, ids: list[str]):
        keys = list(self.showing_items.keys())
        self.begin_batch_update()
        try:
            for id_ in keys:
                if id_ in ids:
                    self.remove_item(self.showing_items[id_])
        finally:
            self.refresh_instance_bboxes()
            self.end_batch_update()

    def clear_all_items(self):
        for item in self.showing_items.values():
            self.removeItem(item)
        self.showing_items.clear()
        self._state_signal_items.clear()
        self.refresh_instance_bboxes()

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

    def select_items(self, ids: list[str]):
        """Select exactly the given annotation items (clears the rest)."""
        id_set = set(ids)
        # creating/removing polygon handles emits sigRegionChanged per handle,
        # which would rebuild instance bboxes per item; disconnect the signals
        # during the batch so selecting N items costs O(N), not O(N * instances)
        self.begin_batch_update()
        try:
            for item in self.items():
                if isinstance(item, (Rectangle, Point, Polygon)):
                    item.setSelected(item.id_ in id_set)
        finally:
            self.end_batch_update()
        self.update()

    def item_at_point(self, point: QPoint | QPointF):
        """Return the topmost annotation item under an image-pixel point.

        Hit-testing runs in image space against ``showing_items`` (items store
        image coordinates and live in the rotated content group), which stays
        reliable under view rotation where scene-space hit tests drift.
        """
        p = QPointF(point.x(), point.y())
        for item in reversed(list(self.showing_items.values())):
            if not item.isVisible():
                continue
            if isinstance(item, Rectangle):
                st = item.getState()
                # handles first: Rectangle only creates them while selected; if we
                # hit a handle, return it so canvas skips clearing the selection.
                if item.handles:
                    ang = math.radians(st["angle"])
                    cos, sin = math.cos(ang), math.sin(ang)
                    hw, hh = st["size"].x(), st["size"].y()
                    radius = max(4.0, getattr(item, "handleSize", 8.0))
                    for hinfo in item.handles:
                        hitem = hinfo.get("item")
                        if hitem is None:
                            continue
                        hp = hinfo.get("pos", (0.0, 0.0))
                        hx = hp[0] * hw
                        hy = hp[1] * hh
                        ix = st["pos"].x() + hx * cos - hy * sin
                        iy = st["pos"].y() + hx * sin + hy * cos
                        if (p.x() - ix) ** 2 + (p.y() - iy) ** 2 <= radius * radius:
                            return hitem
                dx = p.x() - st["pos"].x()
                dy = p.y() - st["pos"].y()
                ang = math.radians(st["angle"])
                cos, sin = math.cos(-ang), math.sin(-ang)
                lx = dx * cos - dy * sin
                ly = dx * sin + dy * cos
                if 0.0 <= lx <= st["size"].x() and 0.0 <= ly <= st["size"].y():
                    return item
            elif isinstance(item, Polygon):
                pts = [(float(x), float(y)) for x, y in item.getState()["points"]]
                # like Rectangle, check the vertex handles first so a press near
                # a vertex grabs the handle instead of clearing/starting a box
                if item.handles:
                    radius = max(8.0, getattr(item, "handleSize", 8.0))
                    for pt, hinfo in zip(pts, item.handles):
                        hitem = hinfo.get("item")
                        if hitem is None:
                            continue
                        if (p.x() - pt[0]) ** 2 + (p.y() - pt[1]) ** 2 <= radius * radius:
                            return hitem
                if self._point_in_polygon(p.x(), p.y(), pts):
                    return item
            elif isinstance(item, Point):
                st = item.getState()
                r = getattr(item, "radius", 8.0)
                if (p.x() - st["pos"].x()) ** 2 + (p.y() - st["pos"].y()) ** 2 <= r * r:
                    return item
        return None

    @staticmethod
    def _point_in_polygon(x: float, y: float, pts: list[tuple[float, float]]) -> bool:
        inside = False
        n = len(pts)
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) + 1e-12) + xi:
                inside = not inside
            j = i
        return inside

    def set_items_movable(self, movable: bool):
        for item in self.showing_items.values():
            if isinstance(item, (Rectangle, Point, Polygon)):
                item.setMovable(movable)

    # endregion

    # region slots
    def on_item_clicked(self, item: Rectangle | Point | Polygon, ev: QMouseEvent):
        # self.current_item = item
        if isinstance(item, (Rectangle, Point, Polygon)):
            self.sigItemClicked.emit(item.id_)

    def on_item_state_change_started(self, item: Rectangle | Point | Polygon):
        if item == self.selecting_item or not isinstance(item, (Rectangle, Point, Polygon)):
            return
        self.sigItemStateChangeStarted.emit(item.saveState())
        self.logger.debug("Item state change started")

    def on_item_state_change_finished(self, item: Rectangle | Point | Polygon):
        if item == self.selecting_item or not isinstance(item, (Rectangle, Point, Polygon)):
            return
        self.sigItemStateChangeFinished.emit(item.saveState())
        self.logger.debug("Item state change Finished")

    def on_item_state_changed(self, item: Rectangle | Point | Polygon):
        if item == self.selecting_item or not isinstance(item, (Rectangle, Point, Polygon)):
            return
        self.sigItemStateChanged.emit(item.saveState())
        if isinstance(item, Polygon) or self._instance_bbox_items:
            self.refresh_instance_bboxes()
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
                preview_pos = self.map_scene_to_view(ev.position())
                self.undo_last_polygon_point(preview_pos)
                ev.accept()
                return
            # Otherwise, let base behavior handle (e.g., autorange in ViewBox)
        elif ev.button() == Qt.MouseButton.LeftButton:
            # self.logger.debug(f"ZGraphicsScene Press: {ev=}, {self._status_mode=}")
            self.mouse_down_pos = self.map_scene_to_view(ev.position())
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
                    # selecting box is scene-space (window-aligned) like drawing rects
                    self.clear_selections_if_no_ctrl(ev)
                    # consume the press so it never reaches a (possibly hidden)
                    # item underneath or the ViewBox, which would drag/pan the
                    # canvas instead of drawing the selection box.
                    ev.accept()
                    return
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
        # Crosshair lives in the (un-rotated) ViewBox data space, so it tracks the
        # mouse on screen; pos below is the rotated image pixel coordinate.
        raw = self.view_box.mapSceneToView(ev.position())
        self.hline.setPos(raw.y())
        self.vline.setPos(raw.x())
        pos: QPointF = self.map_scene_to_view(ev.position())
        self.last_mouse_pos_view = pos
        self.sigMouseMoved.emit(pos)

        viewport_pos = ev.position().toPoint()
        self._last_viewport_pos = viewport_pos
        if self._magnifier_enabled and self._magnifier is not None:
            if self._last_magnifier_pos is None or (viewport_pos - self._last_magnifier_pos).manhattanLength() >= 2:
                self._magnifier.update_content(viewport_pos)
                self._last_magnifier_pos = viewport_pos

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

                selecting = self.selecting_item
                state = selecting.getState()
                lt = self.mapFromScene(self.view_box.mapViewToScene(state["pos"]))
                rb = self.mapFromScene(
                    self.view_box.mapViewToScene(
                        QPoint(
                            state["pos"].x() + state["size"].x(),
                            state["pos"].y() + state["size"].y(),
                        )
                    )
                )
                selection_polygon = self.mapToScene(QRect(lt, rb))
                selection_path = QPainterPath()
                selection_path.addPolygon(selection_polygon)
                items = self.items(
                    QRect(lt, rb),
                    Qt.ItemSelectionMode.IntersectsItemShape,
                )
                # remove the rubber-band before touching selections so it can
                # never be selected/handled by the main window (rapid repeated
                # box selects could otherwise destroy it while still referenced)
                self.remove_item(selecting)
                self.selecting_item = None

                selected_items = []
                for item in items:
                    if item is selecting:
                        continue
                    if isinstance(item, (Point, Rectangle, Polygon)) and item.isVisible():
                        if isinstance(item, Polygon):
                            # Qt's IntersectsItemShape still behaves like a bbox
                            # hit-test for this ROI subclass, so filter polygons
                            # against their exact scene-space shape here.
                            polygon_path = item.mapToScene(item.shape())
                            if not selection_path.intersects(polygon_path):
                                continue
                        item.setSelected(True)
                        selected_items.append(item)
                    # self.logger.debug(f"Release: {item=}, {item.isSelected()=}")

                for item in selected_items:
                    item.update()

                # let the main window sync the annos tree / group-button state
                self.sigSelectionChanged.emit()

                # self.logger.debug(f"{items=}, {rect=}")
            elif self._status_mode == StatusMode.VIEW:
                pass
        return super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev: QMouseEvent):
        # In polygon drawing, a left double-click commits the final vertex (if
        # it is not already the last committed point) and finishes the polygon.
        if (
            ev.button() == Qt.MouseButton.LeftButton
            and self._status_mode == StatusMode.CREATE
            and self._draw_mode == DrawMode.POLYGON
            and self._drawing
            and self.current_item is not None
        ):
            pos = self.map_scene_to_view(ev.position())
            if pos is not None:
                last = self.polygon_points_committed[-1] if self.polygon_points_committed else None
                if last is None or abs(pos.x() - last.x()) > 1e-6 or abs(pos.y() - last.y()) > 1e-6:
                    self.polygon_points_committed.append(pg.Point(pos.x(), pos.y()))
                    self.polygon_preview_point = None
                    state = self.get_drawing_polygon_state()
                    if state:
                        state["id"] = self.current_item.id_
                        self.current_item.setState(state, update=False)
            if len(self.polygon_points_committed) >= 3:
                self.stop_drawing()
            ev.accept()
            return
        super().mouseDoubleClickEvent(ev)

    def apply_appearance_settings(self, settings):
        """Apply Application-tab appearance settings to the canvas."""
        self._display_max_side = int(getattr(settings, "display_max_side", DISPLAY_MAX_SIDE))
        self._pyramid_levels_count = int(getattr(settings, "pyramid_levels", 3))
        self._magnifier_min_zoom = float(getattr(settings, "magnifier_min_zoom", 1.0))
        self._magnifier_max_zoom = float(getattr(settings, "magnifier_max_zoom", 10.0))
        self._magnifier_diameter = int(getattr(settings, "magnifier_diameter", 200))
        self._edit_fill_alpha = float(getattr(settings, "edit_fill_alpha", 0.05))
        self._draw_fill_alpha = float(getattr(settings, "draw_fill_alpha", 0.05))
        if hasattr(self.image_item, "set_mipmap_enabled"):
            self.image_item.set_mipmap_enabled(getattr(settings, "mipmap_enabled", True))
        if self._magnifier is not None:
            self._magnifier.set_zoom_range(self._magnifier_min_zoom, self._magnifier_max_zoom)
            self._magnifier.set_diameter(self._magnifier_diameter)
        hline_color = getattr(settings, "hline_color", "#55ff00")
        hline_width = getattr(settings, "hline_width", 1)
        vline_color = getattr(settings, "vline_color", "#55ff00")
        vline_width = getattr(settings, "vline_width", 1)
        self.hline.setPen(pg.mkPen(hline_color, width=hline_width))
        self.vline.setPen(pg.mkPen(vline_color, width=vline_width))

    def set_magnifier_enabled(self, enabled: bool):
        """Enable/disable the circular magnifier overlay."""
        self._magnifier_enabled = enabled
        if enabled:
            if self._magnifier is None:
                self._magnifier = MagnifierOverlay(
                    self,
                    self.viewport(),
                    min_zoom=self._magnifier_min_zoom,
                    max_zoom=self._magnifier_max_zoom,
                )
            self._magnifier.set_diameter(self._magnifier_diameter)
            self._magnifier.set_zoom(self._magnifier_zoom)
            if self._last_viewport_pos is not None:
                self._magnifier.update_content(self._last_viewport_pos)
        elif self._magnifier is not None:
            self._magnifier.hide()

    def set_magnifier_zoom(self, zoom: float):
        """Set magnifier zoom (clamped to configured range, step 0.5)."""
        self._magnifier_zoom = max(
            self._magnifier_min_zoom,
            min(self._magnifier_max_zoom, round(zoom * 2) / 2),
        )
        if self._magnifier is not None:
            self._magnifier.set_zoom(self._magnifier_zoom)

    def set_magnifier_diameter(self, diameter: int):
        """Set magnifier lens diameter (pixels)."""
        self._magnifier_diameter = max(1, int(diameter))
        if self._magnifier is not None:
            self._magnifier.set_diameter(self._magnifier_diameter)

    def eventFilter(self, obj, event):
        # Ctrl+wheel adjusts the magnifier zoom; plain wheel is left untouched
        # so the ViewBox keeps its normal canvas zoom behaviour.
        if (
            obj is self.viewport()
            and event.type() == QEvent.Type.Wheel
            and self._magnifier_enabled
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            delta = event.angleDelta().y()
            if delta:
                self.set_magnifier_zoom(self._magnifier_zoom + (0.5 if delta > 0 else -0.5))
            event.accept()
            return True
        return False

    def leaveEvent(self, event):
        if self._magnifier is not None:
            self._magnifier.hide()
        super().leaveEvent(event)

    def _delete_hovered_polygon_vertex(self) -> bool:
        """Delete the hovered vertex of a selected polygon in EDIT mode."""
        if self._status_mode != StatusMode.EDIT:
            return False
        for item in self.showing_items.values():
            if not isinstance(item, Polygon) or not item.isSelected() or not item.handles:
                continue
            for info in item.handles:
                handle = info.get("item")
                if handle is not None and getattr(handle, "hovered", False):
                    if len(item.handles) <= 3:
                        return False  # a polygon needs at least 3 vertices
                    item.removeHandle(handle, finish=True)
                    return True
        return False

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
        elif ev.key() == Qt.Key.Key_Backspace and self._status_mode == StatusMode.EDIT:
            if self._delete_hovered_polygon_vertex():
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
    sigRightClickFit = Signal()

    def __init__(self, enableMenu=False, defaultPadding=0.0):
        pg.ViewBox.__init__(self, enableMenu=enableMenu, defaultPadding=defaultPadding)
        self.setMouseMode(self.PanMode)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton:
            self.sigRightClickFit.emit()
        super().mouseClickEvent(ev)

    # reimplement mouseDragEvent to disable continuous axis zoom
    def mouseDragEvent(self, ev, axis=None):
        if axis and ev.button() == Qt.MouseButton.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev, axis=axis)
