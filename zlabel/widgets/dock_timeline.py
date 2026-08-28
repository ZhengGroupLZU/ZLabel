"""Instance timeline dock: a per-frame instance table.

Each column is a frame (D1, D2, ...); rows always run 1..max instance id across
the group (gaps in the middle are empty rows) plus one trailing empty row. A
cell shows a thumbnail of that frame cropped around the instance with its id
overlaid, or a dim cell when the frame has no instance with that id.

Clicking a cell jumps to that frame and selects the instance. Dragging a cell
renumbers (or swaps) the source instance within its own frame: only the target
row matters (the drop column is ignored) - if the target row is empty in the
source frame the instance id becomes that row number, otherwise it is swapped
with the occupant.
"""

from __future__ import annotations

from collections.abc import Callable
from os.path import splitext

import numpy as np
from PIL import Image
from pyqtgraph.Qt.QtCore import QMimeData, QPoint, Qt, QTimer, Signal
from pyqtgraph.Qt.QtGui import QColor, QDrag, QPainter, QPixmap
from pyqtgraph.Qt.QtGui import QImage as _QImage
from pyqtgraph.Qt.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from zlabel.utils.cache import LRUCache
from zlabel.utils.project import Project, Task

INSTANCE_MIME = "application/x-zlabel-instance"

# timeline thumbnails are <= 88x56, so a 512px-long-edge working image is plenty
SMALL_IMAGE_SIDE = 512
# number of small thumbnail images kept in memory across groups
SMALL_IMAGE_CACHE_SIZE = 32
# instance cells are square (width == height); the thumbnail keeps its aspect
CELL_SIZE = 48
# thumbnails are rendered at 2x the cell size (supersampled) and downscaled on
# draw, so the smaller cell still shows a crisp image
THUMBNAIL_MAX = 2 * CELL_SIZE


def _instance_bbox(results) -> tuple[int, int, int, int] | None:
    """Axis-aligned bbox (x, y, w, h) covering an instance's results."""
    xs: list[float] = []
    ys: list[float] = []
    for r in results:
        if hasattr(r, "points") and r.points:
            xs.extend(p[0] for p in r.points)
            ys.extend(p[1] for p in r.points)
        elif hasattr(r, "x") and hasattr(r, "w"):
            xs.extend((r.x, r.x + r.w))
            ys.extend((r.y, r.y + r.h))
        elif hasattr(r, "x"):
            xs.append(r.x)
            ys.append(r.y)
    if not xs or not ys:
        return None
    arr_x = np.asarray(xs)
    arr_y = np.asarray(ys)
    x0, y0 = int(arr_x.min()), int(arr_y.min())
    return x0, y0, int(arr_x.max() - x0), int(arr_y.max() - y0)


class _InstanceCellWidget(QWidget):
    """Cell content: the frame thumbnail as the background with the instance id
    overlaid on top. Mouse events pass through so item clicks / drag-drop /
    hover tooltips keep working on the underlying table item."""

    def __init__(self, pixmap: QPixmap | None, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._pixmap = pixmap
        self._text = text
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#202020"))
        if self._pixmap is not None and not self._pixmap.isNull():
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            # keep the thumbnail's aspect ratio, centered in the square cell
            target = self._pixmap.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            x = (self.width() - target.width()) // 2
            y = (self.height() - target.height()) // 2
            p.drawPixmap(x, y, target.width(), target.height(), self._pixmap)
        if self._text:
            # subtle shadow keeps the id readable on any thumbnail
            p.setPen(QColor(0, 0, 0, 180))
            p.drawText(self.rect().translated(1, 1), Qt.AlignmentFlag.AlignCenter, self._text)
            p.setPen(QColor("white"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)


class _TimelineTable(QTableWidget):
    sigCellMoved = Signal(str, int, int)  # (src_anno, src_iid, target_row)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_press = None
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        # Continuous drag auto-scroll: Qt's built-in auto-scroll restarts its
        # timer on every drag-move, so it barely fires; drive a dedicated timer
        # that runs until the cursor leaves the edge margin.
        self.setAutoScroll(False)
        self._drag_scroll_dir = 0
        self._drag_scroll_margin = 24
        self._drag_scroll_timer = QTimer(self)
        self._drag_scroll_timer.setInterval(100)
        self._drag_scroll_timer.timeout.connect(self._drag_scroll_tick)

    def _update_drag_autoscroll(self, pos: QPoint):
        """Start/stop continuous vertical scrolling based on the cursor position
        (in viewport coordinates) relative to the top/bottom edge margin."""
        h = self.viewport().height()
        if pos.y() < self._drag_scroll_margin:
            self._drag_scroll_dir = -1
            if not self._drag_scroll_timer.isActive():
                self._drag_scroll_timer.start()
        elif pos.y() > h - self._drag_scroll_margin:
            self._drag_scroll_dir = 1
            if not self._drag_scroll_timer.isActive():
                self._drag_scroll_timer.start()
        else:
            self._drag_scroll_dir = 0
            self._drag_scroll_timer.stop()

    def _drag_scroll_tick(self):
        sb = self.verticalScrollBar()
        step = 1
        sb.setValue(sb.value() + self._drag_scroll_dir * step)

    def mousePressEvent(self, ev):
        self._drag_press = ev.position().toPoint()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._drag_press and (ev.buttons() & Qt.MouseButton.LeftButton):
            start = self._drag_press
            if (ev.position().toPoint() - start).manhattanLength() >= QApplication.startDragDistance():
                item = self.itemAt(start)
                if item is not None and item.column() > 0:
                    data = item.data(Qt.ItemDataRole.UserRole)
                    if isinstance(data, tuple) and len(data) == 2 and isinstance(data[1], int):
                        mime = QMimeData()
                        mime.setData(INSTANCE_MIME, f"{data[0]}|{data[1]}".encode("ascii"))
                        drag = QDrag(self)
                        drag.setMimeData(mime)
                        drag.exec(Qt.DropAction.CopyAction)
        super().mouseMoveEvent(ev)

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasFormat(INSTANCE_MIME):
            ev.acceptProposedAction()
        else:
            super().dragEnterEvent(ev)

    def dragMoveEvent(self, ev):
        # Run the base class so Qt's drop-indicator logic still happens, then
        # keep the move accepted: the default would otherwise reject because our
        # items lack ItemIsDropEnabled, showing the forbidden cursor so no drop
        # can land. Auto-scroll is handled by _update_drag_autoscroll.
        if ev.mimeData().hasFormat(INSTANCE_MIME):
            super().dragMoveEvent(ev)
            self._update_drag_autoscroll(ev.position().toPoint())
            ev.acceptProposedAction()
        else:
            super().dragMoveEvent(ev)

    def dragLeaveEvent(self, ev):
        self._drag_scroll_timer.stop()
        super().dragLeaveEvent(ev)

    def dropEvent(self, ev):
        self._drag_scroll_timer.stop()
        if ev.mimeData().hasFormat(INSTANCE_MIME):
            src = ev.mimeData().data(INSTANCE_MIME).data().decode("ascii").split("|")
            if len(src) == 2:
                src_anno, src_iid = src[0], int(src[1])
                item = self.itemAt(ev.position().toPoint())
                if item is not None and item.column() > 0:
                    # only the target row matters: the dragged instance is
                    # renumbered (or swapped) within its own frame to that row.
                    # row() is 0-based while the displayed id is row()+1.
                    self.sigCellMoved.emit(src_anno, src_iid, item.row() + 1)
                    ev.acceptProposedAction()
                    return
        super().dropEvent(ev)


class ZDockTimelineContent(QWidget):
    sigOpenInstance = Signal(str, int)  # anno_id, instance_id
    sigCellMoved = Signal(str, int, int)  # (src anno_id, src iid, target row)
    sigGroupChanged = Signal(str)  # current sequence group (for the dock title)

    def __init__(
        self,
        loader: Callable[[Task], object | None],
        get_image: Callable[[str], Image.Image | None] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._loader = loader
        self._get_image = get_image
        self._group = ""
        self._tasks: list[Task] = []
        self._project: Project | None = None
        # (small_image, full_w, full_h) per filename, LRU-bounded
        self._small_images: LRUCache[str, tuple[Image.Image, int, int]] = LRUCache(SMALL_IMAGE_CACHE_SIZE)
        self._small_image_side: int = SMALL_IMAGE_SIDE
        self._cell_size: int = CELL_SIZE
        self._thumbnail_max: int = THUMBNAIL_MAX

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.table = _TimelineTable(0, 0)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setDefaultSectionSize(self._cell_size)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemClicked.connect(self._on_item_clicked)
        self.table.sigCellMoved.connect(self.sigCellMoved)
        lay.addWidget(self.table)

    def apply_performance_settings(
        self,
        small_image_side: int | None = None,
        cache_size: int | None = None,
        cell_size: int | None = None,
    ):
        """Apply Application-tab performance settings (rebuilds when needed)."""
        changed = False
        if small_image_side is not None and small_image_side != self._small_image_side:
            self._small_image_side = max(64, int(small_image_side))
            self._small_images.clear()
            changed = True
        if cache_size is not None and cache_size != self._small_images.maxsize:
            self._small_images = LRUCache(max(1, int(cache_size)))
            changed = True
        if cell_size is not None and cell_size != self._cell_size:
            self._cell_size = max(16, int(cell_size))
            self._thumbnail_max = 2 * self._cell_size
            self.table.horizontalHeader().setDefaultSectionSize(self._cell_size)
            changed = True
        if changed and self._tasks:
            self._rebuild()

    def set_group(self, project: Project, group: str, tasks: list[Task]):
        """Rebuild the timeline for ``group`` from its (ordered) tasks."""
        # a different project may reuse the same filenames with different
        # images, so drop the small-image cache when the project changes
        if self._project is not project:
            self._small_images.clear()
        self._project = project
        self._group = group
        self._tasks = sorted(tasks, key=lambda t: (t.day, t.filename))
        self._rebuild()

    def _rebuild(self):
        self.table.clear()
        if not self._tasks:
            self.sigGroupChanged.emit("")
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        # per frame: instance_id -> (status, bbox, label_color, label_name)
        frames: list[tuple[Task, dict[int, tuple[str, tuple | None, str, str]]]] = []
        instance_order: list[int] = []
        # per frame: (downsampled image, full width, full height) for thumbnails
        images: dict[str, tuple[Image.Image, int, int] | None] = {}
        for task in self._tasks:
            anno = self._loader(task)
            per: dict[int, tuple[str, tuple | None, str, str]] = {}
            if anno is not None:
                by_iid: dict[int, list] = {}
                for r in anno.results.values():
                    iid = getattr(r, "instance_id", 0)
                    if not iid:
                        continue
                    by_iid.setdefault(iid, []).append(r)
                    if iid not in instance_order:
                        instance_order.append(iid)
                for iid, results in by_iid.items():
                    status = anno.instances.get(iid, "") if iid else ""
                    color = results[0].labels[0].color if results[0].labels else "#888888"
                    label = results[0].labels[0].name if results[0].labels else ""
                    per[iid] = (status, _instance_bbox(results), color, label)
            frames.append((task, per))
            images[task.anno_id] = self._small_image(task)

        self.sigGroupChanged.emit(self._group)
        # leading index column + one column per frame
        n_cols = 1 + len(self._tasks)
        self.table.setColumnCount(n_cols)
        self.table.setHorizontalHeaderLabels([""] + [self._frame_label(t) for t, _ in frames])
        self.table.setColumnWidth(0, 40)
        # rows always run 1..max instance id across the group; gaps in the
        # middle stay as empty (inert) rows, plus one trailing empty row
        max_iid = max(instance_order) if instance_order else 0
        self.table.setRowCount(max_iid + 1)
        # square cells: row height matches the (fixed) column width
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, self._cell_size)

        for iid in range(1, max_iid + 1):
            row = iid - 1
            # index cell: colored by the instance's label across the group
            color = "#888888"
            first_anno: str | None = None
            for _task, per in frames:
                if iid in per:
                    if first_anno is None:
                        first_anno = _task.anno_id
                    if color == "#888888" and per[iid][2]:
                        color = per[iid][2]
            idx = QTableWidgetItem(str(iid))
            idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            idx.setBackground(QColor(color))
            # clicking the index jumps to the earliest frame containing the instance
            if first_anno is not None:
                idx.setData(Qt.ItemDataRole.UserRole, (first_anno, iid))
            self.table.setItem(row, 0, idx)

            for col0, (task, per) in enumerate(frames, start=1):
                cell = QTableWidgetItem()
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if iid in per:
                    cell.setData(Qt.ItemDataRole.UserRole, (task.anno_id, iid))
                    status, bbox, _color, label = per[iid]
                    # tooltip: <file path>\nInstance N\n<instance type>
                    type_str = status or label
                    tip = f"{task.filename}\nInstance {iid}\n{type_str}"
                    cell.setText(str(iid))
                    cell.setToolTip(tip)
                    cell.setForeground(QColor("white"))
                    pix = self._thumbnail(task, images.get(task.anno_id), bbox)
                    if pix is not None:
                        w = _InstanceCellWidget(pix, str(iid))
                        w.setToolTip(tip)
                        self.table.setCellWidget(row, col0, w)
                else:
                    cell.setText("·")
                    cell.setBackground(QColor("#202020"))
                self.table.setItem(row, col0, cell)

        # trailing empty row: blank cells with no user data, so a drop lands on
        # it (renumbering to max+1) but clicking does nothing
        for col0 in range(n_cols):
            cell = QTableWidgetItem()
            cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cell.setBackground(QColor("#202020"))
            self.table.setItem(max_iid, col0, cell)

    def _small_image(self, task: Task) -> tuple[Image.Image, int, int] | None:
        """Downsampled copy of the task's frame for thumbnails, cached per
        filename (long edge <= SMALL_IMAGE_SIDE) so rebuilding the timeline
        never re-decodes the full-resolution photo.

        Returns (small_image, full_width, full_height) so cell bboxes (in full
        image coordinates) can be mapped into the small image."""
        cached = self._small_images.get(task.filename)
        if cached is not None:
            return cached
        if self._get_image is None:
            return None
        img = self._get_image(task.filename)
        if img is None:
            return None
        w, h = img.size
        if max(w, h) > self._small_image_side:
            s = self._small_image_side / max(w, h)
            small = img.resize((max(1, round(w * s)), max(1, round(h * s))), Image.Resampling.LANCZOS)
        else:
            small = img
        entry = (small, w, h)
        self._small_images[task.filename] = entry
        return entry

    def _thumbnail(self, task: Task, entry: tuple[Image.Image, int, int] | None, bbox: tuple | None) -> QPixmap | None:
        """Crop the (downsampled) frame image around the instance bbox and scale
        it to the cell. ``bbox`` is in full-resolution coordinates and is mapped
        into the small image via the stored full size."""
        if entry is None or bbox is None:
            return None
        small, full_w, full_h = entry
        if full_w <= 0 or full_h <= 0:
            return None
        x, y, w, h = bbox
        if w <= 0 or h <= 0:
            return None
        sx = small.width / full_w
        sy = small.height / full_h
        pad = max(2, int(0.08 * max(w * sx, h * sy)))
        x0, y0 = max(0, int(x * sx) - pad), max(0, int(y * sy) - pad)
        x1, y1 = min(small.width, int((x + w) * sx) + pad), min(small.height, int((y + h) * sy) + pad)
        if x1 <= x0 or y1 <= y0:
            return None
        crop = small.crop((x0, y0, x1, y1))
        crop.thumbnail((self._thumbnail_max, self._thumbnail_max), Image.Resampling.LANCZOS)
        qimg = _QImage(crop.tobytes(), crop.width, crop.height, crop.width * 3, _QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)

    @staticmethod
    def _frame_label(task: Task) -> str:
        if task.day:
            return f"D{task.day}"
        return splitext(task.filename)[0]

    def _on_item_clicked(self, item: QTableWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, tuple) and len(data) == 2 and isinstance(data[1], int):
            self.sigOpenInstance.emit(data[0], data[1])
