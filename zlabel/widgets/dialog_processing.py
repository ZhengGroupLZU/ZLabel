import math

from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QColor, QPainter
from pyqtgraph.Qt.QtWidgets import QDialog, QProgressBar, QPushButton, QVBoxLayout


class CircularProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.setTextVisible(False)
        self._angle = 0
        self._particle_angles = [0] * 6
        self._particle_radius = 30
        self._particle_color = QColor(0, 120, 215)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x, center_y = 50, 50

        # Background circle removed as requested

        # Draw particles
        for particle_angle in self._particle_angles:
            rad = particle_angle * 3.14159 / 180
            x = center_x + self._particle_radius * math.cos(rad)
            y = center_y + self._particle_radius * math.sin(rad)

            color = QColor(self._particle_color)
            # color_value = int(155 + 100 * math.sin(rad))
            # color.setAlpha(color_value)

            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            particle_size = 5
            painter.drawEllipse(
                int(x - particle_size / 2),
                int(y - particle_size / 2),
                int(particle_size),
                int(particle_size),
            )

    def setAngle(self, angle):
        self._angle = angle

        for i in range(len(self._particle_angles)):
            self._particle_angles[i] = (angle - i * 20) % 360

        self.update()

    def getAngle(self):
        return self._angle

    def setParticleColor(self, color):
        self._particle_color = color
        self.update()

    def particleColor(self):
        return self._particle_color


class DialogProcessing(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing")
        self.setFixedSize(300, 150)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        layout = QVBoxLayout(self)

        self.progress_bar = CircularProgressBar(self)
        layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(15)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        # Animation timer for circular progress
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(20)  # Update every 20ms for smooth animation

    def update_animation(self):
        # Update the angle with gravity acceleration effect
        current_angle = self.progress_bar.getAngle()

        # Calculate rotation speed based on angle (gravity effect)
        # 0° = top (slowest), 180° = bottom (fastest)
        # Use sine function to simulate gravity: sin(angle) gives 0 at top/bottom, 1 at bottom
        normalized_angle = (current_angle + 90) % 360  # Shift so 0° is at top
        gravity_factor = abs((normalized_angle - 180) / 180.0)  # 0 at top, 1 at bottom

        # Base speed with gravity acceleration: 2° to 8° per update
        rotation_speed = 2 + gravity_factor * 6

        new_angle = (current_angle + rotation_speed) % 360  # Rotate clockwise
        self.progress_bar.setAngle(new_angle)

    def showEvent(self, event):
        super().showEvent(event)
        self.animation_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.animation_timer.stop()
