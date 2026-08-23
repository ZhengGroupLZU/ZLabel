from collections.abc import Callable

from PIL import Image
from pyqtgraph.Qt.QtWidgets import QComboBox, QDialog, QFileDialog, QLabel

from zlabel.utils.exporters import (
    ExportFormat,
    ExportInstance,
    ExportTask,
    export_coco,
    export_yolo,
)
from zlabel.utils.project import Project
from zlabel.widgets.zsettings import ZSettings

from .ui import Ui_DialogExport


class DialogExport(QDialog, Ui_DialogExport):
    def __init__(
        self,
        project: Project | None = None,
        get_image: Callable[[str], Image.Image | None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.project: Project | None = project
        self.get_image = get_image

        self.label_inst = QLabel(self.tr("Instance mode:"), self)
        self.cmbox_inst = QComboBox(self)
        self.cmbox_inst.addItems([self.tr("Split by part"), self.tr("Merge by instance")])
        self.gridLayout.addWidget(self.label_inst, 4, 0)
        self.gridLayout.addWidget(self.cmbox_inst, 4, 1)

        self.btn_output.clicked.connect(self.on_btn_output)
        self.btn_export.clicked.connect(self.on_export)
        self.btn_cancel.clicked.connect(self.close)

    def on_btn_output(self):
        if self.cmbox_format.currentIndex() == ExportFormat.COCO:
            path, _ = QFileDialog.getSaveFileName(self, self.tr("Save COCO json"), ".", "JSON (*.json)")
        else:
            path = QFileDialog.getExistingDirectory(self, self.tr("Select output directory"))
        if path:
            self.ledit_output.setText(path)

    def on_export(self):
        if self.project is None:
            self.textBrowser.append(self.tr("No project loaded"))
            return
        output = self.ledit_output.text().strip()
        if not output:
            self.textBrowser.append(self.tr("Please choose an output path first"))
            return
        fmt = ExportFormat(self.cmbox_format.currentIndex())
        task = ExportTask(self.cmbox_task.currentIndex())
        inst_mode = ExportInstance(self.cmbox_inst.currentIndex())
        self.progressBar.setValue(10)
        try:
            if fmt == ExportFormat.COCO:
                stats = export_coco(self.project, output, task, inst_mode)
            else:
                stats = export_yolo(self.project, output, task, self.get_image, inst_mode)
        except Exception as e:
            self.textBrowser.append(self.tr(f"Export failed: {e}"))
            self.progressBar.setValue(0)
            return
        self.progressBar.setValue(100)
        self.textBrowser.append(self.tr(f"Exported {stats['images']} images, {stats['annotations']} annotations."))


def export_dialog(
    project: Project,
    get_image: Callable[[str], Image.Image | None] | None = None,
    parent=None,
) -> DialogExport:
    return DialogExport(project=project, get_image=get_image, parent=parent)
