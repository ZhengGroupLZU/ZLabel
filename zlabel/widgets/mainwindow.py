import copy
import functools
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from pyqtgraph.Qt.QtCore import QByteArray, QDir, QPointF, QSize, Qt, QThreadPool, QTranslator, Signal
from pyqtgraph.Qt.QtGui import QAction, QCloseEvent, QIcon, QKeySequence, QShortcut, QSurfaceFormat, QUndoStack
from pyqtgraph.Qt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
)

from zlabel.utils import (
    Annotation,
    AnnotationType,
    AutoMode,
    DrawMode,
    FetchType,
    GermStatus,
    KeypointVisible,
    Label,
    Language,
    PointResult,
    PolygonResult,
    Project,
    RectangleResult,
    ResultType,
    RgbMode,
    StatusMode,
    Task,
    User,
    ZLogger,
    id_uuid4,
)
from zlabel.utils.backend import ZLabelBackend, build_backend
from zlabel.widgets import (
    DialogAbout,
    DialogExport,
    DialogProcessing,
    DialogSettings,
    DialogShortcut,
    ResultUndoMode,
    SamWorkerResult,
    Toast,
    ZGetImageWorker,
    ZGetTasksWorker,
    ZLoginThread,
    ZOcrWorker,
    ZResultUndoCmd,
    ZSamPredictWorker,
    ZSettings,
    ZSlider,
    ZUploadFileWorker,
)
from zlabel.widgets.dock_anno import ID_ROLE
from zlabel.widgets.dock_tracks import ZDockTracksContent
from zlabel.widgets.zworker import GetProjectsWorker

from .ui import Ui_MainWindow

sfmt = QSurfaceFormat()
sfmt.setSwapInterval(0)
QSurfaceFormat.setDefaultFormat(sfmt)


@dataclass
class CopyOptions:
    """Result of the copy/propagate dialog."""

    direction: int  # -1 = previous frame, +1 = next frame
    opts: set[str]  # subset of {"dish", "time", "parts"}
    angle: float = 0.0  # rotation applied to copied annotations (deg)
    scale: float = 1.0  # uniform scale applied to copied annotations
    src_center: tuple[float, float] = (0.0, 0.0)  # source frame reference center
    tgt_center: tuple[float, float] = (0.0, 0.0)  # target frame reference center


class MainWindow(QMainWindow, Ui_MainWindow):
    sigSettingsChecked = Signal(bool)
    sigLoginFinished = Signal(bool)

    def __init__(self):
        super().__init__()
        self.logger: ZLogger = ZLogger("MainWindow")
        self.settings_path: Path = Path(QDir.homePath()) / ".zlabel" / ".zlabel.conf"
        self.settings: ZSettings = ZSettings()
        self.backend: ZLabelBackend | None = None
        self.dialog_settings: DialogSettings = DialogSettings(parent=self)
        self.dialog_processing: DialogProcessing = DialogProcessing(parent=self)

        self.user = User.default()
        self.label_default = Label.default()
        self.user_token: str | None = None

        self.undo_stack = QUndoStack(self)
        self.threadpool = QThreadPool()
        self.login_thread: ZLoginThread | None = None

        self.current_instance_id: int = 0
        self._instance_auto_new: bool = True  # canvas annotations always get a new instance
        self._syncing_selection: bool = False  # guard annos<->canvas selection feedback
        self._group_shortcuts: list[QShortcut] = []
        self._point_visible_shortcuts: list[QShortcut] = []

        self.anno_suffix = "zlabel"
        self.last_path = "."
        self._image_cache: dict[str, Image.Image] = {}
        self.threshold = 100
        self.rgb_mode = RgbMode.RGB
        self.canvas_items_visible = True

        self._is_modifying: bool = False
        self._label_shortcuts: list[QShortcut] = []
        self._translator: QTranslator | None = None
        self._is_initing: bool = True
        self._skip_copy_anno: str = ""
        self._label_visibility: dict[str, bool] = {}

        self.init_ui()
        self.init_statusbar()
        self.init_signals()
        self.load_settings()
        # self.ui_update_settings()
        # self.restore_geometry()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        center_point = screen_geometry.center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    # region properties
    @property
    def proj(self) -> Project:
        return self.settings.project

    @functools.cached_property
    def image_paths(self):
        return [task.filename for task in self.proj.tasks.values()]

    @property
    def current_image(self) -> Image.Image | None:
        if self.proj.crt_task is not None:
            img_name = self.proj.crt_task.filename
            if img_name in self._image_cache:
                return self._image_cache[img_name]
        return None

    def cache_image(self, img_name: str, img: Image.Image):
        self._image_cache[img_name] = img

    @property
    def auto_mode(self):
        mode = AutoMode.MANUAL
        if self.settings.sam_enabled and self.settings.cv_enabled:
            mode = AutoMode.SAM & AutoMode.CV
        elif self.settings.sam_enabled:
            mode = AutoMode.SAM
        elif self.settings.cv_enabled:
            mode = AutoMode.CV
        return mode

    # endregion

    # region functions
    def load_settings(self):
        if self.settings_path.exists() and self.settings_path.is_file():
            try:
                self.settings = ZSettings.model_validate_json(self.settings_path.read_text())
                self.set_language(Language(self.settings.language))
                self.dialog_settings.load_settings(self.settings)
                self.ui_update_settings()
                self.restore_geometry()
            except Exception as e:
                self.logger.error(f"Load settings error: {e}")
                self.settings = ZSettings()
                self.dialog_settings.load_settings(self.settings)
                if self.dialog_processing.isVisible():
                    self.dialog_processing.close()
                self.dialog_settings.show()
                return
            finally:
                self._is_initing = False
        else:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings = ZSettings()
            self.settings_path.write_text(self.settings.model_dump_json(ensure_ascii=False, indent=4))
            self.dialog_settings.load_settings(self.settings)
            if self.dialog_processing.isVisible():
                self.dialog_processing.close()
            self.dialog_settings.show()
            self._is_initing = False
            return
        self.user.name = self.settings.username
        self.backend = build_backend(self.settings)
        from zlabel.utils.ocr import set_wxocr_dir

        set_wxocr_dir(self.settings.ocr_wx_dir)
        if self.backend.needs_login:
            if self.settings.host:
                self.dialog_processing.show()
                self.login()
            else:
                if self.dialog_processing.isVisible():
                    self.dialog_processing.close()
        else:
            self.load_projects()
            if self.dialog_processing.isVisible():
                self.dialog_processing.close()
        self._is_initing = False

    def save_geometry(self):
        geometry_data: QByteArray = self.saveGeometry()
        state_data: QByteArray = self.saveState()
        self.settings.geometry = bytes(geometry_data.toBase64().data()).decode("utf-8")
        self.settings.window_state = bytes(state_data.toBase64().data()).decode("utf-8")
        self.settings.save_json(self.settings_path)

    def restore_geometry(self):
        if self.settings.geometry:
            geometry_data: QByteArray = QByteArray.fromBase64(self.settings.geometry.encode("utf-8"))
            if not geometry_data.isEmpty():
                self.restoreGeometry(geometry_data)
        else:
            self.center_on_screen()
        if self.settings.window_state:
            state_data: QByteArray = QByteArray.fromBase64(self.settings.window_state.encode("utf-8"))
            if not state_data.isEmpty():
                self.restoreState(state_data)
        # The Tracks timeline always lives at the bottom; saved layouts from
        # before the move (it used to be a right-side dock) would otherwise
        # place it back on the right.
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_tracks)

    def ui_update_settings(self):
        self.cmbox_anno_type.setCurrentIndex(self.settings.annotation_type.value)
        self.update_anno_type_actions()
        self.set_loglevel(self.settings.log_level.name)
        self.canvas.set_color(self.settings.default_color, self.settings.alpha)
        self.canvas.set_enable_catmull_rom(self.settings.enable_catmull_rom)
        self.canvas.alpha = self.settings.alpha
        self.dockcnt_labels.set_labels(list(self.proj.labels.values()))
        self.update_label_visibility_buttons()
        self.dockcnt_files.cmbox_project.setCurrentIndex(self.settings.project_idx)
        self.dockcnt_files.set_storage_mode(self.proj.storage_mode)
        self.dockcnt_files.set_local_dir(self.proj.local_dir)
        self.dockcnt_files.set_fetch_num_idx_by_value(self.settings.fetch_num)
        self.dockcnt_files.set_file_list(list(self.proj.tasks.values()))
        self.actionSAM.setChecked(self.settings.sam_enabled)
        self.actionOpenCV.setChecked(self.settings.cv_enabled)
        self.action_copy_prev.setEnabled(self.settings.enable_copy_prev)
        title = "ZLabel"
        if self.settings.project_name:
            title += f" - {self.settings.project_name}"
        self.setWindowTitle(title)

        if len(self.proj.tasks) > 0:
            tasks = list(self.proj.tasks.values())
            if self.proj.key_task is None:
                self.proj.key_task = list(self.proj.tasks.keys())[0]
            self.dockcnt_files.set_file_list(tasks)
            self.dockcnt_files.set_row_by_txt(self.proj.key_task)

            if self.proj.crt_anno is None:
                self.on_dock_files_item_clicked(self.proj.key_task)
            if self.proj.crt_anno and len(self.proj.labels) > 0:
                self.proj.key_label = list(self.proj.labels.keys())[0]

        if self.proj.crt_anno and self.proj.labels:
            self.dockcnt_labels.set_labels(list(self.proj.labels.values()), self.proj.key_label)
            self.update_label_visibility_buttons()
            self.dockcnt_anno.set_instance_statuses(list(self.proj.instance_statuses))
            self._refresh_anno_tree()
            self.canvas.create_items_by_anno(self.proj.crt_anno)
            self.apply_label_visibility()
            self.dockcnt_info.set_info_by_anno(self.proj.crt_anno)
        self._refresh_anno_tree()
        self.update_inference_status()
        self.update_storage_status()
        self.try_set_image()

    def init_statusbar(self):
        self.statusbar_inference = QLabel(self.statusbar)
        self.statusbar_inference.setStyleSheet("color: #b4b4b4;")
        self.statusbar.addPermanentWidget(self.statusbar_inference)
        self.statusbar_storage = QLabel(self.statusbar)
        self.statusbar_storage.setStyleSheet("color: #b4b4b4;")
        self.statusbar.addPermanentWidget(self.statusbar_storage)

    def update_inference_status(self):
        """Show the inference mode and local model status on the right side
        of the status bar. Reads the actual backend (which may silently fall
        back to local inference for local-storage projects)."""
        if self.backend is None:
            self.statusbar_inference.setText("Inference: Remote")
            return
        infer = self.backend.inference
        if getattr(infer, "requires_server", True):
            self.statusbar_inference.setText("Inference: Remote")
            return
        status = "not loaded"
        model_status = getattr(infer, "model_status", "idle")
        if model_status == "idle" and hasattr(infer, "_get_model"):
            try:
                infer._get_model()  # initialize the predictor (ready once set up)
                model_status = infer.model_status
            except Exception:
                model_status = "error"
        model_name = getattr(infer, "model_name", "")
        if model_status == "ready":
            status = f"Ready: {model_name}"
        elif model_status == "error":
            err = getattr(infer, "model_error", "")
            status = f"model error: {err}" if err else "model error"
        self.statusbar_inference.setText(f"Inference: Local ({status})")

    def update_storage_status(self):
        """Show the current storage mode and, when local, the images folder
        in the right side of the status bar."""
        is_local = self.proj.storage_mode == "local"
        if is_local:
            img_dir = None
            if self.backend is not None:
                img_dir = getattr(self.backend.storage, "image_dir", None)
            if img_dir is None:
                img_dir = Path(self.proj.local_dir) if self.proj.local_dir else self.settings.project_dir / "images"
            self.statusbar_storage.setText(f"Storage: Local | {img_dir}")
        else:
            self.statusbar_storage.setText("Storage: Remote")

    def login(self):
        # TODO: use async or worker?
        if self.backend is None:
            return
        self.login_thread = ZLoginThread(
            self.backend,
            self.settings.username,
            self.settings.password,
        )
        self.login_thread.login_success.connect(self.on_login_success)
        self.login_thread.login_fail.connect(self.on_login_failed)
        self.login_thread.finished.connect(self.login_thread.quit)
        self.login_thread.finished.connect(self.login_thread.deleteLater)

        self.login_thread.start()

    def on_login_failed(self):
        if self.dialog_processing.isVisible():
            self.dialog_processing.close()

        QMessageBox.critical(
            self,
            self.tr("Error"),
            self.tr("Login Failed, check internet or username and password"),
            QMessageBox.StandardButton.Ok,
        )
        if not self.dialog_settings.isVisible():
            self.dialog_settings.show()

    def on_login_success(self, token: str):
        self.user_token = token
        self.logger.info(f"Login success, {self.settings.username=}")
        self.load_projects()
        if self.dialog_settings.isVisible():
            self.dialog_settings.close()

        if self.dialog_processing.isVisible():
            self.dialog_processing.close()

    def load_projects(self):
        self.logger.debug("Loading projects...")
        if self.backend is None:
            return
        worker = GetProjectsWorker(
            self.backend,
            self.settings.username,
            self.settings.password,
        )
        worker.emitter.success.connect(self.on_get_projects_success)
        worker.emitter.fail.connect(self.on_get_projects_failed)
        self.threadpool.start(worker)

    def on_get_projects_success(self, projects: list[tuple[int, str]]):
        # no need to save, request everytime
        self.settings.projects = projects
        if self.settings.project_idx < 0 and len(projects) > 0:
            self.settings.project_idx = 0
        self.dockcnt_files.set_cmbox_projects([p[1] for p in projects])
        self.dockcnt_files.cmbox_project.setCurrentIndex(self.settings.project_idx)
        self.logger.debug(f"Loaded {projects=}")
        self.load_tasks()

    def on_get_projects_failed(self, msg: str):
        QMessageBox.critical(
            self,
            self.tr("Error"),
            self.tr(f"Get Projects Failed, {msg=}"),
            QMessageBox.StandardButton.Ok,
        )

    def refresh_tasks(self, tasks: list[Task]):
        """Refresh tasks from the storage backend - do not save to local disk"""
        self.proj.tasks.clear()
        for task in tasks:
            if not task.group:
                self._assign_remote_group(task)
            self.proj.add_task(task)
        self.proj.reset_task_key()

        self.logger.info(f"Refreshed {len(tasks)} tasks")

    @staticmethod
    def _assign_remote_group(task: Task):
        """Remote tasks have no directory layout: group by filename prefix
        (e.g. dishA_001.jpg -> group "dishA", day 1). Unknown layout: no group."""
        import re as _re

        m = _re.fullmatch(r"(.+?)[_\-\s]*(\d+)\.(?:png|jpe?g)", task.filename, _re.IGNORECASE)
        if m:
            task.group = m.group(1)
            task.day = int(m.group(2))

    def load_tasks(self):
        """
        Load tasks from the current storage backend
        """
        self.logger.debug(f"Loading tasks for project: {self.settings.project_name}")
        if self.backend is None:
            return
        worker = ZGetTasksWorker(
            self.backend,
            self.settings.fetch_num,
            self.settings.fetch_type.value,
            self.settings.project_id,
            self.settings.username,
            self.settings.password,
            self.settings.random_select,
        )
        worker.emitter.success.connect(self.on_get_tasks_success)
        worker.emitter.fail.connect(self.on_get_tasks_failed)
        self.threadpool.start(worker)

    def on_get_tasks_success(self, tasks: list[Task]):
        self.logger.debug(f"Loaded {len(tasks)} tasks for project: {self.settings.project_name}")
        self.refresh_tasks(tasks)

        self.dockcnt_files.set_file_list(tasks)
        self.dockcnt_files.set_row_by_txt(self.proj.key_task)

        # Update UI after tasks are loaded
        self.ui_update_settings()

    def on_get_tasks_failed(self, msg: str):
        QMessageBox.critical(
            self,
            self.tr("Error"),
            self.tr(f"Get Tasks Failed, {msg=}"),
            QMessageBox.StandardButton.Ok,
        )

    def try_set_image(self, image: Image.Image | None = None):
        if self.proj.crt_task is None or self.backend is None:
            return
        if image is None:
            img_name = self.proj.crt_task.filename
            if img_name not in self._image_cache:
                worker = ZGetImageWorker(
                    self.backend,
                    img_name,
                    self.settings.username,
                    self.settings.password,
                )
                worker.emitter.success.connect(self.cache_image)
                worker.emitter.success.connect(self.on_try_set_image_get_success)
                worker.emitter.fail.connect(self.on_get_image_fail)
                self.dialog_processing.show()
                self.threadpool.start(worker)
                self.logger.info(f"getting {img_name}")
            else:
                self.on_try_set_image_get_success(img_name, self._image_cache[img_name])
        else:
            self.on_try_set_image_get_success("", image)

    def on_try_set_image_get_success(self, name: str, image: Image.Image):
        if self.proj.crt_anno is None:
            return
        # upload and set image to speed up prediction
        # TODO: add uploaded cache and ignore if an image is already uploaded
        # self.run_preupload_img_worker(image)

        self.proj.crt_anno.original_height = image.height
        self.proj.crt_anno.original_width = image.width
        self.dockcnt_info.set_info_by_anno(self.proj.crt_anno)
        self.canvas.update_image(np.asarray(image, dtype=np.uint8))
        self.canvas.set_rgb(self.rgb_mode)
        self.dialog_processing.close()
        self.canvas.fit_view()
        self._maybe_auto_fit_dish()

    def on_get_image_fail(self, msg: str):
        self.dialog_processing.close()
        QMessageBox.warning(
            self,
            self.tr("Warning"),
            self.tr(f"Get image failed, {msg=}"),
            QMessageBox.StandardButton.Ok,
        )

    def add_result(self, result: PointResult | RectangleResult | PolygonResult, update: bool = False):
        if self.proj.crt_anno is None:
            self.logger.error(f"Current annotation is None! {self.proj.crt_task=}")
            return
        self.proj.crt_anno.add_result(result)
        self.canvas.create_item_by_result(result)
        self.dockcnt_anno.add_item(result.id)
        # self.logger.debug(f"Added result {result}")

    def add_results(self, results: list[PointResult | RectangleResult | PolygonResult], update: bool = False):
        for result in results:
            self.add_result(result, update)

    def add_result_undo_cmd(
        self,
        results: list[PointResult | RectangleResult | PolygonResult],
        mode: ResultUndoMode,
        results_old: list[PointResult | RectangleResult | PolygonResult] | None = None,
        target_anno=None,
        instances_old: dict[int, str] | None = None,
        instances_new: dict[int, str] | None = None,
    ):
        cmd = ZResultUndoCmd(
            self,
            results,
            mode,
            results_old,
            target_anno=target_anno,
            instances_old=instances_old,
            instances_new=instances_new,
        )
        self.undo_stack.push(cmd)

    def remove_result(self, id_: str, update: bool = False):
        if self.proj.crt_anno is None or id_ not in self.proj.crt_anno.results:
            self.logger.debug(f"can not remove {id_=}, current annotation is None or id not in results")
            return
        self.proj.crt_anno.remove_result(id_)
        self.canvas.remove_items_by_ids([id_])
        self.dockcnt_anno.remove_item(id_)

    def remove_results(self, ids: list[str], update: bool = False):
        for id_ in ids:
            self.remove_result(id_, update)

    def modify_result(self, result: PointResult | RectangleResult | PolygonResult, update: bool = False):
        if self.proj.crt_anno is None or result.id not in self.proj.crt_anno.results:
            return
        old = self.proj.crt_anno.results.get(result.id)
        self.logger.debug(f"{result=}")
        self.proj.crt_anno.results.update({result.id: result})
        self.canvas.set_item_state_by_result(result, update=update)
        item = self.canvas.showing_items.get(result.id, None)
        if item is not None:
            item.setFillColor(result.labels[0].color, self.settings.alpha)
        # instance regrouping (merge/split/undo) changes the annos tree
        # structure; rebuild instead of scrolling to the row (which would
        # collapse the multi-selection via the selection sync)
        if old is not None and getattr(old, "instance_id", 0) != getattr(result, "instance_id", 0):
            new_iid = getattr(result, "instance_id", 0)
            if new_iid:
                self.proj.crt_anno.instances.setdefault(new_iid, "")
            self._prune_orphan_instances()
            self._refresh_anno_tree()
            self.update_group_button_state()
        else:
            self.dockcnt_anno.set_row_by_text(result.id)

    def modify_results(
        self,
        results: list[PointResult | RectangleResult | PolygonResult] | None = None,
        update: bool = False,
    ):
        if results is None:
            return
        for r in results:
            self.modify_result(r, update)
        self._is_modifying = False

    def add_annotation(self, anno: Annotation):
        self.proj.key_task = anno.id
        self.proj.add_annotation(anno)

    def check_label_ok(self):
        if self.proj.crt_label is None:
            QMessageBox.critical(
                self,
                self.tr("Label Error"),
                self.tr("Select a label first!"),
                QMessageBox.StandardButton.Ok,
            )
            return False
        return True

    def is_current_anno_ok(self):
        if self.proj.crt_anno is None:
            self.logger.warning(f"current annotation is None, {self.proj.crt_task=}")
            return False
        return True

    def is_current_result_ok(self):
        if self.proj.crt_result is None:
            self.logger.warning("current result is None")
            return False
        return True

    def is_current_anno_result_ok(self):
        return self.is_current_anno_ok() and self.is_current_result_ok()

    def validate_project_integrity(self) -> tuple[bool, str]:
        """Validate project structure and return (is_valid, error_message)"""
        try:
            # Check if project directory exists
            if not self.settings.project_dir.exists():
                return False, f"Project directory does not exist: {self.settings.project_dir}"

            # Check if project file exists
            project_file = self.settings.project_dir / f"{self.proj.name}.json"
            if not project_file.exists():
                return False, f"Project file does not exist: {project_file}"

            # Check if annotation directory exists
            if not self.settings.project_anno_dir.exists():
                self.logger.info(f"Creating annotation directory: {self.settings.project_anno_dir}")
                self.settings.project_anno_dir.mkdir(parents=True, exist_ok=True)

            # Check if a backend is available
            if self.backend is None:
                return (
                    False,
                    "Backend is not available. Please check your connection settings.",
                )

            # Note: Tasks are loaded from remote server, so empty tasks is normal during initialization
            # Only show error if we have tasks but something else is wrong

            # Check if labels exist
            if not self.proj.labels:
                self.logger.warning("No labels defined")

            return True, "Project integrity check passed"

        except Exception as e:
            return False, f"Project integrity check failed: {str(e)}"

    def show_project_validation_error(self, error_msg: str):
        """Show project validation error to user"""
        QMessageBox.warning(self, self.tr("Project Validation Error"), error_msg, QMessageBox.StandardButton.Ok)

    def restore_annotations(self):
        # restore annotations
        if not self.settings.project_dir:
            self.logger.error("project_dir is None")
            return
        path = self.settings.project_anno_dir
        annos = list(path.glob(f"*.{self.anno_suffix}"))
        for p in annos:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    anno = Annotation.model_validate_json(f.read(), strict=True)
                self.add_annotation(anno)
            except Exception as e:
                self.logger.warning(f"validate {p=} failed with {e=}")
        self.proj.reset_task_key()

    def show_toast(self, msg: str, timeout: int = 1000):
        toast = Toast(msg, timeout=timeout, parent=self)
        toast.show()

    # endregion

    # region Slots
    def on_dialog_settings_changed(self):
        self.settings.save_json(self.settings_path)
        if self.sender() == self.dialog_settings:
            self.proj.save_json(self.settings.project_path)
        self.ui_update_settings()
        self._refresh_anno_tree()
        self.dockcnt_anno.set_instance_statuses(list(self.proj.instance_statuses))

    def on_dialog_settings_apply_clicked(self):
        self.rebuild_backend()
        if self.backend is None:
            return
        if self.backend.needs_login:
            if self.settings.host:
                self.dialog_processing.show()
                self.login()
            else:
                if self.dialog_processing.isVisible():
                    self.dialog_processing.close()
        else:
            self.load_projects()
            if self.dialog_processing.isVisible():
                self.dialog_processing.close()

    def set_loglevel(self, level: str):
        self.logger.info(f"Setting loglevel to {level}")
        self.logger.setLevel(level)
        if getattr(self, "canvas", None) is not None:
            self.canvas.logger.setLevel(level)
        if self.backend is not None:
            self.backend.logger.setLevel(level)

    # def check_login(self):
    #     if not self.login():
    #         QMessageBox.critical(
    #             self,
    #             "Error",
    #             "Login Failed, check internet or username and password",
    #             QMessageBox.StandardButton.Ok,
    #         )
    #         if not self.dialog_settings.isVisible():
    #             self.dialog_settings.show()
    #     else:
    #         self.dialog_settings.close()

    # region Slots Actions
    def on_action_chinese_triggered(self):
        self.set_language(Language.CHINESE)

    def on_action_english_triggered(self):
        self.set_language(Language.ENGLISH)

    def set_language(self, language: Language):
        assert language in [Language.ENGLISH, Language.CHINESE]
        if not self._is_initing and language.value == self.settings.language:
            return

        self.settings.language = language.value
        if self._translator is not None:
            QApplication.instance().removeTranslator(self._translator)
            self._translator = None

        if language != Language.ENGLISH:
            qm_path = Path("i18n") / f"{language.value}.qm"
            if not qm_path.exists():
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr(f"Translation file for {language.value} not found"),
                    QMessageBox.StandardButton.Ok,
                )
                return
            tr = QTranslator()
            if not tr.load(str(qm_path)):
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr(f"Failed to load translation for {language.value}"),
                    QMessageBox.StandardButton.Ok,
                )
                return
            QApplication.instance().installTranslator(tr)
            self._translator = tr
        self.retranslateUi(self)
        self.dialog_about.retranslateUi(self.dialog_about)
        self.dialog_shortcut.retranslateUi(self.dialog_shortcut)
        self.dialog_settings.retranslateUi(self.dialog_settings)
        self.dockcnt_info.retranslateUi(self.dockcnt_info)
        self.dockcnt_files.retranslateUi(self.dockcnt_files)
        self.dockcnt_labels.retranslateUi(self.dockcnt_labels)
        self.dockcnt_anno.retranslateUi(self.dockcnt_anno)
        self.ui_update_settings()
        self.settings.save_json(self.settings_path)

    def on_action_next_prev_triggered(self):
        row = self.dockcnt_files.currentRow()
        if self.sender() == self.actionNext:
            row += 1
        else:
            row -= 1
        if row < 0 or row >= self.dockcnt_files.count():
            return
        self.dockcnt_files.setCurrentRow(row)
        item = self.dockcnt_files.getItem(row)
        self.dockcnt_files.set_qlabels()
        self.on_dock_files_item_clicked(item.id_)

    def _save_current(self):
        """Save the project metadata and the current annotation."""
        self.proj.save_json(self.settings.project_path)
        if self.proj.crt_anno is None:
            return
        anno_dir = self.settings.project_anno_dir
        if self.backend is not None:
            anno_dir = self.backend.anno_dir or anno_dir
        filename = f"{anno_dir}/{self.proj.crt_anno.id}.{self.anno_suffix}"
        self.proj.crt_anno.save_json(filename)

    def _save_current_if_annotated(self):
        """Save project + annotation only when the current annotation has results."""
        if self.proj.crt_anno is not None and len(self.proj.crt_anno.results) > 0:
            self._save_current()

    def on_action_save_triggered(self):
        self._save_current()

    def on_action_undo_triggered(self):
        if self.undo_stack.canUndo():
            self.undo_stack.undo()
        self._refresh_tracks()

    def on_action_redo_triggered(self):
        if self.undo_stack.canRedo():
            self.undo_stack.redo()
        self._refresh_tracks()

    def on_action_visible_triggered(self):
        self.canvas_items_visible = self.actionVisible.isChecked()
        if self.canvas_items_visible:
            self.canvas.update_by_anno(self.proj.crt_anno)
        else:
            self.canvas.clear_all_items()

    def on_action_zoom_in_triggered(self):
        self.canvas.view_box.scaleBy((0.9, 0.9))

    def on_action_zoom_out_triggered(self):
        self.canvas.view_box.scaleBy((1.1, 1.1))

    def on_action_fit_window_triggered(self):
        self.canvas.fit_view()

    def on_action_restore_triggered(self):
        self.dock_annos.show()
        self.dock_labels.show()
        self.dock_infos.show()
        self.dock_files.show()
        self.dock_tracks.show()

    def on_action_annotations_triggered(self):
        if self.actionAnnotations.isChecked():
            self.dock_annos.show()
        else:
            self.dock_annos.hide()

    def on_action_info_triggered(self):
        if self.actionInfo.isChecked():
            self.dock_infos.show()
        else:
            self.dock_infos.hide()

    def on_action_files_triggered(self):
        if self.actionFiles.isChecked():
            self.dock_files.show()
        else:
            self.dock_files.hide()

    def on_action_labels_triggered(self):
        if self.actionLabels.isChecked():
            self.dock_labels.show()
        else:
            self.dock_labels.hide()

    def on_action_tracks_triggered(self):
        if self.actionTracks.isChecked():
            self.dock_tracks.show()
        else:
            self.dock_tracks.hide()

    def on_dock_tracks_visibility_changed(self, visible: bool):
        self.actionTracks.setChecked(visible)

    def _on_tracks_group_changed(self, group: str):
        """Append the current sequence group to the Tracks dock title."""
        title = self.tr("Tracks")
        if group:
            title += f" · {group}"
        self.dock_tracks.setWindowTitle(title)

    def _refresh_tracks(self):
        """Rebuild the instance timeline for the current frame's sequence group."""
        task = self.proj.crt_task
        group = task.group if task else ""
        tasks = [t for t in self.proj.tasks.values() if t.group == group] if group else []
        self.dockcnt_tracks.set_group(self.proj, group, tasks)

    def on_instance_open(self, anno_id: str, instance_id: int):
        """Jump to the frame containing ``instance_id`` and select its members."""
        if self.proj.crt_anno is not None and self.proj.crt_anno.id == anno_id:
            self._select_instance(instance_id)
            return
        # avoid the auto copy-prev dialog when jumping via the timeline
        self._skip_copy_anno = anno_id
        self.on_dock_files_item_clicked(anno_id)
        self._select_instance(instance_id)

    def _select_instance(self, instance_id: int):
        anno = self.proj.crt_anno
        if anno is None:
            return
        ids = [r.id for r in anno.results.values() if getattr(r, "instance_id", 0) == instance_id]
        if ids:
            self.canvas.select_items(ids)
            self.dockcnt_anno.set_selected_ids(ids)

    def _anno_by_id(self, anno_id: str) -> Annotation | None:
        """The annotation for ``anno_id`` (current frame first, else from disk)."""
        if self.proj.crt_anno is not None and self.proj.crt_anno.id == anno_id:
            return self.proj.crt_anno
        for task in self._group_tasks():
            if task.anno_id == anno_id:
                return self._load_anno_for_task(task)
        return None

    def on_cell_moved(self, src_anno_id: str, src_iid: int, target_row: int):
        """Drag on the instance timeline: renumber or swap the source instance
        within its own frame. Only the target row matters (drop column ignored):
        if the target row is empty in the source frame the instance id becomes
        that row number, otherwise the two instances swap ids/statuses."""
        if src_iid <= 0 or src_iid == target_row:
            return
        anno = self._anno_by_id(src_anno_id)
        if anno is None:
            return
        affected = [r for r in anno.results.values() if getattr(r, "instance_id", 0) in (src_iid, target_row)]
        if not any(getattr(r, "instance_id", 0) == src_iid for r in affected):
            return
        occupied = (
            target_row in {getattr(r, "instance_id", 0) for r in anno.results.values()} or target_row in anno.instances
        )

        result_old = [copy.deepcopy(r) for r in affected]
        result_new = [copy.deepcopy(r) for r in affected]
        inst_old = dict(anno.instances)
        inst_new = dict(inst_old)
        if occupied:
            for r in result_new:
                r.instance_id = target_row if r.instance_id == src_iid else src_iid
            old_src = inst_new.pop(src_iid, None)
            old_tgt = inst_new.pop(target_row, None)
            if old_src is not None:
                inst_new[target_row] = old_src
            if old_tgt is not None:
                inst_new[src_iid] = old_tgt
        else:
            for r in result_new:
                if r.instance_id == src_iid:
                    r.instance_id = target_row
            if src_iid in inst_new:
                inst_new[target_row] = inst_new.pop(src_iid)
        self.add_result_undo_cmd(
            result_new,
            ResultUndoMode.MODIFY_NO_UPDATE,
            result_old,
            target_anno=anno,
            instances_old=inst_old,
            instances_new=inst_new,
        )
        self.show_toast(self.tr(f"Instance {src_iid} → {target_row}" + (" (swap)" if occupied else "")))

    def on_action_finish_triggered(self):
        if self.proj.crt_task is None or self.proj.crt_anno is None or self.backend is None:
            return
        self._save_current()

        # if triggered by click, set task finished and upload to remote storage
        if self.sender() == self.actionFinish:
            self.proj.crt_task.finished = True
            self.dockcnt_files.set_item_finished(self.proj.crt_task)
            # In local-storage mode the annotation is already saved locally;
            # only upload when the storage backend is remote.
            if self.backend is not None and self.backend.needs_login:
                anno_dir = self.backend.anno_dir or self.settings.project_anno_dir
                filename = f"{anno_dir}/{self.proj.crt_anno.id}.{self.anno_suffix}"
                worker_upload = ZUploadFileWorker(
                    self.backend,
                    filename,
                    self.settings.username,
                    self.settings.password,
                )
                worker_upload.emitter.fail.connect(self.show_toast)
                worker_upload.emitter.success.connect(self.show_toast)
                self.threadpool.start(worker_upload)

    def on_action_cancel_triggered(self):
        confirm = QMessageBox.question(
            self,
            self.tr("Confirm"),
            self.tr("Are you sure to cancel the current annotation?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.No:
            return
        self.canvas.clear_all_items()
        self.dockcnt_anno.listWidget.clear()
        self.dockcnt_anno.listWidget.setCurrentItem(None)
        self.dockcnt_info.set_info_by_anno(None)
        if self.proj.crt_anno:
            self.proj.crt_anno.reset_results()
        if self.proj.crt_task:
            self.proj.crt_task.finished = False
            self.dockcnt_files.set_item_unfinished(self.proj.crt_task)

    def on_action_SAM_triggered(self):
        self.settings.sam_enabled = self.actionSAM.isChecked()
        self.settings.save_json(self.settings_path)
        msg = []
        if self.settings.sam_enabled:
            msg.append("SAM")
        if self.settings.cv_enabled:
            msg.append("OpenCV")
        if msg:
            self.show_toast("+".join(msg))

    def on_action_opencv_triggered(self):
        self.settings.cv_enabled = self.actionOpenCV.isChecked()
        self.settings.save_json(self.settings_path)
        msg = []
        if self.settings.sam_enabled:
            msg.append("SAM")
        if self.settings.cv_enabled:
            msg.append("OpenCV")
        if msg:
            self.show_toast("+".join(msg))

    def _set_edit_action_enabled(self, active):
        """Enable the active edit action and disable the others. In KeyPoint
        mode, Rectangle and Polygon stay disabled regardless of what is active."""
        is_keypoint = self.settings.annotation_type == AnnotationType.POINT
        for action in self.action_group_edit:
            if is_keypoint and action in (self.actionRectangle, self.actionPolygon):
                action.setEnabled(False)
            else:
                action.setEnabled(action != active)

    def on_action_move_triggered(self):
        self._set_edit_action_enabled(self.actionMove)
        self.canvas.set_status_mode(StatusMode.VIEW)
        self.show_toast(self.tr("Move Mode"))

    def on_action_edit_triggered(self):
        self._set_edit_action_enabled(self.actionEdit)
        self.canvas.set_status_mode(StatusMode.EDIT)
        self.show_toast(msg=self.tr("Edit Mode"))

    def on_action_rectangle_triggered(self):
        self._set_edit_action_enabled(self.actionRectangle)
        self.canvas.set_status_mode(StatusMode.CREATE)
        self.canvas.set_draw_mode(DrawMode.RECTANGLE)
        self.show_toast(self.tr("Draw Rectangle"))

    def on_action_point_triggered(self):
        self._set_edit_action_enabled(self.actionPoint)
        self.canvas.set_status_mode(StatusMode.CREATE)
        self.canvas.set_draw_mode(DrawMode.POINT)
        self.show_toast(self.tr("Draw KeyPoint"))

    def on_action_polygon_triggered(self):
        self._set_edit_action_enabled(self.actionPolygon)
        self.canvas.set_status_mode(StatusMode.CREATE)
        self.canvas.set_draw_mode(DrawMode.POLYGON)
        self.show_toast(self.tr("Draw Polygon"))

    def on_action_merge_triggered(self):
        # In KeyPoint mode the merge tool groups selected keypoints into an instance.
        pts = self._selected_point_results()
        if pts:
            self.on_group_points()
            return
        self.canvas.merge_items(self.canvas.selected_items)

    def on_action_import_task_triggered(self):
        file_path = QFileDialog.getOpenFileName(
            self,
            self.tr("Import Task"),
            ".",
            "JSON Files (*.json)",
        )[0]
        if not file_path:
            return
        self.logger.debug(f"import task from {file_path}")
        proj = Project.model_validate_json(Path(file_path).read_text(), strict=True)
        names = [n for _, n in self.settings.projects]
        if proj.name not in names:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr(f"project {proj.name} not found in settings, please refresh projects first!"),
            )
            return
        self.settings.project_idx = names.index(proj.name)
        self.settings.project = proj
        self.settings.save_json(self.settings_path)
        self.proj.save_json(self.settings.project_path)
        self.ui_update_settings()
        self.logger.debug(f"imported project {self.settings.project_name}")

    def on_action_export_triggered(self):
        get_image = None
        if self.backend is not None:
            get_image = self.backend.get_image
        dialog = DialogExport(project=self.proj, get_image=get_image, parent=self)
        dialog.show()

    def on_cmbox_annotype_index_changed(self, index: int):
        if index < 0 or index >= len(self.annotation_types):
            return
        self.settings.annotation_type = AnnotationType(index)
        self.settings.save_json(self.settings_path)
        self.update_anno_type_actions()

    def update_anno_type_actions(self):
        """KeyPoint mode disables Rectangle/Polygon/Merge and drops into Move
        (preview) mode; Move is shown as the active mode, the user clicks Point
        to start drawing keypoints."""
        is_keypoint = self.settings.annotation_type == AnnotationType.POINT
        self.actionRectangle.setEnabled(not is_keypoint)
        self.actionPolygon.setEnabled(not is_keypoint)
        # keypoint visibility shortcuts (L/O/X) are only meaningful - and only
        # free of shortcut collisions - while KeyPoint mode is active
        for sc in self._point_visible_shortcuts:
            sc.setEnabled(is_keypoint)
        # merge is always enabled: in KeyPoint mode it groups keypoints into instances
        if is_keypoint:
            self.canvas.set_status_mode(StatusMode.VIEW)
            self._set_edit_action_enabled(self.actionMove)
        else:
            for action in self.action_group_edit:
                action.setEnabled(True)
            # drop any leftover point-drawing state from KeyPoint mode
            if self.canvas._status_mode == StatusMode.CREATE and self.canvas._draw_mode == DrawMode.POINT:
                self.canvas.set_status_mode(StatusMode.VIEW)

    def on_cmbox_rgb_index_changed(self, index: int):
        if index < 0 or index >= len(self.rgb_channels):
            return
        rgb_mode = self.rgb_channels[index][0]
        if rgb_mode == "R":
            self.rgb_mode = RgbMode.R
        elif rgb_mode == "G":
            self.rgb_mode = RgbMode.G
        elif rgb_mode == "B":
            self.rgb_mode = RgbMode.B
        elif rgb_mode == "RGB":
            self.rgb_mode = RgbMode.RGB
        elif rgb_mode == "Gray":
            self.rgb_mode = RgbMode.GRAY
        else:
            self.logger.error(f"{rgb_mode=} not implemented")

        self.canvas.set_rgb(self.rgb_mode)

    def on_slider_threshold_changed(self, v: int):
        self.threshold = v

    # endregion

    # region DockLabel
    def on_dock_label_visibility_changed(self, visible: bool):
        self.actionLabels.setChecked(visible)

    def on_dock_label_listw_item_clicked(self, id: str):
        if self.is_current_anno_ok():
            self.proj.key_label = id
            self.logger.debug(f"Select label {self.proj.crt_label}")
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    def on_shortcut_select_label_number(self, number: int):
        if number < 1 or number > 9:
            return
        count = self.dockcnt_labels.listw_labels.count()
        idx = number - 1
        if idx < 0 or idx >= count:
            return
        self.dockcnt_labels.select_row(idx)
        try:
            label = list(self.proj.labels.values())[idx]
            self.show_toast(self.tr(f"Select [{label.name}]"), timeout=1500)
        except Exception as e:
            self.logger.error(e)

    def on_dock_label_item_color_changed(self, id_: str, color: str):
        self.proj.labels[id_].color = color
        if id_ == self.proj.key_label:
            self.canvas.set_color(color, self.settings.alpha)
        self.logger.debug(f"Labels color changed: {self.proj.labels[id_]=}")
        self.proj.save_json(self.settings.project_path)

    def on_label_visibility_toggled(self, id_: str):
        anno = self.proj.crt_anno
        if anno is None:
            return
        items = [
            item
            for rid, item in self.canvas.showing_items.items()
            if anno.results.get(rid) and anno.results[rid].labels and anno.results[rid].labels[0].id == id_
        ]
        if not items:
            return
        new_visible = not any(item.isVisible() for item in items)
        self._label_visibility[id_] = new_visible
        for item in items:
            item.setVisible(new_visible)
        self.update_label_visibility_buttons()

    def update_label_visibility_buttons(self):
        """Sync the eye buttons in the labels dock with the stored visibility."""
        for row in range(self.dockcnt_labels.listw_labels.count()):
            item = self.dockcnt_labels.listw_labels.item(row)
            if item is None:
                continue
            widget = self.dockcnt_labels.listw_labels.itemWidget(item)
            if hasattr(widget, "set_visible_state"):
                widget.set_visible_state(self._label_visibility.get(widget.id_, True))

    def apply_label_visibility(self):
        """Apply stored per-label visibility to the current canvas items."""
        anno = self.proj.crt_anno
        if anno is None:
            return
        for rid, item in self.canvas.showing_items.items():
            r = anno.results.get(rid)
            if r and r.labels:
                visible = self._label_visibility.get(r.labels[0].id, True)
                item.setVisible(visible)
                if not visible:
                    item.setSelected(False)

    def on_dock_label_item_double_clicked(self, id_: str):
        if not self.proj.crt_anno:
            return
        label = self.proj.labels.get(id_, None)
        if label is None:
            self.logger.debug(f"Label {id_} not found in {self.proj.labels.keys()}")
            return
        items = self.canvas.selected_items
        if len(items) == 0:
            self.logger.debug("No item selected")
            return
        # prevent canvas state changed signal
        self._is_modifying = True

        result_old: list[PointResult | RectangleResult | PolygonResult] = []
        result_new: list[PointResult | RectangleResult | PolygonResult] = []
        for item in items:
            result = self.proj.crt_anno.results.get(item.id_, None)
            if result is None:
                self.logger.warning(f"Result {item.id_} not found in {self.proj.crt_anno.results.keys()}")
                continue
            result_old.append(copy.deepcopy(result))
            r_new = copy.deepcopy(result)
            r_new.labels = [label]
            result_new.append(r_new)
        self.add_result_undo_cmd(result_new, ResultUndoMode.MODIFY, result_old)

    # endregion

    # region DockInfo
    # DockInfo #####
    def on_dock_info_visibility_changed(self, visible: bool):
        self.actionInfo.setChecked(visible)

    def on_dock_info_ledit_note_changed(self, s: str):
        if self.proj.crt_anno:
            self.proj.crt_anno.note = s

    # endregion

    # region DockAnnotation
    # DockAnnotation #####
    def on_dock_anno_visibility_changed(self, visible: bool):
        self.actionAnnotations.setChecked(visible)

    def on_dock_anno_listw_item_clicked(self, item, column: int = 0):
        rid = item.data(0, ID_ROLE) if hasattr(item, "data") else getattr(item, "id_", None)
        if not rid:
            # instance branch clicked: use its first member as the current result
            for i in range(item.childCount()):
                child = item.child(i)
                if child.data(0, ID_ROLE):
                    rid = child.data(0, ID_ROLE)
                    break
        if not rid:
            return
        if self.proj.crt_anno and rid in self.proj.crt_anno.results:
            self.proj.crt_anno.key_result = rid
            if self.proj.crt_result and self.proj.crt_result.labels:
                self.proj.key_label = self.proj.crt_result.labels[0].id
                self.dockcnt_labels.select_row_by_id(self.proj.key_label)
            self.dockcnt_info.set_info_by_result(self.proj.crt_anno, self.proj.crt_result)
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    def on_dock_anno_item_deleted(self, ids: list[str]):
        if self.proj.crt_anno:
            results = [self.proj.crt_anno.results[id_] for id_ in ids]
            self.add_result_undo_cmd(results, ResultUndoMode.REMOVE)
            self._prune_orphan_instances()
            self._refresh_anno_tree()
            self.update_group_button_state()
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    def on_dock_anno_item_count_changed(self, count: int):
        self.dock_annos.setWindowTitle(self.tr(f"Annos ({count} items)"))

    # endregion

    # region DockFiles
    # DockFiles #####
    def on_dock_files_visibility_changed(self, visible: bool):
        self.actionFiles.setChecked(visible)

    def on_dock_files_item_clicked(self, task_id: str):
        # save first (only when the current annotation is not empty)
        self._save_current_if_annotated()

        # set current annotation id to newly clicked
        self.proj.key_task = task_id
        if self.proj.crt_task is None:
            self.logger.warning(f"Current task is None, {self.proj.tasks=}")
            return
        if self.backend is None:
            self.logger.warning(f"ApiPredict is None, {self.backend=}")
            return

        # if the current anno is None:
        # 1. try to fetch from remote
        # 2. if not existed in remote, create
        if self.proj.crt_anno is None:
            task = self.proj.tasks[task_id]
            try:
                name = f"{task.anno_id}.{self.anno_suffix}"
                anno_json = self.backend.get_zlabel(name=name)
                if anno_json is None:
                    raise Exception(f"Response of {name} is None")
                anno = Annotation.model_validate_json(anno_json, strict=True)
                anno.group = task.group
                anno.day = task.day
                self.add_annotation(anno)
                self.logger.info(f"Got anno from remote, added {name}")
            except Exception as e:
                for name in task.labels:
                    label = Label(id=id_uuid4(), name=name, color=self.settings.default_color)
                    self.proj.labels[label.id] = label
                img = self._image_cache.get(task.filename, None)
                self.add_annotation(
                    Annotation(
                        image_path=task.filename,
                        original_height=img.height if img else 0,
                        original_width=img.width if img else 0,
                        created_by=self.user,
                        updated_by=self.user,
                        id=task.anno_id,
                        group=task.group,
                        day=task.day,
                    )
                )
                self.logger.warning(f"{task.anno_id=} not found in remote, created, {e=}")

        # apply view rotation before setting the image so the fit view (incl. the
        # cached-image path) uses this frame's rotation
        self._apply_annotation_rotation()
        self.try_set_image()

        # update ui
        # ^ hereafter, self.proj.crt_anno won't be None
        self.dockcnt_anno.set_instance_statuses(list(self.proj.instance_statuses))
        self._refresh_anno_tree()
        self.dockcnt_anno.set_row_by_text(self.proj.key_result)
        self.dockcnt_anno.set_title()
        self.dockcnt_labels.set_labels(list(self.proj.labels.values()), self.proj.key_label)
        self.update_label_visibility_buttons()
        # self.dockcnt_labels.set_color(self.settings.default_color)

        # clear items in canvas
        if self.canvas_items_visible:
            self.canvas.update_by_anno(self.proj.crt_anno)
            self.apply_label_visibility()
        self.current_instance_id = 0
        self._refresh_anno_tree()
        self._apply_annotation_rotation()
        self._refresh_tracks()
        self._maybe_copy_prev_frame()

    def _apply_annotation_rotation(self):
        angle = self.proj.crt_anno.image_rotation if self.proj.crt_anno else 0
        self.spin_rotation.setValue(angle)
        self.canvas.set_rotation(angle)

    def on_dock_files_fetch_tasks(self, project_idx: int, num: int, finished: int):
        if self.settings.project_idx != project_idx:
            # project_name resolves from project_idx, so update the index first,
            # then load the new project and rebuild the backend from it.
            self.settings.project_idx = project_idx
            self.settings.reload_project()
            self.rebuild_backend()
        self.settings.project_idx = project_idx
        self.settings.project.name = self.settings.project_name
        self.settings.fetch_num = num
        self.settings.fetch_type = FetchType(finished)
        self.settings.save_json(self.settings_path)
        self.load_tasks()

    def on_project_changed(self, idx: int):
        """Switch to another project (from the Project tab)."""
        if self.settings.project_idx != idx:
            self.settings.project_idx = idx
            self.settings.reload_project()
            self.rebuild_backend()
        self.dockcnt_files.cmbox_project.setCurrentIndex(self.settings.project_idx)
        self.settings.save_json(self.settings_path)
        self.load_tasks()
        self.dialog_settings.load_settings(self.settings)

    def on_dock_files_storage_changed(self, storage_mode: str):
        """Switch the current project's storage backend (local vs remote)."""
        if self.settings.project.storage_mode == storage_mode:
            return
        self.settings.project.storage_mode = storage_mode
        self.settings.project.save_json(self.settings.project_path)
        self.rebuild_backend()
        self.update_storage_status()
        if self.backend is None:
            return
        if self.backend.needs_login:
            if self.settings.host:
                self.login()
        else:
            self.load_projects()

    def on_dock_files_local_dir_changed(self, local_dir: str):
        """Set the current project's local images folder."""
        if self.settings.project.local_dir == local_dir:
            return
        self.settings.project.local_dir = local_dir
        self.settings.project.save_json(self.settings.project_path)
        self.rebuild_backend()
        self.update_storage_status()
        if self.backend is not None:
            self.load_tasks()

    def rebuild_backend(self):
        self.backend = build_backend(self.settings)

    # endregion

    # region Canvas
    def run_sam_api_worker(self, worker: ZSamPredictWorker):
        worker.emitter.sigFinished.connect(self.on_sam_worker_finished)
        self.threadpool.start(worker)

    def on_sam_worker_finished(self, worker_results: list[SamWorkerResult]):
        self.update_inference_status()
        if len(worker_results) == 0:
            return
        instance_id = self._ensure_current_instance()
        dish_candidates: list[PolygonResult] = []
        kept: list[SamWorkerResult] = []
        for wr in worker_results:
            if isinstance(wr.result, PolygonResult):
                wr.result.instance_id = instance_id
                if wr.result.labels and wr.result.labels[0].name.lower() in ("dish", "培养皿"):
                    dish_candidates.append(wr.result)
                else:
                    kept.append(wr)
            else:
                kept.append(wr)
        if dish_candidates:
            best = self._select_best_dish(dish_candidates)
            if best is not None:
                self._maybe_fit_dish_ellipse(best)
                kept.append(next(wr for wr in worker_results if wr.result is best))
        results = [wr.result for wr in kept]
        self.proj.key_task = worker_results[0].anno_id
        # self.add_results(results)
        self.add_result_undo_cmd(results, ResultUndoMode.ADD)
        self._refresh_anno_tree()
        self._refresh_tracks()

    @staticmethod
    def _select_best_dish(candidates: list[PolygonResult]) -> PolygonResult | None:
        """Keep the mask that is largest and most circular (dish-like).

        Ranking favours roundness first (a dish is an ellipse), then area.
        """
        from zlabel.utils.geometry import circularity, polygon_area

        if not candidates:
            return None
        return max(candidates, key=lambda r: (round(circularity(r.points), 2), polygon_area(r.points)))

    def _maybe_fit_dish_ellipse(self, result: PolygonResult):
        """Fit an ellipse polygon when the SAM result is a dish."""
        if not result.labels or result.labels[0].name.lower() not in ("dish", "培养皿"):
            return
        from zlabel.utils.geometry import fit_ellipse_polygon

        pts = fit_ellipse_polygon(result.points)
        if pts:
            result.points = pts

    def on_canvas_point_created(self, item_state: dict[str, Any] | None):
        if item_state is None:
            return
        if self.current_image is None:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Please select an image first!"),
                QMessageBox.StandardButton.Ok,
            )
            return
        if self.proj.crt_label is None or self.proj.crt_task is None:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Please select a label and a task first!"),
                QMessageBox.StandardButton.Ok,
            )
            return

        pos = item_state["pos"]

        # Direct keypoint annotation: save the click as a PointResult.
        if self.settings.annotation_type == AnnotationType.POINT:
            if not (self.proj.crt_anno and self.proj.crt_anno.image_path):
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Please select a task first!"),
                    QMessageBox.StandardButton.Ok,
                )
                return
            result = PointResult.new(
                id_=item_state.get("id"),
                labels=[self.proj.crt_label],
                x=pos.x(),
                y=pos.y(),
                visible=KeypointVisible.VISIBLE,
                category_id=self._label_category_id(self.proj.crt_label),
                instance_id=self._ensure_current_instance(),
            )
            self.add_result_undo_cmd([result], ResultUndoMode.ADD)
            self._refresh_anno_tree()
            self._refresh_tracks()
            return

        # Legacy SAM/CV prompt path
        match self.auto_mode:
            case AutoMode.SAM | AutoMode.CV:
                ...
            case _:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("With point, you have to select SAM or CV"),
                    QMessageBox.StandardButton.Ok,
                )
                return
        # TODO: if image already uploaded, ignore uploading image with points
        if not (self.proj.crt_anno and self.proj.crt_anno.image_path):
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Please select a task first!"),
                QMessageBox.StandardButton.Ok,
            )
            return
        if self.backend is None:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("ApiPredict is None, please login first!"),
                QMessageBox.StandardButton.Ok,
            )
            return
        worker = ZSamPredictWorker(
            api=self.backend,
            anno_id=self.proj.crt_task.anno_id,
            image=self.proj.crt_anno.image_path,
            points=[(pos.x(), pos.y())],
            labels=[1.0],
            threshold=self.threshold,
            mode=self.auto_mode,
            result_labels=[self.proj.crt_label],
            # anno_type=0 => RECT, 1 => POLYGON
            return_type=1 if self.settings.annotation_type == 0 else 2,
        )
        self.run_sam_api_worker(worker)

    def _label_category_id(self, label: Label) -> int:
        for i, lab in enumerate(self.proj.labels.values()):
            if lab.id == label.id:
                return i
        return 0

    def on_canvas_rectangle_created(self, item_state: dict[str, Any] | None):
        if item_state is None or self.proj.key_task is None or self.current_image is None:
            self.logger.warning(f"Wrong {item_state=} or {self.proj.key_task=} or current_image")
            return
        # self.logger.debug(f"Rectangle Created: {item_state=}")
        if not self.proj.crt_label:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Select a label first!"),
                QMessageBox.StandardButton.Ok,
            )
            return

        # In SAM/CV mode the drawn rect is only a *prompt* (never saved), so it
        # must not consume an instance id; the real instances are allocated for
        # the predicted results in on_sam_worker_finished.
        instance_id = self._ensure_current_instance() if self.auto_mode == AutoMode.MANUAL else 0
        result = RectangleResult.new(
            id_=item_state["id"],
            type_id=ResultType.RECTANGLE,
            x=item_state["pos"].x(),
            y=item_state["pos"].y(),
            w=item_state["size"].x(),
            h=item_state["size"].y(),
            rotation=item_state["angle"],
            labels=[self.proj.crt_label],
            score=1.0,
            instance_id=instance_id,
        )
        # self.logger.debug(f"{result=}")
        match self.auto_mode:
            # if neither SAM nor CV selected, means create rect manually
            case AutoMode.MANUAL:
                self.add_result_undo_cmd([result], ResultUndoMode.ADD)
                self._maybe_ocr_rect(result)
                self._refresh_tracks()
                return
            # if either sam or CV selected, create by predict
            case AutoMode.SAM | AutoMode.CV:
                ...
            case x if x == AutoMode.SAM & AutoMode.CV:
                ...
            case _:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("AutoMode error"),
                    QMessageBox.StandardButton.Ok,
                )
                return

        if not (self.proj.crt_anno and self.proj.crt_anno.image_path):
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Please select a task first!"),
                QMessageBox.StandardButton.Ok,
            )
            return
        if self.backend is None:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("ApiPredict is None, please login first!"),
                QMessageBox.StandardButton.Ok,
            )
            return
        # The drawn box may be rotated in image space (view rotation): the
        # prompt must be the axis-aligned bounding box of the rotated rect,
        # otherwise the coordinates sent to the backend are displaced.
        left, top, right, bottom = self._crop_box(result)
        worker = ZSamPredictWorker(
            api=self.backend,
            anno_id=self.proj.key_task,
            image=self.proj.crt_anno.image_path,
            rects=[(left, top, right - left, bottom - top)],
            threshold=self.threshold,
            mode=self.auto_mode,
            result_labels=[self.proj.crt_label],
            # anno_type=0 => RECT, 1 => POLYGON
            return_type=1 if self.settings.annotation_type == 0 else 2,
        )
        self.run_sam_api_worker(worker)

    def on_canvas_polygon_created(self, item_state: dict[str, Any] | None):
        if item_state is None or self.proj.key_task is None or self.current_image is None:
            self.logger.warning(f"Wrong {item_state=} or {self.proj.key_task=} or current_image")
            return
        # self.logger.debug(f"Polygon Created: {item_state=}")
        if not self.proj.crt_label:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("Select a label first!"),
                QMessageBox.StandardButton.Ok,
            )
            return

        instance_id = self._ensure_current_instance()

        result = PolygonResult.new(
            id_=item_state["id"],
            type_id=ResultType.POLYGON,
            x=item_state["pos"].x(),
            y=item_state["pos"].y(),
            w=item_state["size"].x(),
            h=item_state["size"].y(),
            rotation=item_state["angle"],
            points=[(p.x(), p.y()) for p in item_state["points"]],
            closed=item_state["closed"],
            labels=[self.proj.crt_label],
            score=1.0,
            instance_id=instance_id,
        )
        # self.logger.debug(f"{result=}")
        self.add_result_undo_cmd([result], ResultUndoMode.ADD)
        self._refresh_anno_tree()
        self._refresh_tracks()

    def on_canvas_item_clicked(self, id_: str):
        if self.proj.crt_anno is None:
            return
        self.proj.key_result = id_
        # guard: set_row_by_text would trigger the annos selection sync and
        # collapse a multi-selection; the full selection is mirrored below
        self._syncing_selection = True
        try:
            self.dockcnt_anno.set_row_by_text(id_)
        finally:
            self._syncing_selection = False
        if self.proj.crt_result and self.proj.crt_result.labels:
            self.dockcnt_labels.select_row_by_id(self.proj.crt_result.labels[0].id)
        self.dockcnt_info.set_info_by_result(self.proj.crt_anno, self.proj.crt_result)
        iid = getattr(self.proj.crt_result, "instance_id", 0)
        if iid:
            self.current_instance_id = iid
        self._sync_annos_selection()
        self.update_group_button_state()

    def on_toggle_point_visible(self, visible: int):
        """Toggle the COCO visibility of the currently selected PointResult."""
        if self.proj.crt_anno is None or self.proj.crt_result is None:
            return
        if not isinstance(self.proj.crt_result, PointResult):
            return
        if self.proj.crt_result.visible == visible:
            return
        result_old = copy.deepcopy(self.proj.crt_result)
        result_new = copy.deepcopy(self.proj.crt_result)
        result_new.visible = visible
        self.add_result_undo_cmd([result_new], ResultUndoMode.MODIFY_NO_UPDATE, [result_old])
        self.show_toast(self.tr(f"Keypoint: {KeypointVisible(visible).name}"))
        self.dockcnt_info.set_info_by_result(self.proj.crt_anno, result_new)

    def _selected_point_results(self) -> list[PointResult]:
        """PointResults of the currently selected canvas items."""
        results: list[PointResult] = []
        if self.proj.crt_anno is None:
            return results
        for item in self.canvas.selected_items:
            r = self.proj.crt_anno.results.get(item.id_, None)
            if isinstance(r, PointResult):
                results.append(r)
        return results

    def on_group_points(self):
        """Assign the same instance_id to all selected keypoints."""
        pts = self._selected_point_results()
        if not pts:
            return
        instance_id = pts[0].instance_id or self._ensure_current_instance()
        result_old = [copy.deepcopy(p) for p in pts]
        result_new = [copy.deepcopy(p) for p in pts]
        for r in result_new:
            r.instance_id = instance_id
        self.add_result_undo_cmd(result_new, ResultUndoMode.MODIFY_NO_UPDATE, result_old)
        self._refresh_anno_tree()
        self.show_toast(self.tr(f"Grouped {len(pts)} keypoints"))

    def _new_individual_instances(self, results: list[PointResult | RectangleResult | PolygonResult]):
        """Deep-copy results, each assigned its own fresh, distinct instance id.

        Returns ``(result_new, inherited)`` where ``inherited`` maps each new
        instance id to the germination status of the result's original instance
        (falling back to the configured default status). Callers must apply the
        map to ``anno.instances`` *after* pushing the undo command, because the
        per-result redo pruning recreates instance entries empty.
        """
        anno = self.proj.crt_anno
        result_new = [copy.deepcopy(r) for r in results]
        inherited: dict[int, str] = {}
        used = self._used_instance_ids()
        for r in result_new:
            old_iid = r.instance_id
            iid = self._next_free_instance_id(used)
            used.add(iid)
            r.instance_id = iid
            if anno is not None:
                inherited[iid] = anno.instances.get(old_iid, "") or self._default_instance_status()
        return result_new, inherited

    def on_ungroup_points(self):
        """Split each selected keypoint into its own independent instance (U),
        inheriting the original group's status."""
        pts = self._selected_point_results()
        if not pts:
            return
        anno = self.proj.crt_anno
        result_old = [copy.deepcopy(p) for p in pts]
        result_new, inherited = self._new_individual_instances(pts)
        self.add_result_undo_cmd(result_new, ResultUndoMode.MODIFY_NO_UPDATE, result_old)
        if anno is not None:
            for iid, status in inherited.items():
                anno.instances[iid] = status
        self._refresh_anno_tree()
        self.show_toast(self.tr(f"Split {len(pts)} keypoints into individual instances"))

    def on_anno_context_menu(self, pos):
        menu = QMenu(self)
        item = self.dockcnt_anno.listWidget.itemAt(pos)
        target_id = item.data(0, ID_ROLE) if item is not None else None
        anno = self.proj.crt_anno
        if anno is not None and target_id and target_id in anno.results:
            sub = menu.addMenu(self.tr("Assign to instance"))
            for iid in sorted(anno.instances):
                sub.addAction(
                    self.tr(f"instance {iid}"),
                    functools.partial(self.on_assign_instance, target_id, iid),
                )
            sub.addSeparator()
            sub.addAction(
                self.tr("New instance..."),
                functools.partial(self.on_assign_instance, target_id, 0),
            )
        act_merge = menu.addAction(self.tr("Merge to instance (Ctrl+G)"))
        act_split = menu.addAction(self.tr("Split from instance (Ctrl+G)"))
        selected = menu.exec(self.dockcnt_anno.listWidget.mapToGlobal(pos))
        if selected == act_merge:
            self.on_group_instances()
        elif selected == act_split:
            self.on_split_instances()

    def on_assign_instance(self, result_id: str, instance_id: int):
        """Move an annotation to a different instance (or a new one)."""
        anno = self.proj.crt_anno
        if anno is None or result_id not in anno.results:
            return
        if instance_id == 0:
            instance_id = self._new_instance_id()
        result = anno.results[result_id]
        if getattr(result, "instance_id", 0) == instance_id:
            return
        if instance_id not in anno.instances:
            self._init_instance_status(instance_id)
        result_old = copy.deepcopy(result)
        result_new = copy.deepcopy(result)
        result_new.instance_id = instance_id
        self.add_result_undo_cmd([result_new], ResultUndoMode.MODIFY_NO_UPDATE, [result_old])
        self.current_instance_id = instance_id
        self._prune_orphan_instances()
        self._refresh_tracks()
        self._refresh_anno_tree()
        self.update_group_button_state()
        item = self.canvas.showing_items.get(result_id)
        if item is not None:
            color = result_new.labels[0].color if result_new.labels else None
            item.set_instance_label(instance_id, color)

    def on_canvas_item_state_changed(self, state: dict[str, Any]):
        if self.proj.crt_result is None or self._is_modifying:
            return
        result: RectangleResult | PolygonResult = copy.deepcopy(self.proj.crt_result)
        result.x = state["pos"][0]
        result.y = state["pos"][1]
        result.w = state["size"][0]
        result.h = state["size"][1]
        result.rotation = state["angle"]
        if isinstance(result, PolygonResult):
            result.closed = state["closed"]
            # Always convert live state points (pg.Point) to plain tuples to avoid
            # shared references between items and ensure consistent data in Result
            result.points = list(state["points"])
        # self.add_result_undo_cmd([result], ResultUndoMode.MODIFY)

        self.dockcnt_anno.set_row_by_text(result.id)
        # self.logger.debug(self.current_result)

    def on_canvas_item_state_change_finished(self, state: dict[str, Any]):
        if self.proj.crt_anno is None or self._is_modifying:
            return
        assert "id" in state and state["id"] in self.proj.crt_anno.results, f"state={state}"
        result: PointResult | RectangleResult | PolygonResult = copy.deepcopy(self.proj.crt_anno.results[state["id"]])
        result_old: PointResult | RectangleResult | PolygonResult = copy.deepcopy(
            self.proj.crt_anno.results[state["id"]]
        )
        if isinstance(result, PointResult):
            result.x = state["pos"][0]
            result.y = state["pos"][1]
            result.visible = state.get("visible", result.visible)
        else:
            result.w = state["size"][0]
            result.h = state["size"][1]
            result.rotation = state["angle"]
            if isinstance(result, PolygonResult):
                # vertices are stored relative to the ROI origin (the origin
                # moves on a body drag); fold it back in so the result keeps
                # absolute coordinates with a (0,0) origin
                px, py = state["pos"][0], state["pos"][1]
                result.points = [(p[0] + px, p[1] + py) for p in state["points"]]
                result.x = 0.0
                result.y = 0.0
            else:
                result.x = state["pos"][0]
                result.y = state["pos"][1]
        if not result.equal_v(result_old):
            self.logger.debug("Adding modify undo command")
            self.add_result_undo_cmd([result], ResultUndoMode.MODIFY_NO_UPDATE, [result_old])
            self.dockcnt_info.set_info_by_result(self.proj.crt_anno, result)

    def on_canvas_items_removed(self, ids: list[str]):
        if self.proj.crt_anno is None:
            return
        results = [self.proj.crt_anno.results[i] for i in ids]
        self.add_result_undo_cmd(results, ResultUndoMode.REMOVE)
        # self.remove_results(ids)
        self.dockcnt_anno.remove_items(ids)
        self.dockcnt_info.set_info_by_anno(self.proj.crt_anno)
        self._prune_orphan_instances()
        self._refresh_anno_tree()
        self.update_group_button_state()

    # region Instances (seed-germination)
    def _default_instance_status(self) -> str:
        """Status recorded for newly created instances (Annos dock combo)."""
        return self.dockcnt_anno.default_instance_status()

    def _init_instance_status(self, iid: int):
        """Record the default germination status for a freshly created instance."""
        if self.proj.crt_anno is not None:
            self.proj.crt_anno.instances[iid] = self._default_instance_status()

    def _ensure_current_instance(self) -> int:
        """Return the instance_id for a new annotation.

        With auto-new enabled (default) every annotation gets a freshly
        allocated instance; otherwise the currently selected instance is
        reused, auto-creating one when none is active."""
        if self._instance_auto_new:
            self.current_instance_id = self._new_instance_id()
            self._init_instance_status(self.current_instance_id)
            return self.current_instance_id
        if not self.current_instance_id:
            self.current_instance_id = self._new_instance_id()
            self._init_instance_status(self.current_instance_id)
        return self.current_instance_id

    def on_instance_auto_new_toggled(self, checked: bool):
        self._instance_auto_new = checked

    def _refresh_anno_tree(self):
        """Rebuild the Annos dock tree from the current annotation.

        Silent: the rebuild clears the tree selection, which would otherwise
        trigger the annos<->canvas selection sync and wipe the canvas
        selection; the guard keeps programmatic rebuilds from doing that."""
        if self.proj.crt_anno is None:
            return
        self._syncing_selection = True
        try:
            self.dockcnt_anno.rebuild(self.proj.crt_anno)
        finally:
            self._syncing_selection = False

    def _prune_orphan_instances(self):
        """Drop instance entries that no longer have any member annotation."""
        anno = self.proj.crt_anno
        if anno is None:
            return
        used = {getattr(r, "instance_id", 0) for r in anno.results.values()}
        for iid in [i for i in anno.instances if i not in used]:
            anno.instances.pop(iid, None)

    def on_instance_status_changed(self, iid: int, status: str):
        if self.proj.crt_anno is None:
            return
        self.proj.crt_anno.instances[iid] = status
        self._refresh_tracks()

    # region instance grouping (merge / split)
    def _selected_results(self) -> list[PointResult | RectangleResult | PolygonResult]:
        """Results currently selected on the canvas (fallback: annos tree)."""
        anno = self.proj.crt_anno
        if anno is None:
            return []
        ids = [it.id_ for it in self.canvas.selected_items]
        if not ids:
            ids = self.dockcnt_anno.selected_result_ids()
        return [anno.results[i] for i in ids if i in anno.results]

    def _selection_in_one_instance(self) -> bool:
        """Rule: the group button is checked iff every selected annotation
        belongs to the same merged instance (single in-instance annotation
        counts as grouped)."""
        results = self._selected_results()
        if not results:
            return False
        iids = {getattr(r, "instance_id", 0) for r in results}
        return len(iids) == 1 and 0 not in iids

    def update_group_button_state(self):
        self.actionGroup.setChecked(self._selection_in_one_instance())

    def on_group_instances(self):
        """Merge the selected annotations into one new instance (Ctrl+G)."""
        anno = self.proj.crt_anno
        if anno is None:
            return
        results = self._selected_results()
        if len(results) < 2:
            self.show_toast(self.tr("Select at least 2 annotations to group"), timeout=2000)
            return
        iids = {getattr(r, "instance_id", 0) for r in results}
        if len(iids) == 1 and 0 not in iids:
            return  # already one instance
        new_iid = self._new_instance_id()
        self._init_instance_status(new_iid)
        result_old = [copy.deepcopy(r) for r in results]
        result_new = [copy.deepcopy(r) for r in results]
        for r in result_new:
            r.instance_id = new_iid
        self.add_result_undo_cmd(result_new, ResultUndoMode.MODIFY_NO_UPDATE, result_old)
        self.current_instance_id = new_iid
        self._prune_orphan_instances()
        self._refresh_anno_tree()
        self._refresh_tracks()
        self.update_group_button_state()
        self.show_toast(self.tr(f"Grouped {len(results)} annotations into instance {new_iid}"))

    def on_split_instances(self):
        """Split the selected annotations out of their instances (Ctrl+G when
        they form one instance): each annotation becomes its own independent
        instance inheriting the original group's status; instances left without
        members are deleted."""
        anno = self.proj.crt_anno
        if anno is None:
            return
        results = [r for r in self._selected_results() if getattr(r, "instance_id", 0)]
        if not results:
            return
        result_old = [copy.deepcopy(r) for r in results]
        result_new, inherited = self._new_individual_instances(results)
        self.add_result_undo_cmd(result_new, ResultUndoMode.MODIFY_NO_UPDATE, result_old)
        # the per-result redo pruning recreates instance entries empty; re-apply
        # the inherited statuses now that every result carries its new id
        for iid, status in inherited.items():
            anno.instances[iid] = status
        self._prune_orphan_instances()
        self._refresh_anno_tree()
        self._refresh_tracks()
        self.update_group_button_state()
        self.show_toast(self.tr(f"Split {len(results)} annotations into individual instances"))

    def on_group_button_triggered(self):
        # the checkable action already toggled itself; decide from the real
        # selection state: grouped -> split, otherwise merge
        if self._selection_in_one_instance():
            self.on_split_instances()
        else:
            self.on_group_instances()

    # endregion

    # region selection sync (annos <-> canvas)
    def _sync_annos_selection(self):
        """Mirror the canvas multi-selection into the Annos tree."""
        if self._syncing_selection:
            return
        self._syncing_selection = True
        try:
            ids = [it.id_ for it in self.canvas.selected_items]
            self.dockcnt_anno.set_selected_ids(ids)
        finally:
            self._syncing_selection = False

    def on_anno_selection_changed(self):
        """Annos tree selection -> canvas selection (+ current instance)."""
        if self._syncing_selection:
            return
        self._syncing_selection = True
        try:
            ids = self.dockcnt_anno.selected_result_ids()
            self.canvas.select_items(ids)
            iid = self.dockcnt_anno.selected_instance_id()
            if iid:
                self.current_instance_id = iid
        finally:
            self._syncing_selection = False
        self.update_group_button_state()

    def on_canvas_selection_changed(self):
        self._sync_annos_selection()
        self.update_group_button_state()

    # endregion

    def _maybe_auto_fit_dish(self):
        """Auto-segment + ellipse-fit the dish when auto_fit_dish is enabled and
        the current frame has no dish annotation yet."""
        if not self.settings.auto_fit_dish or self.backend is None or self.current_image is None:
            return
        anno = self.proj.crt_anno
        if anno is None:
            return
        has_dish = any(
            isinstance(r, PolygonResult) and r.labels and r.labels[0].name.lower() in ("dish", "培养皿")
            for r in anno.results.values()
        )
        if has_dish:
            return
        dish_label = next((lbl for lbl in self.proj.labels.values() if lbl.name.lower() in ("dish", "培养皿")), None)
        if dish_label is None or self.auto_mode == AutoMode.MANUAL:
            return
        w, h = self.current_image.size
        worker = ZSamPredictWorker(
            api=self.backend,
            anno_id=anno.id,
            image=anno.image_path,
            rects=[(0, 0, w, h)],
            threshold=self.threshold,
            mode=self.auto_mode,
            result_labels=[dish_label],
            return_type=2,
        )
        self.run_sam_api_worker(worker)

    @staticmethod
    def _crop_box(result: RectangleResult) -> tuple[int, int, int, int]:
        """Axis-aligned crop region for a rectangle, covering its rotated content."""
        from zlabel.utils.geometry import rect_crop_box

        return rect_crop_box(result.x, result.y, result.w, result.h, result.rotation)

    def _maybe_ocr_rect(self, result: RectangleResult):
        """OCR a timestamp rectangle in a background thread."""
        if not result.labels or result.labels[0].name.lower() not in ("timestamp", "时间戳"):
            return
        img = self.current_image
        if img is None:
            return
        box = self._crop_box(result)
        if box[2] <= box[0] or box[3] <= box[1]:
            return
        worker = ZOcrWorker(img, box, result.id)
        worker.emitter.finished.connect(self.on_ocr_finished)
        self.threadpool.start(worker)

    def on_ocr_finished(self, result_id: str, text: str | None):
        anno = self.proj.crt_anno
        if anno is None or result_id not in anno.results:
            return
        r = anno.results[result_id]
        if not isinstance(r, RectangleResult):
            return
        if not text:
            if self.settings.ocr_skip_manual:
                return
            text, ok = QInputDialog.getText(self, self.tr("Timestamp"), self.tr("OCR failed, enter timestamp text:"))
            if not ok or not text:
                return
        r_old = copy.deepcopy(r)
        r_new = copy.deepcopy(r)
        r_new.text = text
        self.add_result_undo_cmd([r_new], ResultUndoMode.MODIFY_NO_UPDATE, [r_old])

    def on_rotation_changed(self, angle: int):
        self.canvas.set_rotation(angle)
        if self.proj.crt_anno is not None:
            self.proj.crt_anno.image_rotation = angle

    def _used_instance_ids(self) -> set[int]:
        """All positive instance ids currently in use in the current frame.

        Instance ids are allocated per frame (each image numbers its instances
        1..N independently); cross-frame correspondence is by matching id, so
        the same number across frames denotes the same object by convention."""
        used: set[int] = set()
        if self.proj.crt_anno is not None:
            for r in self.proj.crt_anno.results.values():
                iid = getattr(r, "instance_id", 0)
                if iid:
                    used.add(iid)
            used.update(self.proj.crt_anno.instances.keys())
        return used

    def _group_tasks(self) -> list[Task]:
        """Tasks of the current frame's sequence group (ordered by day)."""
        group = self.proj.crt_task.group if self.proj.crt_task else ""
        tasks = [t for t in self.proj.tasks.values() if t.group == group] if group else []
        return sorted(tasks, key=lambda t: (t.day, t.filename))

    @staticmethod
    def _next_free_instance_id(used: set[int]) -> int:
        """Smallest positive id not in ``used`` (fills gaps from 1 upward)."""
        iid = 1
        while iid in used:
            iid += 1
        return iid

    def _new_instance_id(self) -> int:
        """Per-frame instance id: the smallest unused positive id in the current
        frame, so gaps are filled before incrementing (each image starts at 1)."""
        return self._next_free_instance_id(self._used_instance_ids())

    # endregion

    # region Sequence copy (previous frame)
    def _prev_task_for_copy(self, task: Task) -> Task | None:
        """Previous frame in the same group (smaller day, else by filename)."""
        if not task.group:
            return None
        cands = [t for t in self.proj.tasks.values() if t.group == task.group and t.anno_id != task.anno_id]
        if not cands:
            return None
        if task.day > 0:
            cands = [t for t in cands if t.day < task.day]
            if not cands:
                return None
            return max(cands, key=lambda t: t.day)
        return max(cands, key=lambda t: (t.day, t.filename))

    def _next_task_for_copy(self, task: Task) -> Task | None:
        """Next frame in the same group (larger day, else by filename)."""
        if not task.group:
            return None
        cands = [t for t in self.proj.tasks.values() if t.group == task.group and t.anno_id != task.anno_id]
        if not cands:
            return None
        if task.day > 0:
            cands = [t for t in cands if t.day > task.day]
            if not cands:
                return None
            return min(cands, key=lambda t: t.day)
        return min(cands, key=lambda t: (t.day, t.filename))

    def _neighbor_task_for_copy(self, task: Task, direction: int) -> Task | None:
        """Neighbor frame in the same group: previous (-1) or next (+1)."""
        if direction > 0:
            return self._next_task_for_copy(task)
        return self._prev_task_for_copy(task)

    def _load_anno_for_task(self, task: Task) -> Annotation | None:
        if task.anno is not None and task.anno.image_path:
            return task.anno
        if self.backend is None:
            return None
        anno_json = self.backend.get_zlabel(name=f"{task.anno_id}.{self.anno_suffix}")
        if anno_json is None:
            return None
        try:
            anno = Annotation.model_validate_json(anno_json, strict=True)
            self.proj.reconcile_result_labels(anno)
        except Exception as e:
            self.logger.warning(f"Failed to load {task.anno_id=} for copy, {e=}")
            return None
        task.anno = anno
        return anno

    def _ask_copy_options(self, task: Task) -> CopyOptions | None:
        """Dialog to pick copy direction, items, and optional rotation alignment."""
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Copy / propagate from neighbor frame"))
        lay = QVBoxLayout(dlg)

        lay.addWidget(QLabel(self.tr("Direction:")))
        cmb_dir = QComboBox()
        cmb_dir.addItem(self.tr("From previous frame"), -1)
        cmb_dir.addItem(self.tr("From next frame"), 1)
        lay.addWidget(cmb_dir)

        cb_dish = QCheckBox(self.tr("Dish"), dlg)
        cb_dish.setChecked(True)
        cb_time = QCheckBox(self.tr("Timestamp"), dlg)
        cb_time.setChecked(True)
        cb_parts = QCheckBox(self.tr("Instance parts (Seed/Root/Seedling)"), dlg)
        cb_parts.setChecked(True)
        for cb in (cb_dish, cb_time, cb_parts):
            lay.addWidget(cb)

        cb_align = QCheckBox(self.tr("Align copied annotations (rotate + scale) to the dish"), dlg)
        cb_align.setChecked(True)
        lay.addWidget(cb_align)
        ang_label = QLabel()
        ang_label.setWordWrap(True)
        lay.addWidget(ang_label)
        spin_angle = QDoubleSpinBox()
        spin_angle.setRange(-360, 360)
        spin_angle.setDecimals(1)
        spin_angle.setSuffix(self.tr("°"))
        lay.addWidget(spin_angle)
        scale_label = QLabel(self.tr("Scale:"))
        lay.addWidget(scale_label)
        spin_scale = QDoubleSpinBox()
        spin_scale.setRange(0.1, 10.0)
        spin_scale.setDecimals(3)
        spin_scale.setSingleStep(0.05)
        spin_scale.setValue(1.0)
        lay.addWidget(spin_scale)
        center_label = QLabel()
        lay.addWidget(center_label)

        def _reload_source():
            direction = cmb_dir.currentData()
            neighbor = self._neighbor_task_for_copy(task, direction)
            src_anno = self._load_anno_for_task(neighbor) if neighbor else None
            angle, scale, src_c, tgt_c, ang_rel, scale_rel = self._estimate_copy_alignment(src_anno, self.proj.crt_anno)
            if src_anno is not None and self._frame_references(src_anno)[0] is not None:
                if ang_rel:
                    ang_label.setText(self.tr(f"Auto-estimated rotation: {angle:.1f}°"))
                else:
                    ang_label.setText(
                        self.tr("Dish orientation unreliable (round dish / no Number label) - enter manually.")
                    )
            else:
                ang_label.setText(self.tr("No dish in both frames - enter rotation/scale manually."))
            spin_angle.setValue(angle if ang_rel else 0.0)
            spin_scale.setValue(scale if scale_rel else 1.0)
            if scale_rel:
                scale_label.setText(self.tr(f"Scale: (auto-estimated {scale:.3f})"))
            else:
                scale_label.setText(self.tr("Scale: (no auto estimate - enter manually)"))
            center_label.setText(
                self.tr(
                    f"Dish centers: source ({src_c[0]:.0f}, {src_c[1]:.0f}) -> target ({tgt_c[0]:.0f}, {tgt_c[1]:.0f})"
                )
            )

        cmb_dir.currentIndexChanged.connect(lambda *_: _reload_source())
        _reload_source()

        btnbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            dlg,
        )
        btnbox.accepted.connect(dlg.accept)
        btnbox.rejected.connect(dlg.reject)
        lay.addWidget(btnbox)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        opts: set[str] = set()
        if cb_dish.isChecked():
            opts.add("dish")
        if cb_time.isChecked():
            opts.add("time")
        if cb_parts.isChecked():
            opts.add("parts")
        direction = cmb_dir.currentData()
        neighbor = self._neighbor_task_for_copy(task, direction)
        src_anno = self._load_anno_for_task(neighbor) if neighbor else None
        _angle, _scale, src_c, tgt_c, _, _ = self._estimate_copy_alignment(src_anno, self.proj.crt_anno)
        return CopyOptions(
            direction=direction,
            opts=opts,
            angle=spin_angle.value() if cb_align.isChecked() else 0.0,
            scale=spin_scale.value() if cb_align.isChecked() else 1.0,
            src_center=src_c,
            tgt_center=tgt_c,
        )

    @staticmethod
    def _frame_references(anno: Annotation | None) -> tuple[tuple | None, tuple | None]:
        """Reference features of a frame: (dish_ellipse, number_center).

        ``dish_ellipse`` is the (cx, cy, angle_deg, (ma, mi)) fit of the dish
        polygon (None if no dish); ``number_center`` is the center of the
        Number/编号 rectangle (None if not annotated). Together they define the
        similarity transform that maps this frame's dish onto another frame's.
        """
        if anno is None:
            return None, None
        from zlabel.utils.geometry import fit_ellipse_params

        dish = None
        number = None
        for r in anno.results.values():
            name = (r.labels[0].name if r.labels else "").lower()
            if isinstance(r, PolygonResult) and name in ("dish", "培养皿") and dish is None:
                dish = fit_ellipse_params(r.points)
            elif isinstance(r, RectangleResult) and name in ("number", "编号") and number is None:
                number = (r.x + r.w / 2.0, r.y + r.h / 2.0)
        return dish, number

    def _estimate_copy_alignment(
        self, src_anno: Annotation | None, tgt_anno: Annotation | None
    ) -> tuple[float, float, tuple[float, float], tuple[float, float], bool, bool]:
        """Estimate the similarity transform (rotation + uniform scale + center
        mapping) aligning source-frame annotations onto the target frame.

        With a dish and a Number label in both frames the dish-center ->
        number-center vector gives an unambiguous rotation and a scale (vector /
        dish-size ratio). Without a Number label the dish ellipse orientation is
        used (180 deg ambiguous -> not reliable). Without a dish in both frames
        nothing can be auto-estimated.

        Returns ``(angle, scale, src_center, tgt_center, angle_reliable, scale_reliable)``.
        """
        src = self._frame_references(src_anno)
        tgt = self._frame_references(tgt_anno)
        if src is None or tgt is None or src[0] is None or tgt[0] is None:
            return 0.0, 1.0, (0.0, 0.0), (0.0, 0.0), False, False
        (s_cx, s_cy, _sang, (sa, sb)), (t_cx, t_cy, _tang, (ta, tb)) = src[0], tgt[0]
        src_center = (s_cx, s_cy)
        tgt_center = (t_cx, t_cy)

        s_area, t_area = sa * sb, ta * tb
        scale = math.sqrt(t_area / s_area) if s_area > 0 and t_area > 0 else 1.0
        scale_reliable = s_area > 0 and t_area > 0

        angle = 0.0
        angle_reliable = False
        if src[1] is not None and tgt[1] is not None:
            vs = (src[1][0] - s_cx, src[1][1] - s_cy)
            vt = (tgt[1][0] - t_cx, tgt[1][1] - t_cy)
            if math.hypot(*vs) > 1e-6 and math.hypot(*vt) > 1e-6:
                angle = math.degrees(math.atan2(vt[1], vt[0]) - math.atan2(vs[1], vs[0]))
                angle_reliable = True
        if not angle_reliable:
            # fall back to the dish ellipse orientation (ambiguous by 180 deg)
            angle = (_tang - _sang + 180.0) % 360.0 - 180.0
            angle_reliable = max(sa / sb, sb / sa) > 1.2 and max(ta / tb, tb / ta) > 1.2
        return angle, scale, src_center, tgt_center, angle_reliable, scale_reliable

    @staticmethod
    def _transform_result(
        result,
        angle: float,
        scale: float,
        src_center: tuple[float, float],
        tgt_center: tuple[float, float],
    ):
        """Apply the similarity transform (rotation + scale + translation) to a
        copied result's geometry."""
        from zlabel.utils.geometry import similarity_transform

        if isinstance(result, PolygonResult):
            result.points = [similarity_transform(p, angle, scale, src_center, tgt_center) for p in result.points]
        elif isinstance(result, RectangleResult):
            x, y = similarity_transform((result.x, result.y), angle, scale, src_center, tgt_center)
            result.x, result.y = x, y
            result.w *= scale
            result.h *= scale
            result.rotation = (result.rotation + angle) % 360

    def _copy_from_frame(self, neighbor: Task, opts: CopyOptions):
        """Copy (and optionally similarity-align) annotations from a neighbor
        frame, keeping the cross-frame instance identity (`instance_id`).

        The similarity transform (rotation + uniform scale + dish-center
        mapping) is estimated from the dish / Number references of both frames
        (see ``_estimate_copy_alignment``)."""
        anno = self.proj.crt_anno
        if anno is None:
            return
        src_anno = self._load_anno_for_task(neighbor)
        if src_anno is None or not src_anno.results:
            return

        # Per-frame numbering: skip source instances whose id already exists in
        # the target frame (same id = same object, already present) to avoid
        # duplicate ids within one frame.
        target_iids = set(anno.instances) | {getattr(r, "instance_id", 0) for r in anno.results.values()}

        results_new = []
        for r in src_anno.results.values():
            name = (r.labels[0].name if r.labels else "").lower()
            if isinstance(r, RectangleResult):
                if name in ("timestamp", "时间戳", "number", "编号"):
                    keep = "time" in opts.opts
                else:
                    keep = "dish" in opts.opts
            elif isinstance(r, PolygonResult):
                if name in ("dish", "培养皿"):
                    keep = "dish" in opts.opts
                else:
                    keep = "parts" in opts.opts
            else:
                keep = False
            if not keep:
                continue
            if getattr(r, "instance_id", 0) and r.instance_id in target_iids:
                continue

            nr = copy.deepcopy(r)
            nr.id = id_uuid4()
            # printed labels (number/timestamp) are attached to the dish, so they
            # move with it; apply the similarity transform to everything copied.
            # `instance_id` is the cross-frame identity: copied parts keep the
            # source instance id, so the same seed keeps its number across frames.
            if opts.angle or opts.scale != 1.0:
                self._transform_result(nr, opts.angle, opts.scale, opts.src_center, opts.tgt_center)
            results_new.append(nr)

        if not results_new:
            return
        # carry the per-instance status from the source frame (fall back to default)
        for r in results_new:
            iid = getattr(r, "instance_id", 0)
            if iid and iid not in anno.instances:
                anno.instances[iid] = src_anno.instances.get(iid, "") or self._default_instance_status()
        self.add_result_undo_cmd(results_new, ResultUndoMode.ADD)
        self._refresh_anno_tree()
        self._refresh_tracks()

    def _maybe_copy_prev_frame(self):
        if not self.settings.enable_copy_prev:
            return
        task = self.proj.crt_task
        if task is None or not task.group or self.proj.crt_anno is None:
            return
        if self._skip_copy_anno == self.proj.crt_anno.id or self.proj.crt_anno.results:
            return
        opts = self._ask_copy_options(task)
        if opts is None:
            self._skip_copy_anno = self.proj.crt_anno.id
            return
        neighbor = self._neighbor_task_for_copy(task, opts.direction)
        if neighbor is None:
            self._skip_copy_anno = self.proj.crt_anno.id
            return
        self._copy_from_frame(neighbor, opts)

    def on_copy_prev_triggered(self):
        task = self.proj.crt_task
        if not self.settings.enable_copy_prev or task is None or self.proj.crt_anno is None:
            return
        if not task.group:
            QMessageBox.information(
                self,
                self.tr("Copy"),
                self.tr("Current frame has no sequence group."),
                QMessageBox.StandardButton.Ok,
            )
            return
        opts = self._ask_copy_options(task)
        if opts is None:
            return
        neighbor = self._neighbor_task_for_copy(task, opts.direction)
        if neighbor is None:
            QMessageBox.information(
                self,
                self.tr("Copy"),
                self.tr("No neighbor frame in this sequence."),
                QMessageBox.StandardButton.Ok,
            )
            return
        self._copy_from_frame(neighbor, opts)

    # endregion

    def on_canvas_scene_mouse_moved(self, pos: QPointF):
        x, y = pos.x(), pos.y()
        self.statusbar.showMessage(f"{x:.2f}, {y:.2f}")

    # endregion
    # endregion

    # region INIT
    def init_ui(self):
        self.dialog_about = DialogAbout(self)
        self.dialog_shortcut = DialogShortcut(self)

        self.setupUi(self)
        self.action_group_edit = [
            self.actionMove,
            self.actionEdit,
            self.actionRectangle,
            self.actionPoint,
            self.actionPolygon,
        ]

        self.annotation_types = [
            ("Rectangle", ":/icon/icons/rectangle_two_points.svg"),
            ("Polygon", ":/icon/icons/polygon.svg"),
            ("KeyPoint", ":/icon/icons/points.svg"),
        ]
        self.cmbox_anno_type = QComboBox(self)
        for anno_type, icon_path in self.annotation_types:
            icon = QIcon()
            icon.addFile(icon_path, QSize(), QIcon.Mode.Normal, QIcon.State.Off)
            self.cmbox_anno_type.addItem(icon, anno_type)
        self.toolBar.insertWidget(self.actionSAM, self.cmbox_anno_type)

        self.rgb_channels = [
            ("Gray", ":/icon/icons/channel_gray.svg"),
            ("R", ":/icon/icons/channel_r.svg"),
            ("G", ":/icon/icons/channel_g.svg"),
            ("B", ":/icon/icons/channel_b.svg"),
            ("RGB", ":/icon/icons/channel.svg"),
        ]
        self.cmbox_rgb = QComboBox(self)
        for channel, icon_path in self.rgb_channels:
            icon = QIcon()
            icon.addFile(icon_path, QSize(), QIcon.Mode.Normal, QIcon.State.Off)
            self.cmbox_rgb.addItem(icon, channel)
        self.cmbox_rgb.setCurrentIndex(4)
        # self.cmbox_rgb.setEnabled(False)
        self.toolBar.addWidget(self.cmbox_rgb)

        self.slider_threshold = ZSlider(Qt.Orientation.Horizontal, self)
        self.slider_threshold.setValue(self.threshold)
        self.slider_threshold.setStatusTip(self.tr("Set Threshold"))
        self.slider_threshold.setToolTip(self.tr("Set Threshold"))
        self.slider_threshold.setMaximumSize(150, 15)
        self.toolBar.addWidget(self.slider_threshold)

        # view rotation controls, placed right after the copy-prev action
        self.btn_rot_ccw = QPushButton(self)
        self.btn_rot_ccw.setObjectName("btn_rot_ccw")
        self.btn_rot_ccw.setIcon(QIcon(":/icon/icons/go_backward90.svg"))
        self.btn_rot_ccw.setToolTip(self.tr("Rotate view counter-clockwise"))
        self.spin_rotation = QSpinBox(self)
        self.spin_rotation.setObjectName("spin_rotation")
        self.spin_rotation.setRange(-359, 359)
        self.spin_rotation.setSuffix("°")
        self.spin_rotation.setToolTip(self.tr("Rotate the view (stored coords stay in image space)"))
        self.btn_rot_cw = QPushButton(self)
        self.btn_rot_cw.setObjectName("btn_rot_cw")
        self.btn_rot_cw.setIcon(QIcon(":/icon/icons/go_forward90.svg"))
        self.btn_rot_cw.setToolTip(self.tr("Rotate view clockwise"))
        # insert immediately after action_copy_prev (before whatever follows it)
        acts = self.toolBar.actions()
        insert_before = None
        for i, a in enumerate(acts):
            if a is self.action_copy_prev and i + 1 < len(acts):
                insert_before = acts[i + 1]
                break
        for w in (self.btn_rot_ccw, self.spin_rotation, self.btn_rot_cw):
            if insert_before is not None:
                self.toolBar.insertWidget(insert_before, w)
            else:
                self.toolBar.addWidget(w)

        # right dock vertical height ratio Info:Annos:Labels = 1:2:2
        for dock, stretch in [
            (self.dock_infos, 1),
            (self.dock_annos, 2),
            (self.dock_labels, 2),
        ]:
            sp = dock.sizePolicy()
            sp.setVerticalStretch(stretch)
            sp.setVerticalPolicy(QSizePolicy.Policy.Preferred)
            dock.setSizePolicy(sp)

        # Tracks dock: cross-frame timeline (video-editor style) at the bottom
        self.dockcnt_tracks = ZDockTracksContent(
            self._load_anno_for_task,
            lambda name: self.backend.get_image(name) if self.backend is not None else None,
            self,
        )
        self.dock_tracks = QDockWidget(self.tr("Tracks"), self)
        self.dock_tracks.setObjectName("dock_tracks")
        self.dock_tracks.setWidget(self.dockcnt_tracks)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_tracks)
        self.actionTracks = QAction(self.tr("Tracks"), self)
        self.actionTracks.setObjectName("actionTracks")
        self.actionTracks.setCheckable(True)
        self.actionTracks.setChecked(True)
        self.menuDocks.addAction(self.actionTracks)

        # keep the side docks compact so the canvas keeps most of the width
        # (explicit min/max override the inflated minimumSizeHints)
        for content, lo, hi in [
            (self.dockcnt_files, 1, 541),
            (self.dockcnt_info, 1, 541),
            (self.dockcnt_anno, 1, 541),
            (self.dockcnt_labels, 1, 541),
        ]:
            content.setMinimumWidth(lo)
            content.setMaximumWidth(hi)
        # the bottom timeline stays a horizontal strip but tall enough for
        # several instance rows (rows run 1..max instance id)
        self.dockcnt_tracks.setMinimumHeight(1)
        self.dockcnt_tracks.setMaximumHeight(600)

    def init_signals(self):
        # dialog
        self.dialog_settings.sigSettingsChanged.connect(self.on_dialog_settings_changed)
        self.dialog_settings.sigApplyClicked.connect(self.on_dialog_settings_apply_clicked)
        self.dialog_settings.sigProjectChanged.connect(self.on_project_changed)
        self.dialog_settings.destroyed.connect(self.dialog_processing.close)

        # actions
        self.action_import_task.triggered.connect(self.on_action_import_task_triggered)
        self.actionExport.triggered.connect(self.on_action_export_triggered)
        self.actionSettings.triggered.connect(self.dialog_settings.show)
        self.actionAbout.triggered.connect(self.dialog_about.show)
        self.actionShortcut.triggered.connect(self.dialog_shortcut.show)
        self.actionExit.triggered.connect(self.close)
        self.actionChinese.triggered.connect(self.on_action_chinese_triggered)
        self.actionEnglish.triggered.connect(self.on_action_english_triggered)

        self.actionNext.triggered.connect(self.on_action_next_prev_triggered)
        self.actionPrev.triggered.connect(self.on_action_next_prev_triggered)
        self.actionUndo.triggered.connect(self.on_action_undo_triggered)
        self.actionRedo.triggered.connect(self.on_action_redo_triggered)

        self.actionSAM.triggered.connect(self.on_action_SAM_triggered)
        self.actionOpenCV.triggered.connect(self.on_action_opencv_triggered)
        self.actionMove.triggered.connect(self.on_action_move_triggered)
        self.actionEdit.triggered.connect(self.on_action_edit_triggered)
        self.actionRectangle.triggered.connect(self.on_action_rectangle_triggered)
        self.actionPoint.triggered.connect(self.on_action_point_triggered)
        self.actionPolygon.triggered.connect(self.on_action_polygon_triggered)
        self.actionMerge.triggered.connect(self.on_action_merge_triggered)

        self.actionFinish.triggered.connect(self.on_action_finish_triggered)
        self.actionCancel.triggered.connect(self.on_action_cancel_triggered)
        self.actionSave.triggered.connect(self.on_action_save_triggered)

        self.actionVisible.triggered.connect(self.on_action_visible_triggered)
        self.actionZoom_in.triggered.connect(self.on_action_zoom_in_triggered)
        self.actionZoom_out.triggered.connect(self.on_action_zoom_out_triggered)
        self.actionFit_wiondow.triggered.connect(self.on_action_fit_window_triggered)

        self.actionRestore.triggered.connect(self.on_action_restore_triggered)
        self.actionAnnotations.triggered.connect(self.on_action_annotations_triggered)
        self.actionInfo.triggered.connect(self.on_action_info_triggered)
        self.actionFiles.triggered.connect(self.on_action_files_triggered)
        self.actionLabels.triggered.connect(self.on_action_labels_triggered)

        self.cmbox_anno_type.currentIndexChanged.connect(self.on_cmbox_annotype_index_changed)
        self.cmbox_rgb.currentIndexChanged.connect(self.on_cmbox_rgb_index_changed)

        # self.btn_online_mode.sigCheckStateChanged.connect(self.on_btn_online_mode_check_changed)
        self.slider_threshold.valueChanged.connect(self.on_slider_threshold_changed)

        # canvas
        self.canvas.sigPointCreated.connect(self.on_canvas_point_created)
        self.canvas.sigRectangleCreated.connect(self.on_canvas_rectangle_created)
        self.canvas.sigPolygonCreated.connect(self.on_canvas_polygon_created)
        self.canvas.sigItemClicked.connect(self.on_canvas_item_clicked)
        # self.canvas.sigItemStateChanged.connect(self.on_canvas_item_state_changed)
        self.canvas.sigItemStateChangeFinished.connect(self.on_canvas_item_state_change_finished)
        self.canvas.sigItemsRemoved.connect(self.on_canvas_items_removed)
        self.canvas.sigMouseMoved.connect(self.on_canvas_scene_mouse_moved)
        self.canvas.sigMouseBackClicked.connect(self.actionPrev.trigger)
        self.canvas.sigMouseForwardClicked.connect(self.actionNext.trigger)

        # dock info
        self.dock_infos.visibilityChanged.connect(self.on_dock_info_visibility_changed)
        self.dockcnt_info.sigNoteTextChanged.connect(self.on_dock_info_ledit_note_changed)

        # dock files
        self.dock_files.visibilityChanged.connect(self.on_dock_files_visibility_changed)
        self.dockcnt_files.sigItemClicked.connect(self.on_dock_files_item_clicked)
        self.dockcnt_files.sigFetchTasks.connect(self.on_dock_files_fetch_tasks)
        self.dockcnt_files.sigStorageChanged.connect(self.on_dock_files_storage_changed)
        self.dockcnt_files.sigLocalDirChanged.connect(self.on_dock_files_local_dir_changed)

        # dock labels
        self.dock_labels.visibilityChanged.connect(self.on_dock_label_visibility_changed)
        self.dockcnt_labels.sigItemClicked.connect(self.on_dock_label_listw_item_clicked)
        self.dockcnt_labels.sigItemColorChanged.connect(self.on_dock_label_item_color_changed)
        self.dockcnt_labels.sigItemDoubleClicked.connect(self.on_dock_label_item_double_clicked)
        self.dockcnt_labels.sigItemVisibilityToggled.connect(self.on_label_visibility_toggled)

        for n in range(1, 10):
            sc = QShortcut(QKeySequence(str(n)), self)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(functools.partial(self.on_shortcut_select_label_number, n))
            self._label_shortcuts.append(sc)

        # keypoint visibility shortcuts (apply to the selected PointResult).
        # L/O/X = labeled/occluded/excluded (missing); only active in KeyPoint
        # mode so they never clash with actionMove/actionVisible/actionPolygon
        # shortcuts or with the canvas V/X/C polygon-drawing keys.
        self._point_visible_shortcuts: list[QShortcut] = []
        for key, vis in [
            ("L", KeypointVisible.VISIBLE),
            ("O", KeypointVisible.OCCLUDED),
            ("X", KeypointVisible.MISSING),
        ]:
            sc = QShortcut(QKeySequence(key), self)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(functools.partial(self.on_toggle_point_visible, vis.value))
            self._point_visible_shortcuts.append(sc)

        # group / ungroup keypoints into instances.
        # 'G' is already bound to actionMerge (which merges keypoints when
        # points are selected); only 'U' needs a dedicated shortcut here.
        self._point_group_shortcuts: list[QShortcut] = []
        sc = QShortcut(QKeySequence("U"), self)
        sc.setContext(Qt.ShortcutContext.WindowShortcut)
        sc.activated.connect(self.on_ungroup_points)
        self._point_group_shortcuts.append(sc)

        # save shortcut: plain "S" (Ctrl+S lives on actionSave already, so
        # registering StandardKey.Save here would make the shortcut ambiguous)
        sc = QShortcut(QKeySequence("S"), self)
        sc.setContext(Qt.ShortcutContext.WindowShortcut)
        sc.activated.connect(self.on_action_save_triggered)

        # group selected annotations into one instance (merge) / split (unmerge):
        # a single Ctrl+G toggles between the two based on the selection state
        self.actionGroup.triggered.connect(self.on_group_button_triggered)
        self._group_shortcuts: list[QShortcut] = []
        sc = QShortcut(QKeySequence("Ctrl+G"), self)
        sc.setContext(Qt.ShortcutContext.WindowShortcut)
        sc.activated.connect(self.on_group_button_triggered)
        self._group_shortcuts.append(sc)

        # dock annotation context menu
        self.dockcnt_anno.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dockcnt_anno.listWidget.customContextMenuRequested.connect(self.on_anno_context_menu)

        # dock annotations
        self.dock_annos.visibilityChanged.connect(self.on_dock_anno_visibility_changed)
        self.dockcnt_anno.listWidget.itemClicked.connect(self.on_dock_anno_listw_item_clicked)
        self.dockcnt_anno.listWidget.itemSelectionChanged.connect(self.on_anno_selection_changed)
        self.dockcnt_anno.sigItemDeleted.connect(self.on_dock_anno_item_deleted)
        self.dockcnt_anno.sigItemCountChanged.connect(self.on_dock_anno_item_count_changed)
        self.dockcnt_anno.sigInstanceStatusChanged.connect(self.on_instance_status_changed)
        self.dockcnt_anno.sigAutoNewInstanceToggled.connect(self.on_instance_auto_new_toggled)

        # canvas selection changes (rubber-band multi-select) -> annos sync
        self.canvas.sigSelectionChanged.connect(self.on_canvas_selection_changed)

        self.action_copy_prev.triggered.connect(self.on_copy_prev_triggered)

        self.btn_rot_ccw.clicked.connect(lambda: self.spin_rotation.setValue((self.spin_rotation.value() - 90) % 360))
        self.btn_rot_cw.clicked.connect(lambda: self.spin_rotation.setValue((self.spin_rotation.value() + 90) % 360))
        self.spin_rotation.valueChanged.connect(self.on_rotation_changed)

        # Tracks dock
        self.actionTracks.triggered.connect(self.on_action_tracks_triggered)
        self.dock_tracks.visibilityChanged.connect(self.on_dock_tracks_visibility_changed)
        self.dockcnt_tracks.sigOpenInstance.connect(self.on_instance_open)
        self.dockcnt_tracks.sigCellMoved.connect(self.on_cell_moved)
        self.dockcnt_tracks.sigGroupChanged.connect(self._on_tracks_group_changed)

    # endregion

    # region events
    def closeEvent(self, event: QCloseEvent):
        self.save_geometry()
        event.accept()

    # endregion
