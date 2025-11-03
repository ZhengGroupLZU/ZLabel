import pyqtgraph as pg  # type: ignore
from pyqtgraph.graphicsItems.ROI import ROI, Handle
from pyqtgraph.GraphicsScene.mouseEvents import (
    HoverEvent,
    MouseClickEvent,
    MouseDragEvent,
)
from qtpy.QtCore import QPointF, QRectF, Qt, Signal, QTimer
from qtpy.QtGui import QBrush, QColor, QKeyEvent, QPainter, QPen, QPainterPathStroker
from qtpy.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
)
from rich import print

from zlabel.utils import id_uuid4, ZLogger


class Rectangle(pg.RectROI):
    def __init__(
        self,
        rect: QRectF,
        color: str = "#f47b90",
        centered: bool = False,
        sideScalers: bool = False,
        id_: str | None = None,
        **args,
    ):
        self.id_: str = id_ or id_uuid4()
        super().__init__(
            rect.topLeft().toTuple(),
            rect.size().toTuple(),
            centered=centered,
            sideScalers=sideScalers,
            antialias=False,
            **args,
        )
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.logger: ZLogger = ZLogger(__name__)
        self.alpha_: float = 0.1
        self.fill_color: QColor = QColor(color)
        self.fill_color.setAlphaF(self.alpha_)
        self._selected: bool = False
        self._update_pending: bool = False  # 防止频繁更新
        self.brush: QBrush = QBrush(self.fill_color)

        self.selected_pen: QPen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen: QPen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen
        self.handlePen = pg.mkPen(color="black", width=2)

        # 设置缓存模式以提高渲染性能
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
        self.remove_handles()
        self.restore_handles()
        self.hide_handles()

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # def paint(self, p: QPainter, opt, widget):
    #     p.setBrush(self.brush)
    #     self.currentPen = self.pen
    #     if self._selected:
    #         self.currentPen = self.selected_pen
    #     # self.logger.debug(f"{self.id=}, {self._selected=}, {self.currentPen=}")
    #     super().paint(p, opt, widget)

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            if not self._selected:
                self.setSelected(True)
            else:
                self.setSelected(False)
        super().mouseClickEvent(ev)

    def remove_handles(self):
        while self.handles:
            self.removeHandle(0)

    def restore_handles(self):
        for h in self.scale_handles:
            self.addScaleHandle(h[0], h[1])
            # if handle is not None:
            #     handle.sigHovering.connect(self.on_handle_mouse_hover)

    def show_handles(self):
        for h in self.handles:
            h["item"].show()

    def hide_handles(self):
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

    def set_fill_color(self, color: str):
        new_color = QColor(color)
        if self.fill_color.name() != new_color.name():
            self.fill_color = new_color
            self.fill_color.setAlphaF(self.alpha_)
            self.brush = QBrush(self.fill_color)
            self.pen = pg.mkPen(color, width=1)
            self.schedule_update()

    def schedule_update(self):
        if not self._update_pending:
            self._update_pending = True
            QTimer.singleShot(0, self._do_update)

    def _do_update(self):
        self._update_pending = False
        self.update()

    def getState(self):
        state = super().getState()
        state["id"] = self.id_
        return state

    def setState(self, state, update=True):
        super().setState(state, update)
        self.id_ = state["id"]
        self.hide_handles()


class Polygon(pg.GraphicsObject):
    sigClicked = Signal(object, object)  # (self, event)
    sigRegionChanged = Signal(object)  # (self)
    sigRegionChangeStarted = Signal(object)  # (self)
    sigRegionChangeFinished = Signal(object)  # (self)

    def __init__(
        self,
        positions: list[tuple[float, float]],
        closed: bool = False,
        pos: tuple[float, float] | None = None,
        color: str = "#f47b90",
        id_: str | None = None,
        movable: bool = True,
        **args,
    ):
        super().__init__()

        self.id_ = id_ or id_uuid4()
        self.logger = ZLogger(__name__)

        # 基本属性
        self._positions = positions
        self._closed = closed
        self._color = color
        self._movable = movable
        self._selected = False
        self._hovering = False  # 添加悬停状态
        self._dragging = False
        self._drag_start_pos = None
        self._original_positions = None

        # 控制点相关属性
        self.handles = []  # 存储所有控制点
        self._handles_visible = False
        self._dragging_handle = None  # 当前拖拽的控制点

        # 颜色和样式设置
        self.alpha_ = 0.1
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(self.alpha_)

        self.selected_pen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen  # 悬停时使用与选中相同的样式

        # Handle样式
        self.handlePen = pg.mkPen(color="white", width=2)
        self.handleHoverPen = pg.mkPen(color="yellow", width=2)

        # 创建PlotDataItem用于高效绘制数据点
        self._setup_plot_data_item()

        # 创建控制点
        self._create_handles()

        # 设置鼠标交互 - 接受所有鼠标按钮
        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton
        )
        self.setAcceptHoverEvents(True)

        # 设置位置
        if pos is not None:
            self.setPos(pos[0], pos[1])

        # 性能优化设置
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def _setup_plot_data_item(self):
        """设置PlotDataItem用于高效绘制"""
        if not self._positions:
            return

        # 准备数据点
        x_data = [pos[0] for pos in self._positions]
        y_data = [pos[1] for pos in self._positions]

        # 如果是闭合多边形，添加第一个点到末尾
        if self._closed and len(self._positions) > 2:
            x_data.append(self._positions[0][0])
            y_data.append(self._positions[0][1])

        # 创建PlotDataItem
        self.plot_item = pg.PlotDataItem(
            x=x_data,
            y=y_data,
            pen=self.pen,
            brush=pg.mkBrush(self.fill_color) if self._closed else None,
            fillLevel="enclosed" if self._closed else None,
            antialias=False,  # 禁用抗锯齿以提高性能
            connect="all",
        )

        # 将PlotDataItem作为子项添加
        self.plot_item.setParentItem(self)

    def _create_handles(self):
        """创建控制点"""
        self._clear_handles()

        for i, pos in enumerate(self._positions):
            handle = ZHandle(
                radius=4,
                type="s",  # 方形控制点
                pen=self.handlePen,
                hoverPen=self.handleHoverPen,
                parent=self,
                deletable=False,
            )
            handle.setPos(pos[0], pos[1])
            handle.polygon_parent = self  # 设置父多边形引用
            handle.vertex_index = i  # 设置顶点索引

            # 设置handle的可见性
            handle.setVisible(self._handles_visible)
            self.handles.append(handle)

    def _clear_handles(self):
        """清除所有控制点"""
        for handle in self.handles:
            if handle.scene():
                handle.scene().removeItem(handle)
            handle.setParent(None)
        self.handles.clear()

    def _handle_moved(self, handle, index):
        """控制点移动时的回调"""
        if 0 <= index < len(self._positions):
            pos = handle.pos()
            self._positions[index] = (pos.x(), pos.y())
            self._update_plot_data()
            self.sigRegionChanged.emit(self)

    def _handle_move_started(self, handle, index):
        """控制点开始移动时的回调"""
        self.sigRegionChangeStarted.emit(self)

    def _handle_move_finished(self, handle, index):
        """控制点移动结束时的回调"""
        self.sigRegionChangeFinished.emit(self)

    def boundingRect(self):
        """返回边界矩形"""
        if not self._positions:
            return QRectF(0, 0, 1, 1)

        x_coords = [pos[0] for pos in self._positions]
        y_coords = [pos[1] for pos in self._positions]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # 添加一些边距以确保边框完全可见
        margin = 5
        return QRectF(
            min_x - margin,
            min_y - margin,
            max_x - min_x + 2 * margin,
            max_y - min_y + 2 * margin,
        )

    def paint(self, painter, option, widget=None):
        """绘制方法 - 主要由PlotDataItem处理，这里只处理选择状态和悬停状态"""
        if self._selected or self._hovering:
            # 绘制选择边框或悬停高亮
            if self._selected:
                painter.setPen(self.selected_pen)
            else:
                painter.setPen(self.hoverPen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # 绘制多边形轮廓
            if len(self._positions) > 1:
                from qtpy.QtGui import QPolygonF

                polygon = QPolygonF([QPointF(pos[0], pos[1]) for pos in self._positions])
                if self._closed:
                    painter.drawPolygon(polygon)
                else:
                    painter.drawPolyline(polygon)

    def shape(self):
        """返回图形项的精确形状，用于鼠标事件检测"""
        from qtpy.QtGui import QPainterPath, QPolygonF

        if not self._positions or len(self._positions) < 2:
            return QPainterPath()

        path = QPainterPath()
        polygon = QPolygonF([QPointF(pos[0], pos[1]) for pos in self._positions])

        if self._closed and len(self._positions) > 2:
            # 闭合多边形 - 创建填充区域，包括内部
            path.addPolygon(polygon)
            path.closeSubpath()  # 确保路径闭合
            # 设置填充规则，确保内部区域也可点击
            path.setFillRule(Qt.FillRule.WindingFill)
        else:
            # 开放路径 - 创建线条区域
            stroker = QPainterPathStroker()
            stroker.setWidth(max(5, self.pen.width() * 2))  # 设置点击容差
            stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

            line_path = QPainterPath()
            if len(self._positions) > 0:
                line_path.moveTo(QPointF(self._positions[0][0], self._positions[0][1]))
                for pos in self._positions[1:]:
                    line_path.lineTo(QPointF(pos[0], pos[1]))

            path = stroker.createStroke(line_path)

        return path

    def mouseDoubleClickEvent(self, ev: QGraphicsSceneMouseEvent):
        """鼠标双击事件 - 在边缘添加新点"""
        if ev.button() == Qt.MouseButton.LeftButton:
            click_pos = ev.pos()

            # 找到最近的边缘并在该位置插入新点
            insert_index = self._find_insertion_point(click_pos)
            if insert_index is not None:
                new_point = (click_pos.x(), click_pos.y())
                self._positions.insert(insert_index, new_point)

                # 重新创建控制点和更新数据
                self._create_handles()
                self._update_plot_data()

                self.sigRegionChanged.emit(self)
                self.logger.debug(f"Added new point at {new_point} at index {insert_index}")

        ev.accept()

    def _find_insertion_point(self, click_pos):
        """找到插入新点的最佳位置"""
        if len(self._positions) < 2:
            return None

        min_distance = float("inf")
        best_index = None

        # 检查每条边
        for i in range(len(self._positions)):
            if self._closed:
                next_i = (i + 1) % len(self._positions)
            else:
                next_i = i + 1
                if next_i >= len(self._positions):
                    break

            p1 = QPointF(self._positions[i][0], self._positions[i][1])
            p2 = QPointF(self._positions[next_i][0], self._positions[next_i][1])

            # 计算点到线段的距离
            distance = self._point_to_line_distance(click_pos, p1, p2)

            if distance < min_distance and distance < 10:  # 10像素的容差
                min_distance = distance
                best_index = next_i

        return best_index

    def _point_to_line_distance(self, point, line_start, line_end):
        """计算点到线段的距离"""
        # 向量计算
        line_vec = line_end - line_start
        point_vec = point - line_start

        line_len_sq = line_vec.x() ** 2 + line_vec.y() ** 2
        if line_len_sq == 0:
            return (point - line_start).manhattanLength()

        # 投影参数
        t = max(
            0,
            min(
                1,
                (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y()) / line_len_sq,
            ),
        )

        # 最近点
        projection = line_start + t * line_vec
        diff = point - projection

        return (diff.x() ** 2 + diff.y() ** 2) ** 0.5

    def mouseClickEvent(self, ev: MouseClickEvent):
        """鼠标点击事件"""
        if ev.button() == Qt.MouseButton.LeftButton:
            self.setSelected(not self._selected)
            self.sigClicked.emit(self, ev)
        ev.accept()

    def setSelected(self, selected):
        """设置选中状态"""
        if self._selected != selected:
            self._selected = selected
            self._handles_visible = selected

            # 更新控制点可见性
            for handle in self.handles:
                handle.setVisible(self._handles_visible)

            self.update()
            self.sigSelectionChanged.emit(self)

    def show_handles(self):
        """显示控制点"""
        self._handles_visible = True
        for handle in self.handles:
            handle.setVisible(True)

    def hide_handles(self):
        """隐藏控制点"""
        self._handles_visible = False
        for handle in self.handles:
            handle.setVisible(False)

    def remove_handles(self):
        """移除所有控制点"""
        self._clear_handles()
        self._handles_visible = False

    def restore_handles(self):
        """恢复控制点"""
        self._create_handles()
        self._handles_visible = self._selected

    def mousePressEvent(self, ev):
        """鼠标按下事件"""
        self.logger.debug(f"Polygon mousePressEvent: {ev.button()}")
        if ev.button() == Qt.MouseButton.LeftButton:
            # 记录按下位置，但不立即开始拖拽
            self._press_pos = ev.pos()
            self._press_time = ev.timestamp()
        # 不要调用 ev.accept()，让事件继续传播到 mouseClickEvent

    def mouseMoveEvent(self, ev):
        """鼠标移动事件"""
        if hasattr(self, "_press_pos") and self._movable:
            # 检查是否移动了足够的距离来开始拖拽
            if not self._dragging:
                delta = ev.pos() - self._press_pos
                if (delta.x() ** 2 + delta.y() ** 2) ** 0.5 > 5:  # 5像素的拖拽阈值
                    self._dragging = True
                    self._drag_start_pos = self._press_pos
                    self._original_positions = self._positions.copy()
                    self.sigRegionChangeStarted.emit(self)

            if self._dragging and self._original_positions is not None:
                # 计算偏移量
                delta = ev.pos() - self._drag_start_pos

                # 更新所有点的位置
                new_positions = []
                for orig_pos in self._original_positions:
                    new_pos = (orig_pos[0] + delta.x(), orig_pos[1] + delta.y())
                    new_positions.append(new_pos)

                self._positions = new_positions
                self._update_plot_data()
                self.sigRegionChanged.emit(self)
        # 不调用 ev.accept()，让事件继续传播

    def mouseReleaseEvent(self, ev):
        """鼠标释放事件"""
        was_dragging = self._dragging

        if self._dragging:
            self._dragging = False
            self._drag_start_pos = None
            self._original_positions = None
            self.sigRegionChangeFinished.emit(self)

        # 如果没有拖拽，则处理点击事件
        if not was_dragging and ev.button() == Qt.MouseButton.LeftButton:
            self.logger.debug(f"Polygon clicked using {ev.button()}")
            self.setSelected(not self._selected)
            self.sigClicked.emit(self, ev)

        # 清理按下状态
        if hasattr(self, "_press_pos"):
            delattr(self, "_press_pos")
        if hasattr(self, "_press_time"):
            delattr(self, "_press_time")

        ev.accept()  # 在这里接受事件，因为我们已经处理了点击

    def hoverEnterEvent(self, ev):
        """鼠标悬停进入事件"""
        self._hovering = True
        if self._movable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update()  # 触发重绘以显示悬停效果
        ev.accept()

    def hoverLeaveEvent(self, ev):
        """鼠标悬停离开事件"""
        self._hovering = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()  # 触发重绘以移除悬停效果
        ev.accept()

    def _update_plot_data(self):
        """更新PlotDataItem的数据"""
        if not hasattr(self, "plot_item"):
            return

        x_data = [pos[0] for pos in self._positions]
        y_data = [pos[1] for pos in self._positions]

        if self._closed and len(self._positions) > 2:
            x_data.append(self._positions[0][0])
            y_data.append(self._positions[0][1])

        self.plot_item.setData(x=x_data, y=y_data)
        self.prepareGeometryChange()

    def set_fill_color(self, color: str):
        """设置填充颜色"""
        new_color = QColor(color)
        if self.fill_color.name() != new_color.name():
            self._color = color
            self.fill_color = new_color
            self.fill_color.setAlphaF(self.alpha_)
            self.pen = pg.mkPen(color, width=1)

            # 更新PlotDataItem的样式
            if hasattr(self, "plot_item"):
                self.plot_item.setPen(self.pen)
                if self._closed:
                    self.plot_item.setBrush(pg.mkBrush(self.fill_color))

            self.update()

    def setSelected(self, selected: bool):
        """设置选择状态"""
        if self._selected != selected:
            self._selected = selected
            self.update()

    def isSelected(self) -> bool:
        """返回是否被选中"""
        return self._selected

    def getState(self):
        """获取状态信息"""
        return {
            "id": self.id_,
            "pos": QPointF(0.0, 0.0),  # 保持兼容性
            "size": QPointF(1.0, 1.0),  # 保持兼容性
            "angle": 0,  # 保持兼容性
            "points": self._positions,
            "closed": self._closed,
        }

    def setState(self, state, update=True):
        """设置状态信息"""
        self.id_ = state.get("id", self.id_)
        if "points" in state:
            self._positions = state["points"]
            self._update_plot_data()
        if "closed" in state:
            self._closed = state["closed"]
            self._setup_plot_data_item()

        if update:
            self.update()

    def show_handles(self):
        """显示控制点（保持接口兼容性）"""
        pass  # PlotDataItem不需要显示控制点

    def hide_handles(self):
        """隐藏控制点（保持接口兼容性）"""
        pass  # PlotDataItem不需要隐藏控制点


class Circle(pg.CircleROI):
    def __init__(
        self,
        pos: tuple[float, float],
        radius: float = 1.0,
        color: str = "#f47b90",
        id_: str | None = None,
        **args,
    ):
        super().__init__(pos, radius=radius, **args)

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.id_ = id_ or id_uuid4()

        self.center = QPointF(pos[0] - radius, pos[1] - radius)
        self.fill_color = QColor(color)
        self.fill_color.setAlphaF(0.8)
        self.selected_pen: QPen = pg.mkPen(color="w", width=3)
        self.selected_pen.setStyle(Qt.PenStyle.DashLine)
        self.pen: QPen = pg.mkPen(color=color, width=1)
        self.hoverPen = self.selected_pen
        self.brush = QBrush(self.fill_color)

        self.setPos(self.center)

        while self.handles:
            self.removeHandle(0)

    def paint(self, p: QPainter, opt, widget):
        p.setBrush(self.brush)
        if self.isSelected():
            self.currentPen = self.selected_pen
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

    def mouseDragEvent(self, ev):
        """重写鼠标拖拽事件，通知父多边形更新"""
        super().mouseDragEvent(ev)

        # 通知父多边形更新顶点位置
        if hasattr(self, "polygon_parent") and self.polygon_parent is not None:
            if hasattr(self, "vertex_index") and self.vertex_index is not None:
                pos = self.pos()
                self.polygon_parent._handle_moved(self, self.vertex_index)

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
