from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from zlabel.utils import (
    Annotation,
    GermStatus,
    KeypointVisible,
    PointResult,
    PolygonResult,
    RectangleResult,
)

from .ui import Ui_ZDockInfoContent

# field key -> visible row label
_ALL_FIELDS: dict[str, str] = {
    "type": "Type",
    "label": "Label",
    "score": "Score",
    "origin": "Origin",
    "pos": "Position",
    "visible": "Visible",
    "instance": "Instance",
    "size": "Size",
    "rotation": "Rotation",
    "text": "Text",
    "npoints": "Points",
    "area": "Area (px2)",
    "bbox": "BBox",
    "part": "Part",
    "status": "Status",
    "group": "Group",
    "day": "Day",
    "ninstances": "Instances",
    "nresults": "Results",
}

_IMAGE_FIELDS = ("group", "day", "ninstances", "nresults")
_COMMON_FIELDS = ("type", "label", "score", "origin")


def _polygon_area(points: list[tuple[float, float]]) -> float:
    n = len(points)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


class ZDockInfoContent(QWidget, Ui_ZDockInfoContent):
    sigNoteTextChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.ledit_anno_note.textChanged.connect(self.on_ledit_anno_note_textChanged)
        # the generated .ui caps the height at 102px; height is driven by the dock ratio
        self.setMaximumSize(16777215, 16777215)

        # combine image size row + note editor + annotation details into one
        # scrollable content widget; the dock height comes from the layout ratio.
        self._content = QWidget(self)
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(self.label_img_width)
        row.addWidget(self.label)
        row.addWidget(self.label_img_height)
        self._lay.addLayout(row)

        self.gbox_info = QGroupBox("Annotation", self._content)
        self.form = QFormLayout(self.gbox_info)
        self.form.setContentsMargins(6, 6, 6, 6)
        self._rows: list[str] = []
        self._value_labels: dict[str, QLabel] = {}
        for key, name in _ALL_FIELDS.items():
            value = QLabel("")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.form.addRow(name, value)
            self._rows.append(key)
            self._value_labels[key] = value
        self._lay.addWidget(self.gbox_info)
        self._lay.addWidget(self.ledit_anno_note)
        self._lay.addStretch(1)

        self.scroll_info = QScrollArea(self)
        self.scroll_info.setWidget(self._content)
        self.scroll_info.setWidgetResizable(True)
        self.scroll_info.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_info.setGeometry(self.rect())

        self.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scroll_info.setGeometry(self.rect())

    def on_ledit_anno_note_textChanged(self):
        self.sigNoteTextChanged.emit(self.ledit_anno_note.toPlainText())

    # region helpers
    def _set_field(self, key: str, value: str | float | int):
        self._value_labels[key].setText(f"{value:.2f}" if isinstance(value, float) else str(value))

    def _show_rows(self, keys: tuple[str, ...] | list[str]):
        for i, key in enumerate(self._rows):
            self.form.setRowVisible(i, key in keys)

    def clear(self):
        self._show_rows(())
        for v in self._value_labels.values():
            v.setText("")
        self.label_img_width.setText("")
        self.label_img_height.setText("")

    def set_info_by_anno(self, anno: Annotation | None):
        """Image / task level info (shown when nothing is selected)."""
        if anno is None:
            self.clear()
            return
        self.label_img_width.setText(f"{anno.original_width:.2f}")
        self.label_img_height.setText(f"{anno.original_height:.2f}")
        self.ledit_anno_note.setPlainText(anno.note)
        self._show_rows(_IMAGE_FIELDS)
        self._set_field("group", anno.group or "-")
        self._set_field("day", f"D{anno.day}" if anno.day else "-")
        self._set_field("ninstances", len(anno.instances))
        self._set_field("nresults", len(anno.results))

    def set_info_by_result(self, anno: Annotation | None, result=None):
        """Details of the currently selected annotation result."""
        if anno is None or result is None:
            self.set_info_by_anno(anno)
            return
        self.label_img_width.setText(f"{anno.original_width:.2f}")
        self.label_img_height.setText(f"{anno.original_height:.2f}")

        fields = list(_COMMON_FIELDS)
        self._set_field("type", result.type_id.name)
        self._set_field("label", result.labels[0].name if result.labels else "-")
        self._set_field("score", f"{result.score:.2f}")
        self._set_field("origin", result.origin)

        if isinstance(result, PointResult):
            fields += ["pos", "visible", "instance"]
            self._set_field("pos", f"({result.x:.1f}, {result.y:.1f})")
            self._set_field("visible", KeypointVisible(result.visible).name)
            self._set_field("instance", str(result.instance_id) if result.instance_id else "-")
        elif isinstance(result, RectangleResult):
            fields += ["size", "rotation", "text"]
            self._set_field("size", f"({result.x:.1f}, {result.y:.1f}, {result.w:.1f}, {result.h:.1f})")
            self._set_field("rotation", result.rotation)
            self._set_field("text", result.text or "-")
        elif isinstance(result, PolygonResult):
            fields += ["npoints", "area", "bbox", "instance", "part", "status"]
            self._set_field("npoints", len(result.points))
            self._set_field("area", _polygon_area(result.points))
            xs = [p[0] for p in result.points]
            ys = [p[1] for p in result.points]
            bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)) if xs else (0, 0, 0, 0)
            self._set_field("bbox", f"({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f})")
            self._set_field("instance", str(result.instance_id) if result.instance_id else "-")
            self._set_field("part", result.labels[0].name if result.labels else "-")
            status = anno.instances.get(result.instance_id, "") if result.instance_id else ""
            self._set_field("status", status if status else "-")
        self._show_rows(fields)
