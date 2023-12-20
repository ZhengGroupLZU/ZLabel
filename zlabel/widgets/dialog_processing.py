from qtpy.QtCore import Qt, QSize
from qtpy.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from qtpy.QtGui import QFont, QPaintEvent, QPainter, QBrush
import qtawesome as qta  # type: ignore


class DialogProcessing(QDialog):
    def __init__(self, parent):
        super(DialogProcessing, self).__init__(parent)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Loading")
        self.setFixedSize(QSize(130, 135))
        self.icon_widget = qta.IconWidget()
        self.ani = qta.Spin(self.icon_widget, autostart=True)
        self.icon_widget.setIcon(qta.icon("fa5s.spinner", color="green", animation=self.ani))
        self.icon_widget.setIconSize(QSize(90, 90))
        self.icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label = QLabel("Loading...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)

        self.btn_close = QPushButton(qta.icon("fa5s.window-close"), "")
        self.btn_close.setStyleSheet(r"QPushButton{background: transparent}")
        self.btn_close.clicked.connect(self.close)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btn_close)
        hlayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        hlayout.setContentsMargins(0, 0, 0, 0)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.icon_widget)
        vlayout.addWidget(self.label)
        vlayout.setContentsMargins(0, 0, 0, 0)

        self.layout_ = QVBoxLayout(self)
        self.layout_.setSpacing(0)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.addLayout(hlayout)
        self.layout_.addLayout(vlayout)

    def close(self) -> bool:
        return super().close()
        return

    def paintEvent(self, a0: QPaintEvent):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing, True)  # 抗锯齿
        qp.setBrush(QBrush(Qt.GlobalColor.white))
        qp.setPen(Qt.GlobalColor.transparent)
        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        qp.drawRoundedRect(rect, 10, 10)
        qp.end()
