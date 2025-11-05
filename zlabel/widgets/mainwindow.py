import copy
import functools
import json
import os
from collections import OrderedDict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from qtpy.QtCore import (
    QPoint,
    QPointF,
    QRectF,
    QSettings,
    Qt,
    QThreadPool,
    QTranslator,
    Signal,
    Slot,
    QSize,
)
from qtpy.QtGui import QSurfaceFormat, QUndoStack, QIcon
from qtpy.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QComboBox

from zlabel.utils import (
    SamApiHelper,
    AutoMode,
    DrawMode,
    SettingsKey,
    StatusMode,
    ZLogger,
    Annotation,
    Label,
    Project,
    Result,
    ResultType,
    RectangleResult,
    PolygonResult,
    Task,
    User,
    id_md5,
    id_uuid4,
)
from zlabel.utils.enums import RgbMode
from zlabel.widgets import (
    ZSettings,
    DialogProcessing,
    ZLoginThread,
    ResultUndoMode,
    ZResultUndoCmd,
    Toast,
    ZListWidgetItem,
    ZSlider,
    ZTableWidgetItem,
    SamWorkerResult,
    ZGetImageWorker,
    ZGetTasksWorker,
    ZPreuploadImageWorker,
    ZSamPredictWorker,
    ZUploadFileWorker,
    DialogAbout,
    DialogSettings,
)

from .ui import Ui_MainWindow

sfmt = QSurfaceFormat()
sfmt.setSwapInterval(0)
QSurfaceFormat.setDefaultFormat(sfmt)


class MainWindow(QMainWindow, Ui_MainWindow):
    sigSettingsChecked = Signal(bool)
    sigLoginFinished = Signal(bool)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.logger = ZLogger("MainWindow")
        self.root_dir = "."
        self.settings_path = "zlabel.conf"
        self.settings_format = QSettings.Format.IniFormat

        self.settings: ZSettings = ZSettings(self.settings_path, self.settings_format)
        # self.api_alist: AlistApiHelper
        self.api_predict: SamApiHelper

        self.user = User.default()
        self.label_default = Label.default()
        self.user_token: str | None = None

        self.proj: Project
        self.result_old = None
        self.undo_stack = QUndoStack(self)
        self.threadpool = QThreadPool()

        self.anno_suffix = "zlabel"
        self.last_path = "."
        self._image_cache: dict[str, Image.Image] = {}
        self.threshold = 100
        self.rgb_mode = RgbMode.RGB

        self.init_ui()
        self.init_signals()
        self.load_settings()

    # region functions
    def load_settings(self):
        self.dialog_processing.show()
        path = Path(self.settings_path)
        if path.exists() and path.is_file():
            self.settings = ZSettings(self.settings_path, self.settings_format)
            if not (self.settings.validate() and self.settings.project_name):
                self.dialog_settings.show()
                return
        else:
            if not path.parent.exists():
                path.parent.mkdir(parents=True)
            self.dialog_settings.show()
            return
        # file exists and check passed
        self.user.name = self.settings.username
        # self.api_alist = AlistApiHelper(self.settings.host, self.settings.url_prefix)
        self.api_predict = SamApiHelper(
            self.settings.username,
            self.settings.password,
            self.settings.host,
        )
        self.login()
        self.set_loglevel(self.settings.log_level)

    def login(self):
        # TODO: use async or worker?
        self.login_thread = ZLoginThread(
            self.api_predict,
            self.settings.username,
            self.settings.password,
        )
        self.login_thread.login_success.connect(self.on_login_success)
        self.login_thread.login_fail.connect(self.on_login_failed)
        self.login_thread.finished.connect(self.login_thread.quit)
        self.login_thread.finished.connect(self.login_thread.deleteLater)

        self.login_thread.start()

    def on_login_failed(self):
        self.dialog_processing.close()

        QMessageBox.critical(
            self,
            "Error",
            "Login Failed, check internet or username and password",
            QMessageBox.StandardButton.Ok,
        )
        if not self.dialog_settings.isVisible():
            self.dialog_settings.show()

    def on_login_success(self, token: str):
        self.user_token = token
        self.logger.info(f"Login success, {self.settings.username=}")
        self.dialog_settings.close()

        self.restore_project()
        # self.restore_annotations()

        self.actionSAM.setChecked(self.sam_enabled)
        self.actionOpenCV.setChecked(self.cv_enabled)

        if len(self.proj.tasks) > 0:
            tasks = list(self.proj.tasks.values())
            if self.proj.key_task is None:
                self.proj.key_task = list(self.proj.tasks.keys())[0]
            self.dockcnt_files.set_file_list(tasks)
            self.dockcnt_files.set_row_by_txt(self.proj.key_task)

            if self.proj.crt_anno is None:
                self.on_dock_files_item_clicked(self.proj.key_task)
            labels = list(self.proj.crt_anno.labels.keys())  # type: ignore
            if len(labels) > 0:
                self.proj.crt_anno.key_label = labels[0]  # type: ignore

        if self.proj.crt_anno and self.proj.crt_anno.labels:
            self.dockcnt_labels.set_labels(
                list(self.proj.crt_anno.labels.values()),
                self.proj.crt_anno.key_label,
            )
            self.dockcnt_anno.add_items_by_anno(self.proj.crt_anno)
            self.canvas.create_items_by_anno(self.proj.crt_anno)
            self.dockcnt_info.set_info_by_anno(self.proj.crt_anno)
        self.on_settings_color_changed(self.settings.color)
        self.try_set_image()

        self.dialog_processing.close()

    def refresh_tasks(self, tasks: list[Task]):
        self.proj.tasks.clear()
        for task in tasks:
            self.proj.add_task(task)
        self.proj.reset_task_key()
        self.proj.save_json(self.settings.project_path)
        if self.user_token:
            self.on_login_success(self.user_token)

    def load_tasks(self, path: str):
        if not os.path.exists(path):
            QMessageBox.critical(
                self,
                "Error",
                f"Tasks {path=} not exists! Import First!",
                QMessageBox.StandardButton.Ok,
            )
            return
        with open(path, "r", encoding="utf-8") as f:
            tasks = [Task.model_validate(t) for t in json.load(f)]
        # ^ use anno_id as key to simplify object get/set in files list
        QMessageBox.information(
            self,
            "Info",
            f"Import {len(tasks)} Tasks Success!",
            QMessageBox.StandardButton.Ok,
        )
        return tasks

    def load_tasks_remote(self):
        worker = ZGetTasksWorker(
            self.api_predict,
            self.settings.fetch_num,
            self.settings.fetch_finished,
            self.settings.username,
            self.settings.password,
        )
        worker.emitter.success.connect(self.on_get_tasks_success)
        worker.emitter.fail.connect(self.on_get_tasks_failed)
        self.threadpool.start(worker)

    def on_get_tasks_success(self, tasks: list[Task]):
        self.refresh_tasks(tasks)

        self.dockcnt_files.set_file_list(tasks)
        self.dockcnt_files.set_row_by_txt(self.proj.key_task)
        QMessageBox.information(
            self,
            "Info",
            f"Import {len(tasks)} Tasks Success!",
            QMessageBox.StandardButton.Ok,
        )

    def on_get_tasks_failed(self, msg: str):
        QMessageBox.critical(
            self,
            "Error",
            f"Get Tasks Failed, {msg=}",
            QMessageBox.StandardButton.Ok,
        )

    def create_project(self):
        self.proj = Project.new(
            name=self.settings.project_name,
            description=self.settings.project_description,
        )
        self.proj.save_json(self.settings.project_path)

    def try_set_image(self, image: Image.Image | None = None):
        if self.proj.crt_task is None:
            return
        if image is None:
            img_name = self.proj.crt_task.filename
            if img_name not in self._image_cache:
                worker = ZGetImageWorker(
                    self.api_predict,
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
        self.canvas.clear_image()
        self.canvas.set_image(np.asarray(image, dtype=np.uint8))
        self.canvas.set_rgb(self.rgb_mode)
        self.dialog_processing.close()

    def on_get_image_fail(self, msg: str):
        self.dialog_processing.close()
        QMessageBox.warning(
            self,
            "Warning",
            f"Get image failed, {msg=}",
            QMessageBox.StandardButton.Ok,
        )

    def add_result(self, result: RectangleResult | PolygonResult):
        if self.proj.crt_anno is None:
            self.logger.error(f"Current annotation is None! {self.proj.crt_task=}")
            return
        self.proj.crt_anno.add_result(result)
        self.canvas.create_item_by_result(result)
        self.dockcnt_info.set_info_by_result(result)
        self.dockcnt_anno.add_item(result.id)
        self.logger.debug(f"Added result {result}")

    def add_results(self, results: list[RectangleResult | PolygonResult]):
        for result in results:
            self.add_result(result)

    def add_result_undo_cmd(
        self,
        results: list[RectangleResult | PolygonResult],
        mode: ResultUndoMode,
        results_old: list[RectangleResult | PolygonResult] | None = None,
    ):
        cmd = ZResultUndoCmd(self, results, mode, results_old)
        self.undo_stack.push(cmd)

    def remove_result(self, id_: str):
        if self.proj.crt_anno is None or id_ not in self.proj.crt_anno.results:
            self.logger.debug(f"{id_=}, {self.current_anno.results.keys()=}")  # type: ignore
            return
        self.proj.crt_anno.remove_result(id_)
        self.canvas.remove_items_by_ids([id_])
        self.dockcnt_anno.remove_item(id_)

    def remove_results(self, ids: list[str]):
        for id_ in ids:
            self.remove_result(id_)

    def modify_result(self, result: RectangleResult | PolygonResult):
        if self.proj.crt_anno is None or result.id not in self.proj.crt_anno.results:
            return
        self.logger.debug(f"{result=}\n{self.result_old=}")
        self.proj.crt_anno.results.update({result.id: result})
        self.dockcnt_info.set_info_by_result(result)
        self.dockcnt_anno.set_row_by_text(result.id)
        self.canvas.set_item_state_by_result(result, update=False)

    def modify_results(self, results: list[RectangleResult | PolygonResult]):
        for r in results:
            self.modify_result(r)

    def add_annotation(self, anno: Annotation):
        if anno.key_label is None and len(anno.labels) > 0:
            anno.key_label = list(anno.labels.keys())[0]
        self.proj.key_task = anno.id
        self.proj.add_annotation(anno)

    def check_label_ok(self):
        if self.proj.crt_label is None:
            QMessageBox.critical(
                self,
                "Label Error",
                "Select a label first!",
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

    def restore_project(self):
        path = Path(self.settings.project_path)
        if not self.settings.project_name:
            self.dialog_settings.show()
            return
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            self.create_project()
        else:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.proj = Project.model_validate_json(f.read(), strict=True)
            except Exception as e:
                button = QMessageBox.critical(
                    self,
                    "Error",
                    f"Load project Error! {e=}, create new and overwrite?",
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Cancel,
                )
                if button == QMessageBox.StandardButton.Ok:
                    self.create_project()

    def restore_annotations(self):
        # restore annotations
        path = Path(self.settings.project_dir) / "annos"
        annos = list(path.glob(f"*.{self.anno_suffix}"))
        for p in annos:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    anno = Annotation.model_validate_json(f.read(), strict=True)
                self.add_annotation(anno)
            except Exception as e:
                self.logger.warning(f"validate {p=} failed with {e=}")
        self.proj.reset_task_key()

    def run_preupload_img_worker(self, image: Image.Image | None):
        if self.proj.crt_anno is None or image is None:
            return
        self.preupload_worker = ZPreuploadImageWorker(
            self.api_predict,
            self.proj.crt_anno.id,
            copy.deepcopy(image),
        )
        self.threadpool.start(self.preupload_worker)

    def show_toast(self, msg: str):
        toast = Toast(msg, timeout=1000, parent=self)
        toast.show()

    # endregion

    # region properties
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
        if self.sam_enabled and self.cv_enabled:
            mode = AutoMode.SAM & AutoMode.CV
        elif self.sam_enabled:
            mode = AutoMode.SAM
        elif self.cv_enabled:
            mode = AutoMode.CV
        return mode

    @property
    def sam_enabled(self) -> bool:
        return self.settings.value(SettingsKey.PROJ_SAM.value, False, type=bool)  # type: ignore

    @sam_enabled.setter
    def sam_enabled(self, v: bool):
        self.settings.setValue(SettingsKey.PROJ_SAM.value, v)

    @property
    def cv_enabled(self) -> bool:
        return self.settings.value(SettingsKey.PROJ_CV.value, False, type=bool)  # type: ignore

    @cv_enabled.setter
    def cv_enabled(self, v: bool):
        self.settings.setValue(SettingsKey.PROJ_CV.value, v)

    # endregion

    # region Slots
    def on_dialog_settings_changed(self, settings: QSettings):
        for k in settings.allKeys():
            self.settings.setValue(k, settings.value(k))

    def on_settings_color_changed(self, color: str):
        if self.proj.label_id is not None:
            self.on_dock_label_item_color_changed(self.proj.label_id, color)
            self.dockcnt_labels.set_color(color)

    def set_loglevel(self, level: str):
        self.logger.info(f"Setting loglevel to {level}")
        self.logger.setLevel(level)
        self.canvas.logger.setLevel(level)
        # self.api_alist.logger.setLevel(level)
        self.api_predict.logger.setLevel(level)

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

    def on_action_save_triggered(self):
        self.proj.save_json(self.settings.project_path)

    def on_action_undo_triggered(self):
        if self.undo_stack.canUndo():
            self.undo_stack.undo()

    def on_action_redo_triggered(self):
        if self.undo_stack.canRedo():
            self.undo_stack.redo()

    def on_action_visible_triggered(self):
        if self.actionVisible.isChecked():
            self.canvas.create_items_by_anno(self.proj.crt_anno)
        else:
            self.canvas.clear_all_items()

    def on_action_zoom_in_triggered(self):
        self.canvas.view_box.scaleBy((0.9, 0.9))

    def on_action_zoom_out_triggered(self):
        self.canvas.view_box.scaleBy((1.1, 1.1))

    def on_action_finish_triggered(self):
        if self.proj.crt_task is None or self.proj.crt_anno is None:
            return
        self.on_action_save_triggered()
        filename = f"{self.settings.project_dir}/annos/{self.proj.crt_anno.id}.{self.anno_suffix}"
        self.proj.crt_anno.save_json(filename)

        # if triggered by click, set task finished and upload
        if self.sender() == self.actionFinish:
            self.proj.crt_task.finished = True
            self.dockcnt_files.set_item_finished(self.proj.crt_task)
            self.worker_upload = ZUploadFileWorker(
                self.api_predict,
                filename,
                self.settings.username,
                self.settings.password,
            )
            self.worker_upload.emitter.fail.connect(self.show_toast)
            self.worker_upload.emitter.success.connect(self.show_toast)
            self.threadpool.start(self.worker_upload)

    def on_action_cancel_triggered(self):
        self.canvas.clear_all_items()
        self.dockcnt_anno.listWidget.clear()
        self.dockcnt_anno.listWidget.setCurrentRow(-1)
        self.dockcnt_info.set_info_by_anno(None)
        if self.proj.crt_anno:
            self.proj.crt_anno.reset_results()
        if self.proj.crt_task:
            self.proj.crt_task.finished = False
            self.dockcnt_files.set_item_unfinished(self.proj.crt_task)

    def on_action_SAM_triggered(self):
        self.sam_enabled = self.actionSAM.isChecked()
        msg = []
        if self.sam_enabled:
            msg.append("SAM")
        if self.cv_enabled:
            msg.append("OpenCV")
        if msg:
            self.show_toast("+".join(msg))

    def on_action_opencv_triggered(self):
        self.cv_enabled = self.actionOpenCV.isChecked()
        msg = []
        if self.sam_enabled:
            msg.append("SAM")
        if self.cv_enabled:
            msg.append("OpenCV")
        if msg:
            self.show_toast("+".join(msg))

    def on_action_move_triggered(self):
        for action in self.action_group_edit:
            action.setEnabled(action != self.actionMove)

        self.canvas.setStatusMode(StatusMode.VIEW)
        self.show_toast("Move Mode")

    def on_action_edit_triggered(self):
        for action in self.action_group_edit:
            action.setEnabled(action != self.actionEdit)

        self.canvas.setStatusMode(StatusMode.EDIT)
        self.show_toast(msg="Edit Mode")

    def on_action_rectangle_triggered(self):
        for action in self.action_group_edit:
            action.setEnabled(action != self.actionRectangle)

        self.canvas.setStatusMode(StatusMode.CREATE)
        self.canvas.setDrawMode(DrawMode.RECTANGLE)
        self.show_toast("Draw Rectangle")

    def on_action_point_triggered(self):
        for action in self.action_group_edit:
            action.setEnabled(action != self.actionPoint)

        self.canvas.setStatusMode(StatusMode.CREATE)
        self.canvas.setDrawMode(DrawMode.POINT)
        self.show_toast("Draw Point")

    def on_action_polygon_triggered(self):
        for action in self.action_group_edit:
            action.setEnabled(action != self.actionPolygon)

        self.canvas.setStatusMode(StatusMode.CREATE)
        self.canvas.setDrawMode(DrawMode.POLYGON)
        self.show_toast("Draw Polygon")

    def on_action_merge_triggered(self):
        self.canvas.merge_items(self.canvas.selected_items)

    def on_action_import_task_triggered(self):
        path = QFileDialog.getOpenFileName(
            self, "Select tasks", self.last_path, "Json Files(*.json)"
        )[0]
        if path:
            self.last_path = str(Path(path).absolute())
            self.settings.setValue(SettingsKey.TASKS.value, path)
            tasks = self.load_tasks(path)
            if tasks is None:
                return
            self.refresh_tasks(tasks)

    def on_cmbox_annotype_index_changed(self, index: int):
        if index < 0 or index >= len(self.annotation_types):
            return
        self.settings.annotation_type = index

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
    def on_dock_label_btn_add_clicked(self):
        txt = self.dockcnt_labels.ledit_add_label.text()
        if self.proj.crt_anno is None or txt == "":
            QMessageBox.warning(
                self,
                "Warning",
                "add label failed due to no selected task or empty label name!",
                QMessageBox.StandardButton.Ok,
            )
            return
        label = Label(id=id_uuid4(), name=txt, color=self.settings.color)
        self.proj.crt_anno.add_label(label)
        self.dockcnt_labels.add_label(label)

    def on_dock_label_btn_dec_clicked(self):
        row = self.dockcnt_labels.listw_labels.currentRow()
        item: ZListWidgetItem = self.dockcnt_labels.listw_labels.item(row)  # type: ignore
        self.dockcnt_labels.remove_label(row)
        if self.proj.crt_anno is not None:
            self.proj.crt_anno.remove_label(item.id_)
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    def on_dock_label_listw_item_clicked(self, item: ZListWidgetItem):
        if self.proj.crt_anno:
            self.proj.crt_anno.key_label = item.id_
            label = self.proj.crt_anno.labels[item.id_]
            for r in self.proj.crt_anno.results.values():
                r.labels = [label]
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    def on_dock_label_btn_del_clicked(self, id_: str):
        if self.proj.crt_anno:
            self.proj.crt_anno.remove_label(id_)
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    def on_dock_label_item_color_changed(self, id_: str, color: str):
        if self.proj.crt_anno:
            self.proj.crt_anno.labels[id_].color = color
            if id_ == self.proj.crt_anno.key_label:
                self.canvas.set_color(color)
                self.proj.crt_anno.set_color(color)
            self.logger.debug(f"Labels color changed: {self.proj.crt_anno.labels=}")
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    # endregion

    # region DockInfo
    ##### DockInfo #####
    def on_dock_info_ledit_note_changed(self, s: str):
        if self.proj.crt_result is None:
            self.logger.warning(f"Current Result is None, {self.proj.crt_anno=}")
            return
        self.proj.crt_result.note = s

    def on_dock_info_btn_del_clicked(self):
        self.canvas.remove_selected_items()
        if self.proj.crt_anno:
            self.proj.crt_anno.remove_result(self.proj.crt_anno.key_result)
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    # endregion

    # region DockAnnotation
    ##### DockAnnotation #####
    def on_dock_anno_listw_item_clicked(self, item: ZListWidgetItem):
        self.canvas.block_item_state_changed(True)
        self.canvas.select_item(item.id_)
        self.canvas.block_item_state_changed(False)

        if self.proj.crt_anno:
            self.proj.crt_anno.key_result = item.id_
            self.dockcnt_info.set_info_by_anno(self.proj.crt_anno)
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    def on_dock_anno_item_deleted(self, ids: list[str]):
        if self.proj.crt_anno:
            results = [self.proj.crt_anno.results[id_] for id_ in ids]
            self.add_result_undo_cmd(results, ResultUndoMode.REMOVE)
        else:
            self.logger.warning(f"Current anno is None, {self.proj.crt_task=}")

    # endregion

    # region DockFiles
    ##### DockFiles #####
    def on_dock_files_item_clicked(self, task_id: str):
        # save first
        self.on_action_finish_triggered()

        # set current annotation id to newly clicked
        self.proj.key_task = task_id
        if self.proj.crt_task is None:
            self.logger.warning(f"Current task is None, {self.proj.tasks=}")
            return

        # if the current anno is None:
        # 1. try to fetch from remote
        # 2. if not existed in remote, create
        if self.proj.crt_anno is None:
            task = self.proj.tasks[task_id]
            labels = OrderedDict()
            for name in task.labels:
                label = Label(id=id_uuid4(), name=name, color=self.settings.color)
                labels[label.id] = label
            try:
                name = f"{task.anno_id}.{self.anno_suffix}"
                anno_json = self.api_predict.get_zlabel(name=name)
                if anno_json is None:
                    raise Exception(f"Response of {name} is None")
                anno = Annotation.model_validate_json(anno_json, strict=True)
                self.add_annotation(anno)
                self.logger.info(f"Got anno from remote, added {name}")
            except Exception as e:
                self.add_annotation(
                    Annotation.new(
                        image_path=task.filename,
                        width=0,
                        height=0,
                        create_user=self.user,
                        id_=task.anno_id,
                        labels=labels,
                    )
                )
                self.logger.warning(
                    f"{task.anno_id=} not found in remote, created, {e=}"
                )

        self.try_set_image()

        # update ui
        # ^ hereafter, self.proj.crt_anno won't be None
        self.dockcnt_info.set_info_by_anno(self.proj.crt_anno)
        self.dockcnt_anno.add_items_by_anno(self.proj.crt_anno)
        self.dockcnt_anno.set_row_by_text(self.proj.key_result)
        self.dockcnt_anno.set_title()
        self.dockcnt_labels.set_labels(
            list(self.proj.crt_anno.labels.values()),  # type: ignore
            self.proj.crt_anno.key_label,  # type: ignore
        )
        self.dockcnt_labels.set_color(self.settings.color)

        # clear items in canvas
        self.canvas.update_by_anno(self.proj.crt_anno)

    def on_dock_files_fetch_tasks(self, num: int, finished: int):
        self.settings.fetch_num = num
        self.settings.fetch_finished = finished
        self.load_tasks_remote()

    # endregion

    # region Canvas
    def run_sam_api_worker(self, worker: ZSamPredictWorker):
        worker.emitter.sigFinished.connect(self.on_sam_worker_finished)
        self.threadpool.start(worker)

    def on_sam_worker_finished(self, worker_results: list[SamWorkerResult]):
        if len(worker_results) == 0:
            return
        results = [wr.result for wr in worker_results]
        self.proj.key_task = worker_results[0].anno_id
        # self.add_results(results)
        self.add_result_undo_cmd(results, ResultUndoMode.ADD)

    def on_canvas_point_created(self, point: QPointF):
        if (
            self.current_image is None
            or self.proj.crt_label is None
            or self.proj.key_task is None
        ):
            self.logger.warning(f"{self.proj.crt_label=}, {self.proj.key_task=}")
            return

        match self.auto_mode:
            case AutoMode.SAM | AutoMode.CV:
                ...
            case _:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "With point, you have to select SAM or CV",
                    QMessageBox.StandardButton.Ok,
                )
                return
        # TODO: if image already uploaded, ignore uploading image with points
        image_name = self.dockcnt_files.get_current_task_name()
        if not image_name:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select a task first!",
                QMessageBox.StandardButton.Ok,
            )
            return
        worker = ZSamPredictWorker(
            api=self.api_predict,
            anno_id=self.proj.key_task,
            image=image_name,
            points=[(point.x(), point.y())],
            labels=[1.0],
            threshold=self.threshold,
            mode=self.auto_mode,
            result_labels=[self.proj.crt_label],
            # anno_type=0 => RECT, 1 => POLYGON
            return_type=1 if self.settings.annotation_type == 0 else 2,
        )
        self.run_sam_api_worker(worker)

    def on_canvas_rectangle_created(self, item_state: dict[str, Any] | None):
        if (
            item_state is None
            or self.proj.key_task is None
            or self.current_image is None
        ):
            self.logger.warning(
                f"Wrong {item_state=} or {self.proj.key_task=} or current_image"
            )
            return
        self.logger.debug(f"Rectangle Created: {item_state=}")
        if not self.proj.crt_label:
            QMessageBox.warning(
                self,
                "Warning",
                "Select a label first!",
                QMessageBox.StandardButton.Ok,
            )
            return

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
        )
        self.logger.debug(f"{result=}")
        match self.auto_mode:
            # if neither SAM nor CV selected, means create rect manually
            case AutoMode.MANUAL:
                self.add_result_undo_cmd([result], ResultUndoMode.ADD)
                return
            # if either sam or CV selected, create by predict
            case AutoMode.SAM | AutoMode.CV:
                ...
            case x if x == AutoMode.SAM & AutoMode.CV:
                ...
            case _:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "AutoMode error",
                    QMessageBox.StandardButton.Ok,
                )
                return

        image_name = self.dockcnt_files.get_current_task_name()
        if not image_name:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select a task first!",
                QMessageBox.StandardButton.Ok,
            )
            return

        worker = ZSamPredictWorker(
            api=self.api_predict,
            anno_id=self.proj.key_task,
            image=image_name,
            rects=[(result.x, result.y, result.w, result.h)],
            threshold=self.threshold,
            mode=self.auto_mode,
            result_labels=[self.proj.crt_label],
            # anno_type=0 => RECT, 1 => POLYGON
            return_type=1 if self.settings.annotation_type == 0 else 2,
        )
        self.run_sam_api_worker(worker)

    def on_canvas_item_clicked(self, id_: str):
        if self.proj.crt_anno is None:
            return
        self.proj.key_result = id_
        self.dockcnt_anno.set_row_by_text(id_)
        self.dockcnt_info.set_info_by_result(self.proj.crt_result)

    def on_canvas_item_state_changed(self, state: dict[str, Any]):
        if self.proj.crt_result is None:
            return
        result: RectangleResult | PolygonResult = copy.deepcopy(self.proj.crt_result)
        result.x = state["pos"].x()
        result.y = state["pos"].y()
        result.w = state["size"].x()
        result.h = state["size"].y()
        result.rotation = state["angle"]
        if isinstance(result, PolygonResult):
            result.closed = state["closed"]
            result.points = state["points"]
        # self.add_result_undo_cmd([result], ResultUndoMode.MODIFY)

        self.dockcnt_info.set_info_by_result(result)
        self.dockcnt_anno.set_row_by_text(result.id)
        # self.logger.debug(self.current_result)

    def on_canvas_item_state_change_finished(self, state: dict[str, Any]):
        if self.proj.crt_result is None:
            return
        result: RectangleResult | PolygonResult = copy.deepcopy(self.proj.crt_result)
        result_old: RectangleResult | PolygonResult = copy.deepcopy(
            self.proj.crt_result
        )
        if isinstance(result, RectangleResult):
            result.x = state["pos"].x()
            result.y = state["pos"].y()
            result.w = state["size"].x()
            result.h = state["size"].y()
            result.rotation = state["angle"]
        elif isinstance(result, PolygonResult):
            result.points = [(p.x(), p.y()) for p in state["points"]]
        if not result.equal_v(result_old):
            self.logger.debug("Adding modify undo command")
            self.add_result_undo_cmd([result], ResultUndoMode.MODIFY, [result_old])

    def on_canvas_items_removed(self, ids: list[str]):
        if self.proj.crt_anno is None:
            return
        results = [self.proj.crt_anno.results[i] for i in ids]
        self.add_result_undo_cmd(results, ResultUndoMode.REMOVE)
        # self.remove_results(ids)
        self.dockcnt_anno.remove_items(ids)
        self.dockcnt_info.set_info_by_anno(self.proj.crt_anno)

    def on_canvas_scene_mouse_moved(self, pos: QPointF):
        x, y = pos.x(), pos.y()
        self.statusbar.showMessage(f"{x:.2f}, {y:.2f}")

    # endregion
    # endregion

    # region INIT
    def init_ui(self):
        self.dialog_settings = DialogSettings(self.settings_path, self)
        self.dialog_about = DialogAbout(self)
        self.dialog_processing = DialogProcessing(self)
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
        ]
        self.cmbox_anno_type = QComboBox(self)
        for anno_type, icon_path in self.annotation_types:
            icon = QIcon()
            icon.addFile(icon_path, QSize(), QIcon.Mode.Normal, QIcon.State.Off)
            self.cmbox_anno_type.addItem(icon, anno_type)
        self.cmbox_anno_type.setCurrentIndex(self.settings.annotation_type)
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
        self.toolBar.addWidget(self.cmbox_rgb)

        self.slider_threshold = ZSlider(Qt.Orientation.Horizontal, self)
        self.slider_threshold.setValue(self.threshold)
        self.slider_threshold.setStatusTip("Set Threshold")
        self.slider_threshold.setToolTip("Set Threshold")
        self.slider_threshold.setMaximumSize(150, 20)
        self.toolBar.addWidget(self.slider_threshold)

    def init_signals(self):
        # dialog
        self.dialog_settings.sigSettingsChanged.connect(self.on_dialog_settings_changed)
        self.dialog_settings.sigApplyClicked.connect(self.load_settings)
        self.dialog_settings.destroyed.connect(self.dialog_processing.close)
        self.dialog_settings.sigLoglevelChanged.connect(self.set_loglevel)
        self.dialog_settings.sigColorChanged.connect(self.on_settings_color_changed)
        # actions
        self.actionSettings.triggered.connect(self.dialog_settings.show)
        self.actionAbout.triggered.connect(self.dialog_about.show)
        self.actionExit.triggered.connect(self.close)

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

        self.action_import_task.triggered.connect(self.on_action_import_task_triggered)

        self.cmbox_anno_type.currentIndexChanged.connect(
            self.on_cmbox_annotype_index_changed
        )
        self.cmbox_rgb.currentIndexChanged.connect(self.on_cmbox_rgb_index_changed)

        # self.btn_online_mode.sigCheckStateChanged.connect(self.on_btn_online_mode_check_changed)
        self.slider_threshold.valueChanged.connect(self.on_slider_threshold_changed)

        # canvas
        self.canvas.sigPointCreated.connect(self.on_canvas_point_created)
        self.canvas.sigRectangleCreated.connect(self.on_canvas_rectangle_created)
        self.canvas.sigItemClicked.connect(self.on_canvas_item_clicked)
        self.canvas.sigItemStateChanged.connect(self.on_canvas_item_state_changed)
        self.canvas.sigItemStateChangeFinished.connect(
            self.on_canvas_item_state_change_finished
        )
        self.canvas.sigItemsRemoved.connect(self.on_canvas_items_removed)
        self.canvas.sigMouseMoved.connect(self.on_canvas_scene_mouse_moved)
        self.canvas.sigMouseBackClicked.connect(self.actionPrev.trigger)
        self.canvas.sigMouseForwardClicked.connect(self.actionNext.trigger)

        # dock info
        self.dockcnt_info.ledit_anno_note.textChanged.connect(
            self.on_dock_info_ledit_note_changed
        )
        self.dockcnt_info.btn_delete_anno.clicked.connect(
            self.on_dock_info_btn_del_clicked
        )

        # dock files
        self.dockcnt_files.sigItemClicked.connect(self.on_dock_files_item_clicked)
        self.dockcnt_files.sigFetchTasks.connect(self.on_dock_files_fetch_tasks)

        # dock labels
        self.dockcnt_labels.listw_labels.itemClicked.connect(
            self.on_dock_label_listw_item_clicked
        )
        self.dockcnt_labels.btn_decrease.clicked.connect(
            self.on_dock_label_btn_dec_clicked
        )
        self.dockcnt_labels.btn_increase.clicked.connect(
            self.on_dock_label_btn_add_clicked
        )
        # self.dockcnt_labels.ledit_add_label.editingFinished.connect(
        #     self.on_dock_label_btn_add_clicked
        # )
        self.dockcnt_labels.sigBtnDeleteClicked.connect(
            self.on_dock_label_btn_del_clicked
        )
        self.dockcnt_labels.sigItemColorChanged.connect(
            self.on_dock_label_item_color_changed
        )

        # dock annotations
        self.dockcnt_anno.listWidget.itemClicked.connect(
            self.on_dock_anno_listw_item_clicked
        )
        self.dockcnt_anno.sigItemDeleted.connect(self.on_dock_anno_item_deleted)
        self.dockcnt_anno.sigItemCountChanged.connect(
            lambda n: self.dock_annos.setWindowTitle(f"Annos ({n} items)")
        )

    # endregion

    # region events

    # endregion
