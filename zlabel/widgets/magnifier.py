"""Circular magnifier overlay for the annotation canvas.

The overlay is a child of the canvas viewport. Instead of grabbing the (possibly
OpenGL-backed) viewport, it renders the small scene region under the cursor
directly with QGraphicsScene.render(), so the lens content works even when the
viewport is an OpenGL widget.
"""

from __future__ import annotations

from pyqtgraph.Qt.QtCore import QPoint, QRect, QRectF, Qt
from pyqtgraph.Qt.QtGui import QColor, QPainter, QPainterPath, QPen
from pyqtgraph.Qt.QtWidgets import QWidget

MAGNIFIER_DIAMETER = 200
MAGNIFIER_MIN_ZOOM = 1.0
MAGNIFIER_MAX_ZOOM = 10.0
MAGNIFIER_STEP = 0.5
# lens is drawn above-right of the cursor so it does not hide the mouse
CURSOR_OFFSET = QPoint(30, -30)


class MagnifierOverlay(QWidget):
    def __init__(self, canvas, parent: QWidget | None = None, min_zoom: float = 1.0, max_zoom: float = 10.0):
        super().__init__(parent)
        self._canvas = canvas
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom
        self._zoom = 2.0
        self._diameter = MAGNIFIER_DIAMETER
        self._source_scene_rect = QRectF()
        self._cursor_pos = QPoint()
        self.setFixedSize(self._diameter, self._diameter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def zoom(self) -> float:
        return self._zoom

    def set_zoom_range(self, min_zoom: float, max_zoom: float):
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom
        self.set_zoom(self._zoom)

    def set_zoom(self, zoom: float):
        self._zoom = max(self._min_zoom, min(self._max_zoom, round(zoom * 2) / 2))
        if self.isVisible():
            self.update_content(self._cursor_pos)

    def update_content(self, cursor_pos: QPoint):
        """Compute the scene region under the cursor and reposition the lens."""
        self._cursor_pos = cursor_pos
        viewport = self.parentWidget()
        if viewport is None:
            return

        source_size = max(1, int(self._diameter / self._zoom))
        src = QRect(
            cursor_pos.x() - source_size // 2,
            cursor_pos.y() - source_size // 2,
            source_size,
            source_size,
        )
        # clamp to the viewport
        vp_rect = viewport.rect()
        src = src.intersected(vp_rect)
        if src.width() <= 0 or src.height() <= 0:
            self.hide()
            return

        self._source_scene_rect = self._canvas.mapToScene(src).boundingRect()

        # place the lens above-right of the cursor, clamped inside the viewport
        pos = cursor_pos + CURSOR_OFFSET
        pos.setX(max(0, min(pos.x(), vp_rect.width() - self._diameter)))
        pos.setY(max(0, min(pos.y() - self._diameter, vp_rect.height() - self._diameter)))
        self.move(pos)
        self.show()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(self.rect())
        painter.setClipPath(path)

        if not self._source_scene_rect.isEmpty():
            target = QRectF(self.rect())
            self._canvas.scene().render(painter, target, self._source_scene_rect)

        painter.setClipping(False)
        pen = QPen(QColor("#ffffff"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))

        # center crosshair
        pen = QPen(QColor("#ffffff"))
        pen.setWidth(1)
        painter.setPen(pen)
        cx, cy = self.width() // 2, self.height() // 2
        painter.drawLine(cx - 10, cy, cx + 10, cy)
        painter.drawLine(cx, cy - 10, cx, cy + 10)
