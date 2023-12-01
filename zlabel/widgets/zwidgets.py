from typing import Optional
from qtpy.QtWidgets import QListWidgetItem, QHBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QColorDialog, QSlider
from qtpy.QtCore import Qt, Signal, QRect, QRectF, QPointF
from qtpy.QtGui import QIcon, QColor, QPainter, QPen, QBrush, QMouseEvent
from rich import print


class ZListWidgetItem(QListWidgetItem):
    def __init__(self, id_: str, text: str, listview):
        super().__init__(text, listview)
        self.id_ = id_


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
