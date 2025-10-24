import functools
import glob
import hashlib
import json
import os
from collections import OrderedDict, namedtuple
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Tuple

import numpy as np
import pyqtgraph as pg
from numpy.typing import NDArray
from PIL import Image
from qtpy.QtCore import QPointF, QRectF, Qt, QThread, QTranslator, Signal, Slot, QPoint, QSettings
from qtpy.QtGui import (
    QAction,
    QUndoStack,
    QUndoCommand,
    QCloseEvent,
    QColor,
    QIcon,
    QImageReader,
    QKeySequence,
    QMouseEvent,
    QPen,
    QPixmap,
    QShortcut,
)
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsWidget,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QDialogButtonBox,
)
from zlabel.models.sam_onnx import SamOnnxModel
from zlabel.models.types import SamOnnxEncodedInput

from zlabel.utils.enums import AutoMode, DrawMode, SettingsKey, StatusMode
from zlabel.utils.logger import ZLogger
from zlabel.widgets.dialog_new_proj import DialogNewProject
from zlabel.widgets.dialog_processing import DialogProcessing
from zlabel.widgets.switch_button import SwitchBtn
from zlabel.widgets.zundostack import ResultUndoMode, ZResultUndoCmd
from zlabel.widgets.zwidgets import ZListWidgetItem, ZSlider, ZSwitchButton
from zlabel.widgets.zworker import SamWorkerResult, ZSamEncodeWorker, ZSamWorker

from ..utils.project import Annotation, Label, Project, Result, ResultType, User, id_md5, id_uuid4, ResultStep, Stack
from . import (
    DialogAbout,
    DialogSettings,
)
from .graphic_objects import Polygon, Rectangle
from .ui import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.logger = ZLogger("MainWindow")
        self.settings = QSettings("zlabel.ini", QSettings.Format.IniFormat)
        # DEBUG
        self.settings.setValue(SettingsKey.PROJECT_PATH.value, r"C:\DEV\python\zlabel_sam\imgs")
        self.user_default = User.default()
        self.label_default = Label.default()

        self.proj: Project = Project.new(
            project_path=r"C:\DEV\python\zlabel_sam\imgs",
            name="test",
            description="test",
            users=OrderedDict({self.user_default.id: self.user_default}),
            labels=OrderedDict({self.label_default.id: self.label_default}),
            annotations=None,
        )

        self.undo_stack = QUndoStack(self)

        self._is_sam_enabled = True
        self._is_cv_enabled = False
        self._is_online_mode = False
        self._project_name = "project.zproj"

        self.anno_suffix = "zlabel"
        self.img_suffix = [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]
        self.threshold = 100

        self.sam_onnx_encoder_path: str = "data/sam_vit_b_encoder_quantized.onnx"
        self.sam_onnx_decoder_path: str = "data/sam_vit_b_decoder_quantized.onnx"
        self.sam_model: SamOnnxModel | None = None
        self.worker_thread = None
        self.sam_worker = None

        self.setupUi(self)
        self.init_ui()
        self.init_signals()
        self.load_model()

    # region properties
    @property
    def anno_id(self):
        return self.proj.key_anno

    @anno_id.setter
    def anno_id(self, id_: str):
        assert id_ in self.proj.annotations, f"key {id_} must in existed annotations"
        self.proj.key_anno = id_

    @property
    def label_id(self):
        return self.proj.key_label

    @label_id.setter
    def label_id(self, id_: str):
        assert id_ in self.proj.labels, f"label key {id_} not in labels: {self.proj.labels=}"
        self.proj.key_label = id_

    @property
    def user_id(self):
        return self.proj.key_user

    @user_id.setter
    def user_id(self, id_: str):
        assert id_ in self.proj.users, f"{id_=}, {self.proj.users=}"
        self.proj.key_user = id_

    @property
    def result_id(self):
        if self.current_annotation:
            return self.current_annotation.result_key
        return None

    @result_id.setter
    def result_id(self, id_: str):
        if self.current_annotation and id_ in self.current_annotation.results:
            self.proj.annotations[self.anno_id].result_key = id_
        else:
            self.logger.error(f"{id_=} not in results, ensure that you have created it!")

    @property
    def annotations(self):
        return self.proj.annotations

    @property
    def labels(self):
        return self.proj.labels

    @property
    def current_label(self) -> Label | None:
        return self.proj.current_label

    @property
    def current_annotation(self) -> Annotation | None:
        return self.proj.current_annotation

    @current_annotation.setter
    def current_annotation(self, anno: Annotation | None):
        """
        if anno is None, clear results of current annotation
        if anno is not None and anno.id in self.annotations, set current annotation id to anno.id
        if anno is not None and anno.id not in self.annotations, add anno to current annotation
        """
        if anno is None:
            self.proj.annotations[self.anno_id].results.clear()
            return
        if self.current_annotation and anno.id == self.current_annotation.id:
            return
        if anno.id in self.annotations:
            self.anno_id = anno.id
            return
        self.proj.add_annotation(anno)

    @property
    def current_result(self):
        return self.proj.current_result

    @current_result.setter
    def current_result(self, r: Result):
        if r is None:
            self.logger.warning(f"{r=}, skipping...")
            return
        if self.current_annotation and r.id in self.current_annotation.results:
            self.proj.annotations[self.anno_id].result_key = r.id
            return
        self.logger.debug(f"Adding {r=}")
        self.add_result_undo_cmd([r], ResultUndoMode.ADD)

    @property
    def current_user(self):
        return self.proj.current_user

    @current_user.setter
    def current_user(self, user: User):
        ids = [u.id for u in self.proj.users.values()]
        if user.id in ids:
            self.user_id = user.id

    @property
    def image_paths(self):
        return self.proj.image_paths

    @property
    def current_image(self) -> NDArray | None:
        img = self.canvas.current_image
        if img is None:
            QMessageBox.warning(
                self,
                "Warning",
                "Please load image first",
                QMessageBox.StandardButton.Ok,
            )
        return img

    @property
    def project_path(self):
        return self.proj.project_path

    @project_path.setter
    def project_path(self, p: str):
        self.proj.project_path = p

    @property
    def is_model_loaded(self):
        return self.sam_model is not None

    @property
    def auto_mode(self):
        mode = AutoMode.MANUAL
        if self._is_sam_enabled and self._is_cv_enabled:
            mode = AutoMode.SAM & AutoMode.CV
        elif self._is_sam_enabled:
            mode = AutoMode.SAM
        elif self._is_cv_enabled:
            mode = AutoMode.CV
        return mode

    # endregion
    # region functions
    def set_image(self, path: str | None = None):
        path = path or self.proj.current_image_path
        if not path:
            return
        self.canvas.clear_image()
        self.canvas.setImage(path)

        if self.sam_model is not None and self.current_image is not None:
            key = hashlib.md5(self.current_image.tobytes()).hexdigest()
            if not self.sam_model.key_cached(key):
                self.encode_thread = QThread()
                self.worker_encode = ZSamEncodeWorker(self.sam_model, self.current_image)
                self.worker_encode.moveToThread(self.encode_thread)

                self.encode_thread.started.connect(self.dialog_processing.show)
                self.encode_thread.started.connect(self.worker_encode.run)
                self.encode_thread.finished.connect(self.encode_thread.deleteLater)

                self.worker_encode.sigFinished.connect(self.on_worker_encode_finished)
                self.worker_encode.sigFinished.connect(self.encode_thread.quit)
                self.worker_encode.sigFinished.connect(self.worker_encode.deleteLater)
                self.encode_thread.start()

            # self.sam_model.encode(self.current_image)

    def on_worker_encode_finished(self, r: Tuple[str, SamOnnxEncodedInput]):
        self.sam_model.add_encoded_input(r[0], r[1])  # type: ignore
        self.dialog_processing.hide()
        self.statusbar.showMessage("Image load success, start now!")

    def load_project(self):
        proj_path = self.settings.value(SettingsKey.PROJECT_PATH.value, "")
        path = Path(str(proj_path))
        if not path.exists():
            self.dialog_new_proj.show()
        else:
            zproj = list(path.glob("*.zproj"))
            if len(zproj) == 0:
                self.dialog_new_proj.show()
            try:
                with open(zproj[0], "r", encoding="utf-8") as f:
                    self.proj = Project.model_validate_json(f.read())
            except Exception as e:
                self.logger.error(f"Load project file {zproj[0]} Failed, Check it!\n{e=}")
        if self.proj is not None:
            self.refresh_image_paths()
            self.refresh_annotations()

    def set_image_paths(self, paths: List[str], clear=False):
        if clear:
            self.proj.annotations.clear()
        for i, p in enumerate(paths):
            id_ = id_md5(p)
            if id_ in self.proj.annotations:
                continue
            try:
                img = Image.open(p)
                self.proj.add_annotation(
                    Annotation.new(
                        p,
                        img.width,
                        img.height,
                        self.current_user,
                        id_=id_md5(p),
                        anno_suffix=self.anno_suffix,
                    )
                )
            except Exception:
                continue

    def refresh_image_paths(self, clear=False):
        paths = Path(self.project_path).glob("*")
        ppaths = [str(pp) for pp in paths if pp.suffix in self.img_suffix]
        self.set_image_paths(ppaths, clear)
        keys = list(self.annotations.keys())
        # self.anno_id = keys[0] if keys else ""

    def load_model(self):
        if os.path.exists(self.sam_onnx_encoder_path) and os.path.exists(self.sam_onnx_decoder_path):
            self.sam_model = SamOnnxModel(
                encoder_path=self.sam_onnx_encoder_path,
                decoder_path=self.sam_onnx_decoder_path,
            )
            return True
        else:
            QMessageBox.critical(
                self,
                "Model Error",
                "Model files not found",
                QMessageBox.StandardButton.Ok,
            )
            return False

    def add_result(self, result: Result):
        self.proj.annotations[self.anno_id].add_result(result)
        # if result.origin != "manual":
        self.canvas.create_item_by_result(result)
        self.dockcnt_info.set_info_by_result(result)
        self.dockcnt_anno.add_item(result.id)

    def add_results(self, results: List[Result]):
        for result in results:
            self.add_result(result)

    def add_result_undo_cmd(self, results: List[Result], mode: ResultUndoMode):
        cmd = ZResultUndoCmd(self, results, mode)
        self.undo_stack.push(cmd)

    def remove_result(self, id_: str):
        if id_ not in self.current_annotation.results:  # type: ignore
            self.logger.debug(f"{id_=}, {self.current_annotation.results.keys()=}")  # type: ignore
            return
        self.proj.annotations[self.anno_id].remove_result(id_)
        self.canvas.remove_items_by_ids([id_])
        self.dockcnt_anno.remove_item(id_)

    def remove_results(self, ids: List[str]):
        for id_ in ids:
            self.remove_result(id_)

    def update_ui(self):
        self.set_image()

    def check_model_ok(self):
        if self.sam_model is None:
            QMessageBox.critical(
                self,
                "Model Error",
                "Model is not loaded!",
                QMessageBox.StandardButton.Ok,
            )
            return False
        return True

    def check_label_ok(self):
        if self.current_label is None:
            QMessageBox.critical(
                self,
                "Label Error",
                "Select a label first!",
                QMessageBox.StandardButton.Ok,
            )
            return False
        return True

    def is_current_anno_ok(self):
        anno = self.current_annotation
        if anno is None:
            self.logger.warning(f"current annotation is None, {self.proj=}")
            return False
        return True

    def is_current_result_ok(self):
        result = self.current_result
        if result is None:
            self.logger.warning("current result is None")
            return False
        return True

    def is_current_anno_result_ok(self):
        return self.is_current_anno_ok() and self.is_current_result_ok()

    def restore_annotations(self):
        # restore annotations
        anno = self.current_annotation
        if anno:
            for result in anno.results.values():
                if result.type_id == ResultType.RECTANGLE:
                    rect = QRectF(result.x, result.y, result.w, result.h)
                    item = Rectangle(
                        rect=rect,
                        color=result.labels[0].color,
                        movable=True,
                    )
                    self.canvas.addItem(item)
                else:
                    raise NotImplementedError

    def refresh_annotations(self):
        path = Path(self.project_path)
        anno_paths = path.glob(f"*.{self.anno_suffix}")
        for p in anno_paths:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    anno = Annotation.model_validate_json(f.read())
                self.proj.add_annotation(anno)
            except Exception as e:
                self.logger.critical(f"load {p=} failed, error: {e=}")
        self.logger.info(f"Loaded Finished!\n Annotations: {len(self.annotations)}")

    # def on_current_result_changed(self):
    #     self.dockcnt_info.set_info_by_anno(self.current_annotation)

    #     if self.is_current_anno_ok():
    #         self.dockcnt_anno.set_row_by_text(self.result_id)

    # endregion

    # region Slots
    def on_dialog_new_proj_clicked(self, btn: QPushButton):
        if btn == self.dialog_new_proj.btn_ok:
            self.settings.setValue(SettingsKey.PROJECT_PATH.value, self.dialog_new_proj.proj_path)
            user = User(
                id=id_uuid4(), name=self.dialog_new_proj.proj_user_name, email=self.dialog_new_proj.proj_user_email
            )
            self.proj = Project.new(
                self.dialog_new_proj.proj_path,
                self.dialog_new_proj.proj_name,
                self.dialog_new_proj.proj_description,
                users=OrderedDict({user.id: user}),
            )
        elif btn == self.dialog_new_proj.btn_cancel:
            ...

    # region Slots Actions
    def on_action_open_dir_triggered(self):
        directory = QFileDialog.getExistingDirectory(self, "Open Directory")
        path = Path(directory)
        if path.exists():
            zprojs = list(path.glob("*.zproj"))
            if len(zprojs) == 0:
                self.dialog_new_proj.show()
            else:
                ...
            self.project_path = directory
            self.refresh_image_paths(clear=True)
            self.refresh_annotations()
            self.dockcnt_files.update_file_list(self.image_paths)
            self.logger.debug(f"{self.proj.current_image_idx=}")

    def on_action_next_prev_triggered(self):
        row = self.dockcnt_files.listw_files.currentRow()
        if self.sender() == self.actionNext:
            row += 1
        else:
            row -= 1
        if row < 0 or row >= self.dockcnt_files.listw_files.count():
            return
        self.dockcnt_files.listw_files.setCurrentRow(row)
        item = self.dockcnt_files.listw_files.item(row)
        self.dockcnt_files.update_labels()
        self.on_dock_files_item_clicked(item)  # type: ignore

    def on_action_save_triggered(self):
        self.proj.save_json(f"{self.proj.name}.zproj")

    def on_action_undo_triggered(self):
        if self.undo_stack.canUndo():
            self.undo_stack.undo()

    def on_action_redo_triggered(self):
        if self.undo_stack.canRedo():
            self.undo_stack.redo()

    def on_action_visible_triggered(self):
        if self.actionVisible.isChecked():
            self.canvas.clear_all_items()
        else:
            self.canvas.create_items_by_anno(self.current_annotation)

    def on_action_zoom_in_triggered(self):
        self.canvas.view_box.scaleBy((0.9, 0.9))

    def on_action_zoom_out_triggered(self):
        self.canvas.view_box.scaleBy((1.1, 1.1))

    def on_action_finish_triggered(self):
        self.on_action_save_triggered()
        if self.current_annotation is None:
            return
        self.current_annotation.save_json()

    def on_action_cancel_triggered(self):
        self.canvas.clear_all_items()
        self.dockcnt_anno.listWidget.clear()
        self.dockcnt_anno.listWidget.setCurrentRow(-1)
        self.dockcnt_info.set_info_by_anno(None)
        self.current_annotation = None

    def on_action_SAM_triggered(self):
        # TODO implement SAM and OpenCV
        checked = self.actionSAM.isChecked()
        self._is_sam_enabled = checked

    def on_action_opencv_triggered(self):
        checked = self.actionOpenCV.isChecked()
        self._is_cv_enabled = checked

    def on_action_move_triggered(self):
        self.actionEdit.setEnabled(True)
        self.actionMove.setEnabled(False)
        self.actionRectangle.setEnabled(True)
        self.actionPoint.setEnabled(True)

        self.canvas.setStatusMode(StatusMode.VIEW)

    def on_action_edit_triggered(self):
        self.actionEdit.setEnabled(False)
        self.actionMove.setEnabled(True)
        self.actionRectangle.setEnabled(True)
        self.actionPoint.setEnabled(True)

        self.canvas.setStatusMode(StatusMode.EDIT)

    def on_action_rectangle_triggered(self):
        self.actionMove.setEnabled(True)
        self.actionEdit.setEnabled(True)
        self.actionRectangle.setEnabled(False)
        self.actionPoint.setEnabled(True)

        self.canvas.setStatusMode(StatusMode.CREATE)
        self.canvas.setDrawMode(DrawMode.RECTANGLE)

    def on_action_point_triggered(self):
        self.actionMove.setEnabled(True)
        self.actionEdit.setEnabled(True)
        self.actionRectangle.setEnabled(True)
        self.actionPoint.setEnabled(False)

        self.canvas.setStatusMode(StatusMode.CREATE)
        self.canvas.setDrawMode(DrawMode.POINT)

    def on_action_polygon_triggered(self):
        self.canvas.setStatusMode(StatusMode.CREATE)
        self.canvas.setDrawMode(DrawMode.POLYGON)

    def on_btn_online_mode_check_changed(self, checked: bool):
        self._is_online_mode = checked

    def on_slider_threshold_changed(self, v: int):
        self.threshold = v

    # endregion

    # region DockLabel
    def on_dock_label_btn_add_clicked(self):
        txt = self.dockcnt_labels.ledit_add_label.text()
        if self.proj is None or txt == "":
            return
        label = Label(id=id_uuid4(), name=txt)
        self.proj.add_label(label)
        self.dockcnt_labels.add_label(label)

    def on_dock_label_btn_dec_clicked(self):
        row = self.dockcnt_labels.listw_labels.currentRow()
        item: ZListWidgetItem = self.dockcnt_labels.listw_labels.item(row)  # type: ignore
        self.dockcnt_labels.remove_label(row)
        self.proj.labels.pop(item.id_)

    def on_dock_label_listw_item_clicked(self, item: ZListWidgetItem):
        self.label_id = item.id_

    def on_dock_label_btn_del_clicked(self, id_: str):
        self.proj.labels.pop(id_)

    def on_dock_label_item_color_changed(self, id_: str, color: str):
        self.proj.labels[id_].color = color
        self.canvas.color = color
        self.logger.debug(self.proj.labels)

    # endregion

    # region DockInfo
    ##### DockInfo #####
    def on_dock_info_ledit_note_changed(self, s: str):
        if self.current_result is None:
            return
        idx_result = self.current_annotation.crt_result_idx  # type: ignore
        self.proj.annotations[self.anno_id].results[idx_result].note = s

    def on_dock_info_cbox_user_changed(self, value: int):
        name = self.dockcnt_info.cbox_users.itemText(value)
        for k in self.proj.users:
            user = self.proj.users[k]
            if user.name == name:
                self.user_id = user.id
                break

    def on_dock_info_btn_del_clicked(self):
        self.canvas.remove_selected_item()

    # endregion

    # region DockAnnotation
    ##### DockAnnotation #####
    def on_dock_anno_listw_item_clicked(self, item: ZListWidgetItem):
        self.result_id = item.id_
        self.canvas.select_item(item.id_)
        self.dockcnt_info.set_info_by_anno(self.current_annotation)

    def on_dock_anno_item_deleted(self, ids: List[str]):
        results = [self.current_annotation.results[id_] for id_ in ids]  # type: ignore
        # self.remove_results(ids)
        self.add_result_undo_cmd(results, ResultUndoMode.REMOVE)

    # endregion

    # region DockFiles
    ##### DockFiles #####
    def on_dock_files_item_clicked(self, item: ZListWidgetItem):
        # save first
        self.on_action_save_triggered()
        self.on_action_finish_triggered()

        # set current annotation id to newly clicked
        self.anno_id = item.id_
        anno = self.current_annotation

        # update ui
        self.set_image()
        self.dockcnt_info.set_info_by_anno(anno)
        self.dockcnt_anno.add_items_by_anno(anno)
        self.dockcnt_anno.set_row_by_text(self.result_id)

        # clear items in canvas
        self.canvas.clear_all_items()
        if anno is not None:
            self.canvas.create_items_by_anno(anno)

    def on_dock_files_ledit_jump_changed(self, s: str):
        try:
            row = int(s) - 1
            item = self.dockcnt_files.listw_files.item(row)
            self.on_dock_files_item_clicked(item)  # type: ignore
        except Exception as e:
            self.logger.debug(f"{type(s)=}, {e=}")

    # endregion

    # region Canvas
    def on_sam_worker_finished(self, worker_results: List[SamWorkerResult]):
        if len(worker_results) == 0:
            return
        results = [wr.result for wr in worker_results]
        self.anno_id = worker_results[0].anno_id
        # self.add_results(results)
        self.add_result_undo_cmd(results, ResultUndoMode.ADD)

    def on_canvas_point_created(self, point: QPointF):
        if not self.check_model_ok():
            return
        if not self.check_label_ok():
            return

        if self.current_image is None:
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
        self.sam_worker = ZSamWorker(
            model=self.sam_model,  # type: ignore
            anno_id=self.anno_id,
            result_labels=[self.current_label],  # type: ignore
            img=self.current_image,
            points=[(point.x(), point.y())],
            labels=[1.0],
            result_type=ResultType.POINT,
            auto_mode=self.auto_mode,
            threshold=self.threshold,
        )
        self.worker_thread = QThread(self)
        self.sam_worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.sam_worker.run)
        self.sam_worker.sigFinished.connect(self.worker_thread.quit)
        self.sam_worker.sigFinished.connect(self.sam_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.sam_worker.sigFinished.connect(self.on_sam_worker_finished)
        self.worker_thread.start()

    def on_canvas_rectangle_created(self, item: Rectangle | None):
        self.logger.debug(f"Rectangle Created: {item}")
        if item is None:
            return
        if not self.current_label:
            self.canvas.remove_item(item)
            QMessageBox.warning(
                self,
                "Warning",
                "Select a label first!",
                QMessageBox.StandardButton.Ok,
            )
            return
        match item:
            case Rectangle():
                d = item.getState()
                result = Result.new(
                    id_=item.id,
                    type_id=ResultType.RECTANGLE,
                    x=d["pos"].x(),
                    y=d["pos"].y(),
                    w=d["size"].x(),
                    h=d["size"].y(),
                    rotation=d["angle"],
                    labels=[self.current_label],
                    score=1.0,
                )
            case _:
                raise NotImplementedError
        self.logger.debug(f"{result=}")
        # self.add_result(result)
        self.add_result_undo_cmd([result], ResultUndoMode.ADD)

        self.dockcnt_anno.add_item(result.id)
        self.dockcnt_info.set_info_by_result(result)

    def on_canvas_item_clicked(self, id_: str):
        if not self.is_current_anno_ok():
            return
        self.result_id = id_
        self.dockcnt_anno.set_row_by_text(id_)
        self.dockcnt_info.set_info_by_result(self.current_result)

    def on_canvas_item_state_changed(self, item: Rectangle | Polygon):
        if not self.is_current_anno_result_ok():
            return
        result: Result = self.current_result  # type: ignore
        state = item.getState()
        result.x = state["pos"].x()
        result.y = state["pos"].y()
        result.w = state["size"].x()
        result.h = state["size"].y()
        result.rotation = state["angle"]
        self.current_result = result

        self.dockcnt_info.set_info_by_result(result)
        self.dockcnt_anno.set_row_by_text(result.id)
        # self.logger.debug(self.current_result)

    def on_canvas_items_removed(self, items: List[Rectangle | Polygon]):
        if not self.is_current_anno_ok():
            return
        ids = [item.id for item in items]

        results = [self.current_annotation.results[i] for i in ids]  # type: ignore
        self.add_result_undo_cmd(results, ResultUndoMode.REMOVE)
        # self.remove_results(ids)
        self.dockcnt_anno.remove_items(ids)
        self.dockcnt_info.set_info_by_anno(self.current_annotation)

    def on_canvas_scene_mouse_moved(self, pos: QPointF):
        x, y = pos.x(), pos.y()
        self.statusbar.showMessage(f"{x:.2f}, {y:.2f}")

    # endregion
    # endregion

    # region INIT
    def init_ui(self):
        self.dialog_settings = DialogSettings(self)
        self.dialog_about = DialogAbout(self)
        self.dialog_processing = DialogProcessing(self)
        self.dialog_new_proj = DialogNewProject(self)
        self.actionSAM.setChecked(self._is_sam_enabled)
        self.actionOpenCV.setChecked(self._is_cv_enabled)

        self.btn_online_mode = ZSwitchButton(self)
        self.btn_online_mode.setStatusTip("Switch Online Mode")
        self.btn_online_mode.setToolTip("Switch Online Mode")
        self.toolBar.addWidget(self.btn_online_mode)

        self.slider_threshold = ZSlider(Qt.Orientation.Horizontal, self)
        self.slider_threshold.setValue(self.threshold)
        self.slider_threshold.setStatusTip("Set Threshold")
        self.slider_threshold.setToolTip("Set Threshold")
        self.slider_threshold.setMaximumSize(100, 20)
        self.toolBar.addWidget(self.slider_threshold)

        self.refresh_image_paths(clear=True)
        self.label_id = self.label_default.id
        self.user_id = self.user_default.id

        self.dockcnt_files.update_file_list(self.image_paths)

        self.dockcnt_info.set_info_by_anno(self.current_annotation)

        if self.current_annotation:
            self.dockcnt_anno.add_items(list(self.current_annotation.results.keys()))

        self.dockcnt_labels.set_labels(list(self.labels.values()), self.label_id)

        self.set_image()

    def init_signals(self):
        # dialog
        self.dialog_new_proj.buttonBox.clicked.connect(self.on_dialog_new_proj_clicked)
        # actions
        self.actionOpen_dir.triggered.connect(self.on_action_open_dir_triggered)
        self.actionSettings.triggered.connect(self.dialog_settings.show)
        self.actionAbout.triggered.connect(self.dialog_about.show)

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

        self.actionFinish.triggered.connect(self.on_action_finish_triggered)
        self.actionCancel.triggered.connect(self.on_action_cancel_triggered)
        self.actionSave.triggered.connect(self.on_action_save_triggered)

        self.actionVisible.triggered.connect(self.on_action_visible_triggered)
        self.actionZoom_in.triggered.connect(self.on_action_zoom_in_triggered)
        self.actionZoom_out.triggered.connect(self.on_action_zoom_out_triggered)

        self.btn_online_mode.sigCheckStateChanged.connect(self.on_btn_online_mode_check_changed)
        self.slider_threshold.valueChanged.connect(self.on_slider_threshold_changed)

        # canvas
        self.canvas.sigPointCreated.connect(self.on_canvas_point_created)
        self.canvas.sigRectangleCreated.connect(self.on_canvas_rectangle_created)
        self.canvas.sigItemClicked.connect(self.on_canvas_item_clicked)
        self.canvas.sigItemStateChanged.connect(self.on_canvas_item_state_changed)
        self.canvas.sigItemsRemoved.connect(self.on_canvas_items_removed)
        self.canvas.sigMouseMoved.connect(self.on_canvas_scene_mouse_moved)

        # dock info
        self.dockcnt_info.cbox_users.currentIndexChanged.connect(self.on_dock_info_cbox_user_changed)
        self.dockcnt_info.ledit_anno_note.textChanged.connect(self.on_dock_info_ledit_note_changed)
        self.dockcnt_info.btn_delete_anno.clicked.connect(self.on_dock_info_btn_del_clicked)

        # dock files
        self.dockcnt_files.listw_files.itemClicked.connect(self.on_dock_files_item_clicked)
        self.dockcnt_files.ledit_jump.textEdited.connect(self.on_dock_files_ledit_jump_changed)

        # dock labels
        self.dockcnt_labels.listw_labels.itemClicked.connect(self.on_dock_label_listw_item_clicked)
        self.dockcnt_labels.btn_decrease.clicked.connect(self.on_dock_label_btn_dec_clicked)
        self.dockcnt_labels.btn_increase.clicked.connect(self.on_dock_label_btn_add_clicked)
        self.dockcnt_labels.ledit_add_label.editingFinished.connect(self.on_dock_label_btn_add_clicked)
        self.dockcnt_labels.sigBtnDeleteClicked.connect(self.on_dock_label_btn_del_clicked)
        self.dockcnt_labels.sigItemColorChanged.connect(self.on_dock_label_item_color_changed)

        # dock annotations
        self.dockcnt_anno.listWidget.itemClicked.connect(self.on_dock_anno_listw_item_clicked)
        self.dockcnt_anno.sigItemDeleted.connect(self.on_dock_anno_item_deleted)

    # endregion

    # region events

    # endregion
