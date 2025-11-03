from typing import Optional
from qtpy.QtWidgets import (
    QListWidgetItem,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QColorDialog,
    QSlider,
    QSizePolicy,
    QListWidget,
    QTableWidgetItem,
    QTableWidget,
    QMainWindow,
)
from qtpy.QtCore import (
    Qt,
    Signal,
    QRect,
    QRectF,
    QPointF,
    QTimer,
    QSize,
    QPropertyAnimation,
    QByteArray,
)
from qtpy.QtGui import (
    QIcon,
    QColor,
    QPainter,
    QPen,
    QBrush,
    QMouseEvent,
    QClipboard,
    QPaintEvent,
    QGuiApplication,
)
from rich import print

from zlabel.utils import Task


class ZListWidget(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def move_current_row(self, prev: bool):
        row = self.currentRow()
        if prev:
            new_row = max(0, row - 1)
        else:
            new_row = min(self.count(), row + 1)
        self.setCurrentRow(new_row)
        self.itemClicked.emit(self.currentItem())

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.BackButton:
            self.move_current_row(prev=True)
            e.accept()
            return
        elif e.button() == Qt.MouseButton.ForwardButton:
            self.move_current_row(prev=False)
            e.accept()
            return
        return super().mousePressEvent(e)


class ZTableWidget(QTableWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.insertColumn(0)
        self.insertColumn(1)
        self.setHorizontalHeaderLabels(["id", "File Name"])
        self.setColumnWidth(0, 50)
        self.setColumnWidth(1, 100)

    def move_current_row(self, prev: bool):
        row = self.currentRow()
        if prev:
            new_row = max(0, row - 1)
        else:
            new_row = min(self.rowCount(), row + 1)
        self.selectRow(new_row)
        self.itemClicked.emit(self.currentItem())

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.BackButton:
            self.move_current_row(prev=True)
            e.accept()
            return
        elif e.button() == Qt.MouseButton.ForwardButton:
            self.move_current_row(prev=False)
            e.accept()
            return
        return super().mousePressEvent(e)


class ZTableWidgetItem(QTableWidgetItem):
    def __init__(self, id_: str, txt: str, finished: bool = False):
        super().__init__()
        self.alpha_ = 0.3

        self.id_ = id_
        self.setText(txt)
        self.setToolTip(txt)
        if finished:
            self.set_finished()
        else:
            self.set_unfinished()

    def set_finished(self):
        color = QColor("#24bfa5")
        color.setAlphaF(self.alpha_)
        self.setBackground(color)

    def set_unfinished(self):
        color = QColor("#fd394c")
        color.setAlphaF(self.alpha_)
        self.setBackground(color)


class ZListWidgetItem(QListWidgetItem):
    def __init__(self, id_: str, text: str, listview):
        super().__init__(text, listview)
        self.id_ = id_
        self.alpha_ = 0.3

    def set_finished(self):
        color = QColor("#24bfa5")
        color.setAlphaF(self.alpha_)
        self.setBackground(color)

    def set_unfinished(self):
        color = QColor("#fd394c")
        color.setAlphaF(self.alpha_)
        self.setBackground(color)


class ZLabelItemWidget(QWidget):
    sigBtnDeleteClicked = Signal(str)
    sigColorChanged = Signal(str)

    def __init__(
        self,
        id_: str,
        text: str,
        color: str = "#000000",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.id_ = id_
        self.color = color
        self.clipboard = QGuiApplication.clipboard()

        self.label_color = QPushButton("")
        self.label_color.setMaximumWidth(20)
        self.label_color.clicked.connect(self.on_label_color_clicked)
        self.set_label_color(color)
        self.label_text = QLabel(text)
        self.btn_delete = QPushButton()
        self.btn_delete.setMaximumSize(20, 20)
        self.btn_delete.setIcon(QIcon(":/icon/icons/delete-3.svg"))
        self.btn_delete.clicked.connect(self.on_btn_delete_clicked)

        self.layout_ = QHBoxLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.addWidget(self.label_color)
        self.layout_.addWidget(self.label_text)
        self.layout_.addWidget(self.btn_delete)
        self.setLayout(self.layout_)

    def set_label_color(self, color: str):
        self.label_color.setStyleSheet(f"QPushButton {{margin: 3px; background-color : {color};}}")

    def on_btn_delete_clicked(self):
        self.sigBtnDeleteClicked.emit(self.id_)

    def on_label_color_clicked(self):
        color = QColorDialog.getColor(QColor(self.color), self)
        self.color = color.name()
        self.set_label_color(self.color)
        self.sigColorChanged.emit(self.id_)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            text = self.label_text.text()
            self.clipboard.setText(text)
            Toast("Copied to clipboard!", parent=self.parent().parent()).show()
            event.accept()
            return
        return super().mousePressEvent(event)


class ZSwitchButton(QPushButton):
    sigCheckStateChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self._bg_checked_color = QColor("#06b6d4")
        self._bg_unchecked_color = QColor("#334155")
        self._fg_checked_color = QColor("#ffffff")
        self._fg_unchecked_color = QColor("#f4511e")
        self._border_color = QColor("#4e7ab5")
        self._border_color.setAlphaF(0.0)

        self._pen = QPen(self._border_color)
        self._pen.setWidth(1)
        self._radius = 9
        self.setFixedSize(self._radius * 4, self._radius * 2)

    def paintEvent(self, event):
        fg_color = self._fg_checked_color if self.isChecked() else self._fg_unchecked_color
        bg_color = self._bg_checked_color if self.isChecked() else self._bg_unchecked_color

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # draw background
        painter.setBrush(bg_color)
        painter.setPen(self._pen)
        painter.drawRoundedRect(self.rect(), self._radius, self._radius)

        # draw foreground
        painter.setBrush(QBrush(fg_color))
        radius = 0.85 * self._radius
        if self.isChecked():
            center = QPointF(3 * self._radius, self._radius)
        else:
            center = QPointF(self._radius, self._radius)
        painter.drawEllipse(center, radius, radius)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self.sigCheckStateChanged.emit(self.isChecked())
        return super().mouseReleaseEvent(e)


class ZSlider(QWidget):
    valueChanged = Signal(int)

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.slider = QSlider(orientation, self)
        self.slider.setMinimum(1)
        self.slider.setMaximum(200)
        self.label = QLabel(self)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(3)
        self.setLayout(layout)

        self.slider.valueChanged.connect(lambda v: self.label.setText(f"{v}"))
        self.slider.valueChanged.connect(self.valueChanged.emit)

    def setValue(self, v: int):
        self.slider.setValue(v)


class Toast(QWidget):
    style_sheet = r"#LabelMessage{color:white;font-size:12pt;}"

    def __init__(self, message="", timeout=2000, parent=None):
        """
        @param message: 提示信息
        @param timeout: 窗口显示时长
        @param parent: 父窗口控件
        """
        super().__init__(parent)
        self.parent_: QMainWindow | None = parent
        self.timer = QTimer()
        # 由于不知道动画结束的事件，所以借助QTimer来关闭窗口，动画结束就关闭窗口，所以这里的事件要和动画时间一样
        self.timer.singleShot(timeout, self.close)  # singleShot表示timer只会启动一次
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.ToolTip
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 设置窗口透明
        # self.setMaximumSize(QSize(300, 200))
        self.layout_ = QHBoxLayout(self)
        self.layout_.setContentsMargins(3, 3, 3, 3)
        self.animation = None
        self.init_ui(message)
        self.create_animation(timeout)
        self.setStyleSheet(Toast.style_sheet)

        self.center()

    def center(self):
        screen = QGuiApplication.primaryScreen()
        p0 = screen.geometry()
        p = self.frameGeometry()
        self.move(p0.center().x() - p.width() // 2, int((p0.height() - p.height()) * 0.85))

    def init_ui(self, message):
        message_label = QLabel()
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(message_label.sizePolicy().hasHeightForWidth())
        message_label.setSizePolicy(size_policy)
        message_label.setWordWrap(True)
        message_label.setText(message)
        message_label.setTextFormat(Qt.TextFormat.AutoText)
        message_label.setScaledContents(True)
        message_label.setObjectName("LabelMessage")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_.addWidget(message_label)

    def create_animation(self, timeout):
        # 1.定义一个动画
        self.animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.animation.setTargetObject(self)
        # 2.设置属性值
        self.animation.setStartValue(0)
        self.animation.setKeyValueAt(0.2, 0.9)  # 设置插值0.3 表示单本次动画时间的0.3处的时间点
        self.animation.setKeyValueAt(0.8, 0.9)  # 设置插值0.8 表示单本次动画时间的0.3处的时间点
        self.animation.setEndValue(0)
        # 3.设置时长
        self.animation.setDuration(timeout)
        # 4.启动动画
        self.animation.start()

    def paintEvent(self, a0: QPaintEvent):
        qp = QPainter()
        qp.begin(self)  # 不能掉，不然没效果
        qp.setRenderHints(QPainter.RenderHint.Antialiasing, True)  # 抗锯齿
        qp.setBrush(QBrush(Qt.GlobalColor.black))
        qp.setPen(Qt.GlobalColor.transparent)
        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        qp.drawRoundedRect(rect, 15, 15)
        qp.end()
