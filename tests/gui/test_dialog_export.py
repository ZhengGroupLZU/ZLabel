from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from zlabel.utils import Annotation, Label, PolygonResult, RectangleResult, Task
from zlabel.utils.exporters import ExportFormat, ExportInstance, ExportTask
from zlabel.widgets.dialog_export import DialogExport


@pytest.fixture
def project() -> object:
    from zlabel.utils import Project

    p = Project(id="p1", name="proj", storage_mode="local")
    lbl = Label.new("Seed", "#ff0000")
    p.labels = {lbl.id: lbl}
    p.key_label = lbl.id
    t = Task(id=1, filename="a.png", anno_id="a", labels=[])
    p.tasks[t.anno_id] = t
    p.add_task(t)
    anno = Annotation(id="a", image_path="a.png", original_width=64, original_height=64)
    anno.add_result(RectangleResult.new(id_="r1", x=1, y=1, w=10, h=10, labels=[lbl]))
    anno.add_result(PolygonResult.new(id_="g1", points=[(5, 5), (20, 5), (20, 15), (5, 15)], closed=True, labels=[lbl]))
    p.tasks["a"].anno = anno
    return p


@pytest.fixture
def dialog(qtbot, project) -> DialogExport:
    d = DialogExport(project=project, get_image=lambda name: Image.new("RGB", (64, 64)))
    qtbot.addWidget(d)
    d.resize(600, 500)
    d.show()
    return d


def test_combo_defaults(dialog):
    assert dialog.cmbox_format.currentIndex() == ExportFormat.COCO
    assert dialog.cmbox_task.currentIndex() == ExportTask.DETECTION
    assert dialog.cmbox_inst.count() == 2


def test_output_button_save_file(dialog, mock_qt_dialogs):
    mock_qt_dialogs.file_result = ("C:/out.json", "*.json")
    dialog.on_btn_output()
    assert dialog.ledit_output.text() == "C:/out.json"
    assert any(kind == "getSaveFileName" for kind, _ in mock_qt_dialogs.calls)


def test_output_button_directory(dialog, mock_qt_dialogs):
    dialog.cmbox_format.setCurrentIndex(ExportFormat.YOLO)
    mock_qt_dialogs.directory_result = "C:/yolo"
    dialog.on_btn_output()
    assert dialog.ledit_output.text() == "C:/yolo"
    assert any(kind == "getExistingDirectory" for kind, _ in mock_qt_dialogs.calls)


def test_export_no_output_path(dialog):
    dialog.ledit_output.setText("")
    dialog.on_export()
    assert "output path" in dialog.textBrowser.toPlainText()
    assert dialog.progressBar.value() == 0


def test_export_no_project(qtbot):
    d = DialogExport(project=None)
    qtbot.addWidget(d)
    d.ledit_output.setText("C:/out.json")
    d.on_export()
    assert "No project" in d.textBrowser.toPlainText()


def test_export_coco_writes_json(dialog, tmp_path):
    out = tmp_path / "out.json"
    dialog.ledit_output.setText(str(out))
    dialog.on_export()
    assert dialog.progressBar.value() == 100
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["images"] and data["annotations"]


def test_export_yolo_writes_files(dialog, tmp_path):
    out = tmp_path / "yolo"
    out.mkdir()
    dialog.cmbox_format.setCurrentIndex(ExportFormat.YOLO)
    dialog.ledit_output.setText(str(out))
    dialog.on_export()
    assert dialog.progressBar.value() == 100
    # at least one label/annotation file was written
    assert list(out.iterdir()), "yolo output directory must contain files"


def test_export_error_resets_progress(dialog, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "zlabel.widgets.dialog_export.export_coco",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    out = tmp_path / "out.json"
    dialog.ledit_output.setText(str(out))
    dialog.on_export()
    assert dialog.progressBar.value() == 0
    assert "boom" in dialog.textBrowser.toPlainText()
