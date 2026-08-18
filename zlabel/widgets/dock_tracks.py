"""Instance timeline dock: a per-frame instance table.

Each column is a frame (D1, D2, ...); rows always run 1..max instance id across
the group (gaps in the middle are empty rows). A cell shows a thumbnail of that
frame cropped around the instance with its id overlaid, or a dim cell when the
frame has no instance with that id.

Clicking a cell jumps to that frame and selects the instance. Dragging a cell
renumbers (or swaps) the source instance within its own frame: only the target
row matters (the drop column is ignored) - if the target row is empty in the
source frame the instance id becomes that row number, otherwise it is swapped
with the occupant.
"""

from __future__ import annotations

from collections.abc import Callable
from os.path import splitext

from PIL import Image
from pyqtgraph.Qt.QtCore import QMimeData, Qt, Signal
from pyqtgraph.Qt.QtGui import QColor, QDrag, QIcon, QPixmap
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

from zlabel.utils.project import Project, Task

INSTANCE_MIME = "application/x-zlabel-instance"


def _instance_bbox(results) -> tuple[int, int, int, int] | None:
    """Axis-aligned bbox (x, y, w, h) covering an instance's results."""
    xs: list[float] = []
    ys: list[float] = []
    for r in results:
        if hasattr(r, "points") and r.points:
            xs += [p[0] for p in r.points]
            ys += [p[1] for p in r.points]
        elif hasattr(r, "x") and hasattr(r, "w"):
            xs += [r.x, r.x + r.w]
            ys += [r.y, r.y + r.h]
        elif hasattr(r, "x"):
            xs.append(r.x)
            ys.append(r.y)
    if not xs or not ys:
        return None
    return int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys))


class _TimelineTable(QTableWidget):
    sigCellMoved = Signal(str, int, int)  # (src_anno, src_iid, target_row)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_press = None
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

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
        # Without this the view's default dragMoveEvent rejects the move (items
        # lack ItemIsDropEnabled), showing the forbidden cursor so the drop can
        # never land on a target cell.
        if ev.mimeData().hasFormat(INSTANCE_MIME):
            ev.acceptProposedAction()
        else:
            super().dragMoveEvent(ev)

    def dropEvent(self, ev):
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


class ZDockTracksContent(QWidget):
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

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.table = _TimelineTable(0, 0)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setDefaultSectionSize(96)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemClicked.connect(self._on_item_clicked)
        self.table.sigCellMoved.connect(self.sigCellMoved)
        lay.addWidget(self.table)

    def set_group(self, project: Project, group: str, tasks: list[Task]):
        """Rebuild the timeline for ``group`` from its (ordered) tasks."""
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

        # per frame: instance_id -> (status, bbox, label_color, results)
        frames: list[tuple[Task, dict[int, tuple[str, tuple | None, str]]]] = []
        instance_order: list[int] = []
        images: dict[str, Image.Image | None] = {}
        for task in self._tasks:
            anno = self._loader(task)
            per: dict[int, tuple[str, tuple | None, str]] = {}
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
                    per[iid] = (status, _instance_bbox(results), color)
            frames.append((task, per))
            if self._get_image is not None:
                images[task.anno_id] = self._get_image(task.filename)

        self.sigGroupChanged.emit(self._group)
        # leading index column + one column per frame
        n_cols = 1 + len(self._tasks)
        self.table.setColumnCount(n_cols)
        self.table.setHorizontalHeaderLabels([""] + [self._frame_label(t) for t, _ in frames])
        self.table.setColumnWidth(0, 40)
        # rows always run 1..max instance id across the group; gaps in the
        # middle stay as empty (inert) rows
        max_iid = max(instance_order) if instance_order else 0
        self.table.setRowCount(max_iid)

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
                    status, bbox, _color = per[iid]
                    cell.setText(f"{iid}" + (f"\n{status}" if status else ""))
                    cell.setToolTip(self.tr(f"{task.filename}: instance {iid}" + (f" ({status})" if status else "")))
                    pix = self._thumbnail(task, images.get(task.anno_id), bbox)
                    if pix is not None:
                        cell.setIcon(QIcon(pix))
                    cell.setForeground(QColor("white"))
                else:
                    cell.setText("·")
                    cell.setBackground(QColor("#202020"))
                self.table.setItem(row, col0, cell)

    def _thumbnail(self, task: Task, image: Image.Image | None, bbox: tuple | None) -> QPixmap | None:
        """Crop the frame image around the instance bbox and scale it to the cell."""
        if image is None or bbox is None:
            return None
        x, y, w, h = bbox
        if w <= 0 or h <= 0:
            return None
        pad = max(4, int(0.08 * max(w, h)))
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(image.width, x + w + pad), min(image.height, y + h + pad)
        if x1 <= x0 or y1 <= y0:
            return None
        crop = image.crop((x0, y0, x1, y1))
        crop.thumbnail((88, 56), Image.Resampling.LANCZOS)
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
