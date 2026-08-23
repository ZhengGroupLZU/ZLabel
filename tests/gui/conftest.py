from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pyqtgraph.Qt.QtCore import QPointF, Qt
from pyqtgraph.Qt.QtWidgets import QFileDialog, QInputDialog, QMenu, QMessageBox


# ---------------------------------------------------------------------------
# Blocking-dialog mocks
# ---------------------------------------------------------------------------
class DialogMocks:
    """Canned responses + call log for every blocking Qt dialog.

    Tests change the ``*_result`` attributes before triggering the UI path,
    then inspect ``calls`` to assert the dialog was opened with the right args.
    """

    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []
        self.messagebox_result = QMessageBox.StandardButton.Ok
        self.question_result = QMessageBox.StandardButton.Yes
        self.file_result: tuple[str, str] = ("", "")
        self.directory_result = ""
        self.input_result: tuple[str, bool] = ("", False)
        self.menu_exec_result = None

    def _box(self, kind: str):
        def _f(*args, **_kwargs):
            self.calls.append((kind, args))
            return getattr(self, f"{kind}_result", self.messagebox_result)

        return _f

    def install(self, monkeypatch: pytest.MonkeyPatch):
        from pyqtgraph.Qt.QtWidgets import QMessageBox as _QMB

        monkeypatch.setattr(_QMB, "critical", self._box("critical"))
        monkeypatch.setattr(_QMB, "warning", self._box("warning"))
        monkeypatch.setattr(_QMB, "question", self._box("question"))
        monkeypatch.setattr(_QMB, "information", self._box("information"))

        monkeypatch.setattr(
            QFileDialog,
            "getOpenFileName",
            lambda *a, **k: self.calls.append(("getOpenFileName", a)) or self.file_result,
        )
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            lambda *a, **k: self.calls.append(("getSaveFileName", a)) or self.file_result,
        )
        monkeypatch.setattr(
            QFileDialog,
            "getExistingDirectory",
            lambda *a, **k: self.calls.append(("getExistingDirectory", a)) or self.directory_result,
        )
        monkeypatch.setattr(
            QInputDialog,
            "getText",
            lambda *a, **k: self.calls.append(("getText", a)) or self.input_result,
        )
        monkeypatch.setattr(
            QMenu,
            "exec",
            lambda *a, **k: self.calls.append(("menu.exec", a)) or self.menu_exec_result,
        )


@pytest.fixture
def mock_qt_dialogs(monkeypatch: pytest.MonkeyPatch) -> DialogMocks:
    mocks = DialogMocks()
    mocks.install(monkeypatch)
    return mocks


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
@pytest.fixture
def main_window(qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A fully constructed MainWindow with a local backend and no network.

    ``load_settings`` is neutralized so nothing touches the real home dir or
    starts login/task-fetch workers; the window is injected with a local-mode
    ZSettings + backend. Tests then populate ``win.proj`` directly.
    """
    import zlabel.widgets.mainwindow as mwmod
    from zlabel.utils.backend import build_backend
    from zlabel.widgets.zsettings import ZSettings

    monkeypatch.setattr(mwmod.MainWindow, "load_settings", lambda self: None)

    win = mwmod.MainWindow()
    qtbot.addWidget(win)
    win.resize(1200, 800)
    win.show()

    settings = ZSettings(root_dir=tmp_path)
    settings.project.storage_mode = "local"
    settings.inference_mode = "local"
    win.settings = settings
    win.settings_path = tmp_path / ".zlabel" / ".zlabel.conf"
    win.settings_path.parent.mkdir(parents=True, exist_ok=True)
    win.backend = build_backend(settings)
    win._is_initing = False

    # neutralize network / heavy paths (workers, MNN model load, modal spinner)
    monkeypatch.setattr(win, "try_set_image", lambda image=None: None)
    monkeypatch.setattr(win, "update_inference_status", lambda: None)
    monkeypatch.setattr(win, "load_projects", lambda: None)
    monkeypatch.setattr(win, "load_tasks", lambda: None)
    monkeypatch.setattr(win.dialog_processing, "show", lambda: None)
    monkeypatch.setattr(win.dialog_processing, "close", lambda: None)

    yield win

    # remove translators installed by language tests (QApplication is session-scoped)
    from pyqtgraph.Qt.QtWidgets import QApplication as _QA

    tr = getattr(win, "_translator", None)
    if tr is not None:
        _QA.instance().removeTranslator(tr)
        win._translator = None


@pytest.fixture
def populated_project(main_window, tmp_path: Path, qtbot):
    """MainWindow with one local task + annotation (empty results) + cached
    image, canvas items built and the view fitted to the 64x64 image."""
    win = main_window
    proj = win.proj
    proj.name = "proj"
    proj.storage_mode = "local"
    from zlabel.utils import Label, Task

    lbl = Label.new("A", "#ff0000")
    proj.labels = {lbl.id: lbl}
    proj.key_label = lbl.id
    task = Task(id=1, filename="a.png", anno_id="a", labels=[])
    proj.tasks = {task.anno_id: task}
    proj.add_task(task)

    from zlabel.utils import Annotation

    anno = Annotation(
        id=task.anno_id,
        image_path=str(tmp_path / "a.png"),
        original_width=64,
        original_height=64,
    )
    proj.add_annotation(anno)

    img = Image.fromarray(np.full((64, 64, 3), 128, dtype=np.uint8))
    win._image_cache[task.filename] = img
    win.canvas.update_image(np.asarray(img))
    win.canvas.create_items_by_anno(anno)
    # let the window layout settle (canvas resizes re-range the view)
    qtbot.wait(100)
    win.canvas.view_box.setRange(xRange=[0, 64], yRange=[0, 64], padding=0.0)
    win.canvas._status_mode = None  # reset by tests via actions

    def rebuild(anno_: Annotation | None = None) -> None:
        """Rebuild canvas items + fix the view range (settled layout)."""
        a = anno_ if anno_ is not None else anno
        win.canvas.create_items_by_anno(a)
        win.canvas.view_box.setRange(xRange=[0, 64], yRange=[0, 64], padding=0.0)
        win.canvas.view_box.disableAutoRange()
        qtbot.wait(50)

    return win, proj, anno, rebuild


# ---------------------------------------------------------------------------
# Canvas helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def canvas_view():
    """Helpers to map image coords <-> viewport coords and drive mouse drags."""

    def to_view(canvas, x: float, y: float):
        # image coords -> data coords (view rotation) -> scene -> viewport widget
        data = canvas._img_to_scene(QPointF(x, y))
        scene = canvas.view_box.mapViewToScene(data)
        return canvas.mapFromScene(scene)

    def drag(canvas, p0: tuple[float, float], p1: tuple[float, float], qtbot, steps: int = 6):
        from PySide6.QtTest import QTest

        a = to_view(canvas, *p0)
        b = to_view(canvas, *p1)
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
        qtbot.wait(10)
        for i in range(1, steps + 1):
            t = i / steps
            mp = to_view(canvas, p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
            QTest.mouseMove(canvas.viewport(), mp)
            qtbot.wait(5)
        # Re-send the final position and give the event loop time to deliver it
        # before release when moving existing items (EDIT mode); otherwise the
        # ROI may finish at the previous move step and the drag comes up short.
        from zlabel.utils import StatusMode

        if canvas._status_mode == StatusMode.EDIT:
            QTest.mouseMove(canvas.viewport(), b)
            qtbot.wait(20)
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b)
        qtbot.wait(10)

    def click(canvas, p: tuple[float, float], qtbot, button=Qt.MouseButton.LeftButton):
        from PySide6.QtTest import QTest

        QTest.mouseClick(canvas.viewport(), button, Qt.KeyboardModifier.NoModifier, to_view(canvas, *p))
        qtbot.wait(10)

    return {"to_view": to_view, "drag": drag, "click": click}


@pytest.fixture
def make_anno():
    """Build an Annotation with results of every type."""
    from zlabel.utils import (
        Annotation,
        Label,
        PointResult,
        PolygonResult,
        RectangleResult,
    )

    def _make(
        rects: int = 1,
        points: int = 0,
        polys: int = 0,
        label: Label | None = None,
    ) -> tuple[Annotation, Label]:
        lbl = label or Label.new("A", "#ff0000")
        anno = Annotation(id="a", image_path="a.png", original_width=64, original_height=64)
        for i in range(rects):
            anno.add_result(
                RectangleResult.new(id_=f"r{i}", x=5 + i * 20, y=5 + i * 20, w=15, h=15, labels=[lbl], score=1.0)
            )
        for i in range(points):
            anno.add_result(PointResult.new(id_=f"p{i}", x=10 + i * 10, y=10 + i * 10, labels=[lbl], score=1.0))
        for i in range(polys):
            anno.add_result(
                PolygonResult.new(
                    id_=f"g{i}",
                    points=[(5, 5), (25, 5), (25, 20), (5, 20)],
                    closed=True,
                    labels=[lbl],
                    score=1.0,
                )
            )
        return anno, lbl

    return _make
