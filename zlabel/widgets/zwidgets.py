from pyqtgraph.Qt.QtCore import QByteArray, QPointF, QPropertyAnimation, QSize, Qt, QTimer, Signal
from pyqtgraph.Qt.QtGui import (
    QBrush,
    QColor,
    QGuiApplication,
    QIcon,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
)
from pyqtgraph.Qt.QtWidgets import (
    QApplication,
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


class ZPushButton(QPushButton):
    doubleClicked = Signal()
    singleClicked = Signal()

    def __init__(self, text: str, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emitSingleClicked)
        self._double_click_flag = False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._timer.isActive():
                self._timer.start(QApplication.instance().doubleClickInterval())  # type: ignore
            else:
                self._timer.stop()
                self._double_click_flag = True  # Set flag for double-click
                self.doubleClicked.emit()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._double_click_flag:
            self._double_click_flag = False  # Reset flag
            # Block the default QPushButton's clicked signal if it was a double-click
            # This is crucial to prevent both single and double click signals from firing
            # if the default clicked signal is connected elsewhere.
            # In this specific implementation, we rely on the timer for single clicks,
            # so explicitly blocking the super's release event isn't strictly necessary
            # if you only connect to singleClicked and doubleClicked.
            pass  # We handle click logic with our timer and double_click_flag
        else:
            super().mouseReleaseEvent(event)

    def _emitSingleClicked(self):
        self.singleClicked.emit()


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
    def __init__(self, id_: str, text: str, listview: QListWidget):
        super().__init__(text, listview)
        self.id_ = id_
        self.alpha_ = 0.3
        self.setSizeHint(QSize(100, 30))

    def set_finished(self):
        color = QColor("#24bfa5")
        color.setAlphaF(self.alpha_)
        self.setBackground(color)

    def set_unfinished(self):
        color = QColor("#fd394c")
        color.setAlphaF(self.alpha_)
        self.setBackground(color)


class ZLabelItemWidget(QWidget):
    sigColorChanged = Signal(str)
    sigSelected = Signal()
    sigVisibilityToggled = Signal(str)

    def __init__(
        self,
        id_: str,
        text: str,
        color: str = "#000000",
        btn_text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.id_ = id_
        self.color = color
        self.clipboard = QGuiApplication.clipboard()

        self.btn_visible = QPushButton()
        self.btn_visible.setCheckable(True)
        self.btn_visible.setChecked(True)
        self.btn_visible.setFixedSize(22, 22)
        self.btn_visible.setIcon(QIcon(":/icon/icons/eye-2.svg"))
        self.btn_visible.setToolTip("Show / hide all annotations of this label")
        self.btn_visible.clicked.connect(self.on_visible_clicked)

        self.label_color = ZPushButton(btn_text)
        self.label_color.setMaximumWidth(30)
        self.label_color.clicked.connect(self.sigSelected.emit)
        self.label_color.doubleClicked.connect(self.on_label_color_clicked)
        self.set_label_color(color)

        self.label_text = QLabel(text)

        self.layout_ = QHBoxLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.addWidget(self.btn_visible)
        self.layout_.addWidget(self.label_color)
        self.layout_.addWidget(self.label_text)
        self.setLayout(self.layout_)

    def set_visible_state(self, visible: bool):
        self.btn_visible.blockSignals(True)
        self.btn_visible.setChecked(visible)
        self.btn_visible.blockSignals(False)
        self.btn_visible.setStyleSheet("opacity: 0.35;" if not visible else "")

    def on_visible_clicked(self):
        self.sigVisibilityToggled.emit(self.id_)

    def set_label_color(self, color: str):
        self.label_color.setStyleSheet(f"ZPushButton {{margin: 1px; background-color: {color};}}")

    def on_label_color_clicked(self):
        color = QColorDialog.getColor(QColor(self.color), self)
        if not color.isValid():
            return
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


class ZInstanceItemWidget(QWidget):
    sigVisibilityToggled = Signal(str)
    sigDefaultSelected = Signal(str)

    def __init__(
        self,
        id_: str,
        text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.id_ = id_

        self.btn_visible = QPushButton()
        self.btn_visible.setCheckable(True)
        self.btn_visible.setChecked(True)
        self.btn_visible.setFixedSize(22, 22)
        self.btn_visible.setIcon(QIcon(":/icon/icons/eye-2.svg"))
        self.btn_visible.setToolTip("Show / hide annotations with this instance status")
        self.btn_visible.clicked.connect(self.on_visible_clicked)

        self.radio = QRadioButton()
        self.radio.setFixedSize(22, 22)
        self.radio.setToolTip("Use as the default instance status when merging")
        self.radio.toggled.connect(self.on_radio_toggled)

        self.label_text = QLabel(text)
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # let clicks on the text fall through to the row so the item click can
        # select the radio button
        self.label_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.layout_ = QHBoxLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.addWidget(self.btn_visible)
        self.layout_.addWidget(self.radio)
        self.layout_.addWidget(self.label_text)
        self.setLayout(self.layout_)

    def set_visible_state(self, visible: bool):
        self.btn_visible.blockSignals(True)
        self.btn_visible.setChecked(visible)
        self.btn_visible.blockSignals(False)
        self.btn_visible.setStyleSheet("opacity: 0.35;" if not visible else "")

    def on_visible_clicked(self):
        self.sigVisibilityToggled.emit(self.id_)

    def on_radio_toggled(self, checked: bool):
        if checked:
            self.sigDefaultSelected.emit(self.id_)


class ZColorButton(QPushButton):
    """A small color-swatch button that opens a QColorDialog on click."""

    colorChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None, color: str = "#000000"):
        super().__init__(parent)
        self._color = QColor(color)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(24)
        self.setMinimumWidth(64)
        self.clicked.connect(self._pick_color)
        self._update_style()

    def color(self) -> str:
        return self._color.name()

    def set_color(self, color: str):
        self._color = QColor(color)
        self._update_style()

    def _update_style(self):
        self.setText(self._color.name())
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._color.name()}; color: white; border: 1px solid #888; }}"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(self._color, self)
        if color.isValid():
            self.set_color(color.name())
            self.colorChanged.emit(self.color())


class ZSwitchButton(QPushButton):
    sigCheckStateChanged = Signal(bool)

    def __init__(self, parent: QWidget | None = None):
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

    def paintEvent(self, event: QPaintEvent) -> None:
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
        self.setStyleSheet("""
QSlider::groove:horizontal {
    height: 10px;
}
QSlider::handle:horizontal {
    width: 10px;
    height: 10px;
}""")
        self.label = QLabel(self)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(3)
        self.setLayout(layout)

        self.slider.valueChanged.connect(lambda v: self.label.setText(f"{v}"))
        self.slider.valueChanged.connect(self.valueChanged.emit)

    def setValue(self, v: int) -> None:
        self.slider.setValue(v)


class Toast(QWidget):
    style_sheet = r"#LabelMessage{color:white;font-size:12pt;}"

    def __init__(self, message: str = "", timeout: int = 2000, parent: QWidget | None = None):
        super().__init__(parent)
        self.parent_: QMainWindow | None = parent
        QTimer.singleShot(timeout, self.close)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
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

    def init_ui(self, message: str = ""):
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

    def create_animation(self, timeout: int = 2000):
        self.animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.animation.setTargetObject(self)
        self.animation.setStartValue(0)
        self.animation.setKeyValueAt(0.2, 0.9)
        self.animation.setKeyValueAt(0.8, 0.9)
        self.animation.setEndValue(0)
        self.animation.setDuration(timeout)
        self.animation.start()

    def paintEvent(self, a0: QPaintEvent):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing, True)
        qp.setBrush(QBrush(Qt.GlobalColor.black))
        qp.setPen(Qt.GlobalColor.transparent)
        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        qp.drawRoundedRect(rect, 15, 15)
        qp.end()
