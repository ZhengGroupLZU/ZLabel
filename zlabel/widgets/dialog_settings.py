from pyqtgraph.Qt.QtCore import Qt, Signal
from pyqtgraph.Qt.QtGui import QIcon
from pyqtgraph.Qt.QtWidgets import (
    QColorDialog,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QInputDialog,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidgetItem,
)

from zlabel.utils import id_md5
from zlabel.utils.enums import LogLevel
from zlabel.utils.project import Label
from zlabel.widgets.zsettings import ZSettings

from .ui import Ui_DialogSettings


class DialogSettings(QDialog, Ui_DialogSettings):
    sigSettingsChanged = Signal()
    sigApplyClicked = Signal()
    sigCancelClicked = Signal()
    sigProjectChanged = Signal(int)

    def __init__(
        self,
        settings: ZSettings | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self.settings: ZSettings | None = settings
        self.table_labels.setHorizontalHeaderLabels(["ID", "Name", "Color", "Delete"])
        self.table_labels.setRowCount(0)

        self._loading: bool = True

        if self.settings:
            self.load_settings()
        self.init_signals()
        self._loading = False

    def _load_statuses(self):
        from zlabel.widgets.dock_anno import humanize_status

        self.table_statuses.setRowCount(0)
        if self.settings is None:
            return
        for val in self.settings.project.instance_statuses:
            row = self.table_statuses.rowCount()
            self.table_statuses.insertRow(row)
            item = QTableWidgetItem(humanize_status(val))
            item.setData(Qt.ItemDataRole.UserRole, val)
            self.table_statuses.setItem(row, 0, item)

    def on_add_status(self):
        if self.settings is None:
            return
        text, ok = QInputDialog.getText(self, self.tr("Add status"), self.tr("Status value:"))
        if not ok or not text.strip():
            return
        val = text.strip().lower().replace(" ", "_")
        if val not in self.settings.project.instance_statuses:
            self.settings.project.instance_statuses.append(val)
            self._load_statuses()
            self.sigSettingsChanged.emit()

    def on_del_status(self):
        if self.settings is None:
            return
        row = self.table_statuses.currentRow()
        if row < 0:
            return
        item = self.table_statuses.item(row, 0)
        if item is not None:
            val = item.data(Qt.ItemDataRole.UserRole)
            if val in self.settings.project.instance_statuses:
                self.settings.project.instance_statuses.remove(val)
        self._load_statuses()
        self.sigSettingsChanged.emit()

    def _refresh_projects_combo(self):
        if self.settings is None:
            return
        self.combo_projects.blockSignals(True)
        self.combo_projects.clear()
        self.combo_projects.addItems([name for _, name in self.settings.projects])
        self.combo_projects.setCurrentIndex(self.settings.project_idx)
        self.combo_projects.blockSignals(False)

    def on_project_selected(self, index: int):
        if self._loading or self.settings is None:
            return
        if index < 0 or index >= len(self.settings.projects):
            return
        if index != self.settings.project_idx:
            self.settings.project_idx = index
            self.sigProjectChanged.emit(index)

    def on_new_project(self):
        if self.settings is None:
            return
        name, ok = QInputDialog.getText(self, self.tr("New Project"), self.tr("Project name:"))
        if not ok or not name.strip():
            return
        name = name.strip()
        from zlabel.utils.project import Project, id_uuid4

        project = Project(id=id_uuid4(), name=name)
        project.storage_mode = self.settings.project.storage_mode
        project.save_json(self.settings.project_root / name / f"{name}.json")
        self.settings.projects.append((len(self.settings.projects), name))
        self.settings.project_idx = len(self.settings.projects) - 1
        self.settings.project = project
        self._refresh_projects_combo()
        self.load_settings(self.settings)
        self.sigProjectChanged.emit(self.settings.project_idx)

    def on_delete_project(self):
        if self.settings is None or len(self.settings.projects) <= 1:
            return
        idx = self.settings.project_idx
        self.settings.projects.pop(idx)
        self.settings.project_idx = min(idx, len(self.settings.projects) - 1)
        self.settings.reload_project()
        self._refresh_projects_combo()
        self.load_settings(self.settings)
        self.sigProjectChanged.emit(self.settings.project_idx)

    def _rename_project(self, new_name: str):
        if self.settings is None:
            return
        old_name = self.settings.project.name
        if not new_name or new_name == old_name:
            return
        old_dir = self.settings.project_root / old_name
        new_dir = self.settings.project_root / new_name
        if old_dir.exists() and not new_dir.exists() and old_name:
            try:
                old_dir.rename(new_dir)
            except OSError:
                pass
        self.settings.project.name = new_name
        if 0 <= self.settings.project_idx < len(self.settings.projects):
            self.settings.projects[self.settings.project_idx] = (
                self.settings.projects[self.settings.project_idx][0],
                new_name,
            )
        self._refresh_projects_combo()

    def on_preset_selected(self, index: int):
        if index == 1:
            self.on_germ_preset()
        elif index == 0:
            self.on_empty_preset()

    def on_empty_preset(self):
        """Clear the project's labels and instance statuses."""
        if self.settings is None:
            return
        self.settings.project.labels.clear()
        self.settings.project.instance_statuses = []
        self.settings.project.key_label = None
        self.set_labels({})
        self._load_statuses()
        self.sigSettingsChanged.emit()

    def on_browse_model_dir(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("Select MNN model folder"))
        if not path:
            return
        self.ledit_model_dir.setText(path)
        self.on_settings_changed("model_dir")

    def on_germ_preset(self):
        """Load the germination preset: default labels (merged with existing) and
        default instance statuses (replaced)."""
        if self.settings is None:
            return
        from zlabel.utils import germ_preset_labels
        from zlabel.utils.project import GermStatus

        existing = {lbl.name for lbl in self.settings.project.labels.values()}
        for lbl in germ_preset_labels().values():
            if lbl.name not in existing:
                self.settings.project.labels[lbl.id] = lbl
        self.settings.project.key_label = next(iter(self.settings.project.labels), None)
        self.settings.project.instance_statuses = [s.value for s in GermStatus] + ["dish", "text"]
        self.set_labels(self.settings.project.labels)
        self._load_statuses()
        self.sigSettingsChanged.emit()

    def on_browse_ocr_dir(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("Select WeChat OCR folder (wxocr)"))
        if not path:
            return
        self.ledit_ocr_dir.setText(path)
        self.on_settings_changed("ocr_wx_dir")

    def on_ocr_dir_changed(self):
        """Push the chosen wxocr folder to the OCR engine (resets its cache)."""
        from zlabel.utils.ocr import set_wxocr_dir

        set_wxocr_dir(self.settings.ocr_wx_dir if self.settings else "")

    def update_inference_widgets_enabled(self):
        is_local = self.cmbox_inference_mode.currentIndex() == 1
        self.cmbox_backend.setEnabled(is_local)
        self.cmbox_model_name.setEnabled(is_local)
        self.ledit_model_dir.setEnabled(is_local)
        self.btn_model_dir.setEnabled(is_local)

    def load_settings(self, settings: ZSettings | None = None):
        self.settings = settings or self.settings
        assert self.settings is not None

        self.ledit_host.setText(str(self.settings.host))
        self.ledit_username.setText(str(self.settings.username))
        self.ledit_password.setText(str(self.settings.password))
        self.dspbox_alpha.setValue(self.settings.alpha)
        self.ckbox_random.setChecked(self.settings.random_select)
        self.ckbox_catmull_rom.setChecked(self.settings.enable_catmull_rom)

        self.cmbox_loglevel.setCurrentIndex(self.settings.log_level.value)

        self.cmbox_inference_mode.setCurrentIndex(0 if self.settings.inference_mode == "remote" else 1)
        self.cmbox_backend.setCurrentText(self.settings.inference_backend)
        self.cmbox_model_name.setCurrentText(self.settings.model_name)
        self.ledit_model_dir.setText(self.settings.model_dir)
        self.spin_upload_size.setValue(self.settings.upload_image_size)
        self.ckbox_auto_dish.setChecked(self.settings.auto_fit_dish)
        self.ckbox_ocr_enable.setChecked(self.settings.ocr_enable_manual)
        self.ledit_ocr_dir.setText(self.settings.ocr_wx_dir)
        self.ckbox_copy_prev.setChecked(self.settings.enable_copy_prev)
        self.update_inference_widgets_enabled()

        self.btn_hline_color.set_color(self.settings.hline_color)
        self.spin_hline_width.setValue(self.settings.hline_width)
        self.btn_vline_color.set_color(self.settings.vline_color)
        self.spin_vline_width.setValue(self.settings.vline_width)
        self.btn_default_color.set_color(self.settings.default_color)
        self.dspbox_edit_alpha.setValue(self.settings.edit_fill_alpha)
        self.dspbox_draw_alpha.setValue(self.settings.draw_fill_alpha)
        self.dspbox_mag_min.setValue(self.settings.magnifier_min_zoom)
        self.dspbox_mag_max.setValue(self.settings.magnifier_max_zoom)
        self.spin_mag_diameter.setValue(self.settings.magnifier_diameter)
        self.spin_display_max_side.setValue(self.settings.display_max_side)
        self.spin_pyramid_levels.setValue(self.settings.pyramid_levels)
        self.spin_image_cache_size.setValue(self.settings.image_cache_size)
        self.spin_tl_small_side.setValue(self.settings.timeline_small_image_side)
        self.spin_tl_cache_size.setValue(self.settings.timeline_small_image_cache_size)
        self.spin_tl_cell_size.setValue(self.settings.timeline_cell_size)

        self.set_labels(self.settings.project.labels)
        self.ledit_projname.setText(str(self.settings.project.name))
        self.ledit_prjdesc.setText(str(self.settings.project.description))
        self._refresh_projects_combo()
        self._load_statuses()

    def init_signals(self):
        # here the k passed to on_settings_changed is the attribute name in ZSettings
        self.ledit_host.editingFinished.connect(lambda: self.on_settings_changed("host"))
        self.ledit_username.editingFinished.connect(lambda: self.on_settings_changed("username"))
        self.ledit_password.editingFinished.connect(lambda: self.on_settings_changed("password"))
        self.dspbox_alpha.editingFinished.connect(lambda: self.on_settings_changed("alpha"))
        self.ckbox_random.checkStateChanged.connect(lambda: self.on_settings_changed("random_select"))
        self.ckbox_catmull_rom.checkStateChanged.connect(lambda: self.on_settings_changed("enable_catmull_rom"))

        self.ledit_projname.editingFinished.connect(lambda: self.on_settings_changed("project_name"))
        self.ledit_prjdesc.editingFinished.connect(lambda: self.on_settings_changed("project_desc"))

        # Track edits in the labels table
        self.table_labels.itemChanged.connect(self.on_table_labels_item_changed)

        self.btn_apply.clicked.connect(self.sigSettingsChanged.emit)
        self.btn_apply.clicked.connect(self.sigApplyClicked.emit)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_cancel.clicked.connect(self.sigCancelClicked.emit)

        self.btn_add_label.clicked.connect(self.on_btn_label_add_clicked)
        self.btn_delete_label.clicked.connect(self.on_btn_label_delete_clicked)
        self.btn_clear.clicked.connect(self.on_btn_label_clear_clicked)

        self.cmbox_loglevel.currentIndexChanged.connect(lambda: self.on_settings_changed("log_level"))

        self.cmbox_inference_mode.currentIndexChanged.connect(self.on_inference_mode_changed)
        self.cmbox_backend.currentIndexChanged.connect(lambda: self.on_settings_changed("inference_backend"))
        self.cmbox_model_name.currentIndexChanged.connect(lambda: self.on_settings_changed("model_name"))
        self.ledit_model_dir.editingFinished.connect(lambda: self.on_settings_changed("model_dir"))
        self.spin_upload_size.valueChanged.connect(lambda: self.on_settings_changed("upload_image_size"))
        self.ckbox_auto_dish.toggled.connect(lambda: self.on_settings_changed("auto_fit_dish"))
        self.ckbox_ocr_enable.toggled.connect(lambda: self.on_settings_changed("ocr_enable_manual"))
        self.ledit_ocr_dir.editingFinished.connect(lambda: self.on_settings_changed("ocr_wx_dir"))
        self.ckbox_copy_prev.toggled.connect(lambda: self.on_settings_changed("enable_copy_prev"))

        self.btn_hline_color.colorChanged.connect(lambda _: self.on_settings_changed("hline_color"))
        self.spin_hline_width.valueChanged.connect(lambda: self.on_settings_changed("hline_width"))
        self.btn_vline_color.colorChanged.connect(lambda _: self.on_settings_changed("vline_color"))
        self.spin_vline_width.valueChanged.connect(lambda: self.on_settings_changed("vline_width"))
        self.btn_default_color.colorChanged.connect(lambda _: self.on_settings_changed("default_color"))
        self.dspbox_edit_alpha.valueChanged.connect(lambda: self.on_settings_changed("edit_fill_alpha"))
        self.dspbox_draw_alpha.valueChanged.connect(lambda: self.on_settings_changed("draw_fill_alpha"))
        self.dspbox_mag_min.valueChanged.connect(lambda: self.on_settings_changed("magnifier_min_zoom"))
        self.dspbox_mag_max.valueChanged.connect(lambda: self.on_settings_changed("magnifier_max_zoom"))
        self.spin_mag_diameter.valueChanged.connect(lambda: self.on_settings_changed("magnifier_diameter"))
        self.spin_display_max_side.valueChanged.connect(lambda: self.on_settings_changed("display_max_side"))
        self.spin_pyramid_levels.valueChanged.connect(lambda: self.on_settings_changed("pyramid_levels"))
        self.spin_image_cache_size.valueChanged.connect(lambda: self.on_settings_changed("image_cache_size"))
        self.spin_tl_small_side.valueChanged.connect(lambda: self.on_settings_changed("timeline_small_image_side"))
        self.spin_tl_cache_size.valueChanged.connect(
            lambda: self.on_settings_changed("timeline_small_image_cache_size")
        )
        self.spin_tl_cell_size.valueChanged.connect(lambda: self.on_settings_changed("timeline_cell_size"))

        self.combo_projects.currentIndexChanged.connect(self.on_project_selected)
        self.btn_new_project.clicked.connect(self.on_new_project)
        self.btn_delete_project.clicked.connect(self.on_delete_project)

        self.combo_preset.currentIndexChanged.connect(self.on_preset_selected)
        self.btn_add_status.clicked.connect(self.on_add_status)
        self.btn_del_status.clicked.connect(self.on_del_status)
        self.btn_model_dir.clicked.connect(self.on_browse_model_dir)
        self.btn_ocr_dir.clicked.connect(self.on_browse_ocr_dir)

    def on_inference_mode_changed(self):
        self.update_inference_widgets_enabled()
        self.on_settings_changed("inference_mode")

    def on_settings_changed(self, k: str):
        if self._loading:
            return
        assert self.settings is not None
        if k == "host":
            self.settings.host = self.ledit_host.text().strip()
        elif k == "username":
            self.settings.username = self.ledit_username.text().strip()
        elif k == "password":
            self.settings.password = self.ledit_password.text().strip()
        elif k == "alpha":
            self.settings.alpha = self.dspbox_alpha.value()
        elif k == "random_select":
            self.settings.random_select = self.ckbox_random.isChecked()
        elif k == "enable_catmull_rom":
            self.settings.enable_catmull_rom = self.ckbox_catmull_rom.isChecked()
        elif k == "inference_mode":
            self.settings.inference_mode = "local" if self.cmbox_inference_mode.currentIndex() == 1 else "remote"
        elif k == "inference_backend":
            self.settings.inference_backend = self.cmbox_backend.currentText()
        elif k == "model_name":
            self.settings.model_name = self.cmbox_model_name.currentText()
        elif k == "model_dir":
            self.settings.model_dir = self.ledit_model_dir.text().strip()
        elif k == "upload_image_size":
            self.settings.upload_image_size = self.spin_upload_size.value()
        elif k == "auto_fit_dish":
            self.settings.auto_fit_dish = self.ckbox_auto_dish.isChecked()
        elif k == "ocr_enable_manual":
            self.settings.ocr_enable_manual = self.ckbox_ocr_enable.isChecked()
        elif k == "ocr_wx_dir":
            self.settings.ocr_wx_dir = self.ledit_ocr_dir.text().strip()
            self.on_ocr_dir_changed()
        elif k == "enable_copy_prev":
            self.settings.enable_copy_prev = self.ckbox_copy_prev.isChecked()
        elif k == "hline_color":
            self.settings.hline_color = self.btn_hline_color.color()
        elif k == "hline_width":
            self.settings.hline_width = self.spin_hline_width.value()
        elif k == "vline_color":
            self.settings.vline_color = self.btn_vline_color.color()
        elif k == "vline_width":
            self.settings.vline_width = self.spin_vline_width.value()
        elif k == "default_color":
            self.settings.default_color = self.btn_default_color.color()
        elif k == "edit_fill_alpha":
            self.settings.edit_fill_alpha = self.dspbox_edit_alpha.value()
        elif k == "draw_fill_alpha":
            self.settings.draw_fill_alpha = self.dspbox_draw_alpha.value()
        elif k == "magnifier_min_zoom":
            self.settings.magnifier_min_zoom = self.dspbox_mag_min.value()
        elif k == "magnifier_max_zoom":
            self.settings.magnifier_max_zoom = self.dspbox_mag_max.value()
        elif k == "magnifier_diameter":
            self.settings.magnifier_diameter = self.spin_mag_diameter.value()
        elif k == "display_max_side":
            self.settings.display_max_side = self.spin_display_max_side.value()
        elif k == "pyramid_levels":
            self.settings.pyramid_levels = self.spin_pyramid_levels.value()
        elif k == "image_cache_size":
            self.settings.image_cache_size = self.spin_image_cache_size.value()
        elif k == "timeline_small_image_side":
            self.settings.timeline_small_image_side = self.spin_tl_small_side.value()
        elif k == "timeline_small_image_cache_size":
            self.settings.timeline_small_image_cache_size = self.spin_tl_cache_size.value()
        elif k == "timeline_cell_size":
            self.settings.timeline_cell_size = self.spin_tl_cell_size.value()
        elif k == "project_name":
            self._rename_project(self.ledit_projname.text().strip())
        elif k == "project_desc":
            self.settings.project.description = self.ledit_prjdesc.text().strip()
        elif k == "log_level":
            self.settings.log_level = LogLevel(self.cmbox_loglevel.currentIndex())
        else:
            raise ValueError(f"Unknown setting key: {k}")
        self.sigSettingsChanged.emit()

    def on_table_labels_item_changed(self, item: QTableWidgetItem):
        if self.settings is None or self.sender() != self.table_labels or item.column() == 0:
            return

        # Name
        item_name = self.table_labels.item(item.row(), 1)
        label_name = item_name.text().strip() if item_name else ""
        if not label_name:
            return

        # ID
        label_id = id_md5(label_name)
        item_id = self.table_labels.item(item.row(), 0)
        prev_id = item_id.text().strip() if item_id else ""
        if item_id:
            item_id.setText(label_id)
        else:
            self.table_labels.setItem(item.row(), 0, QTableWidgetItem(label_id))
        # Determine current color from the row's color button (if present)
        color_btn = self.table_labels.cellWidget(item.row(), 2)
        color_text = "#000000"
        if isinstance(color_btn, QPushButton):
            t = color_btn.text().strip()
            if t:
                color_text = t.lower()
        # If the ID changed due to a name edit, drop the old entry
        if prev_id and prev_id != label_id:
            self.settings.project.labels.pop(prev_id, None)

        if label_id in self.settings.project.labels:
            self.settings.project.labels[label_id].name = label_name
            self.settings.project.labels[label_id].color = color_text
        else:
            self.settings.project.labels[label_id] = Label(id=label_id, name=label_name, color=color_text)

        # Only handle name edits here; color is managed by the button widget
        self.sigSettingsChanged.emit()

    def on_btn_label_add_clicked(self):
        self.add_row(Label(id="", name=""))

    def on_btn_label_delete_clicked(self):
        if self.settings is None:
            return

        selected_items = self.table_labels.selectedItems()
        selected_rows = list({item.row() for item in selected_items})
        selected_rows.sort(reverse=True)
        for row in selected_rows:
            label_item = self.table_labels.item(row, 0)
            if label_item:
                label_id = label_item.text().strip()
                self.settings.project.labels.pop(label_id, None)
            self.table_labels.removeRow(row)
        self.sigSettingsChanged.emit()

    def on_btn_label_clear_clicked(self):
        if self.settings is None:
            return

        self.settings.project.labels.clear()
        self.table_labels.setRowCount(0)

    def add_row(self, label: Label, row: int | None = None):
        idx = row if row is not None else self.table_labels.rowCount()
        self.table_labels.insertRow(idx)

        # ID
        item = QTableWidgetItem("")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if label.id:
            item.setText(label.id)
        self.table_labels.setItem(idx, 0, item)

        # name
        item = QTableWidgetItem("")
        if label.name:
            item.setText(label.name)
        self.table_labels.setItem(idx, 1, item)

        def btn_item_select_color_clicked(btn: QPushButton):
            color = QColorDialog.getColor()
            if not color.isValid():
                return
            btn.setStyleSheet(f"background-color: {color.name()}")
            btn.setText(color.name().upper())
            # Update settings with the selected color based on current row/name
            if self.settings is None:
                return
            # find the row of this button
            row_idx = -1
            for r in range(self.table_labels.rowCount()):
                if self.table_labels.cellWidget(r, 2) is btn:
                    row_idx = r
                    break
            if row_idx < 0:
                return
            item_name = self.table_labels.item(row_idx, 1)
            label_name = item_name.text().strip() if item_name else ""
            if not label_name:
                # No name yet; just update button UI, wait for name input
                return
            label_id = id_md5(label_name)
            item_id = self.table_labels.item(row_idx, 0)
            if item_id:
                item_id.setText(label_id)
            else:
                self.table_labels.setItem(row_idx, 0, QTableWidgetItem(label_id))
            if label_id in self.settings.project.labels:
                self.settings.project.labels[label_id].color = color.name()
                self.settings.project.labels[label_id].name = label_name
            else:
                self.settings.project.labels[label_id] = Label(id=label_id, name=label_name, color=color.name())
            self.sigSettingsChanged.emit()

        def btn_item_delete_clicked(btn: QPushButton):
            if self.settings is None:
                return
            # Identify the row from the clicked button
            target_row = -1
            for r in range(self.table_labels.rowCount()):
                if self.table_labels.cellWidget(r, 3) is btn:
                    target_row = r
                    break
            if target_row < 0:
                return
            label_item_id = self.table_labels.item(target_row, 0)
            label_id = label_item_id.text().strip() if label_item_id else ""
            if label_id:
                self.settings.project.labels.pop(label_id, None)
            self.table_labels.removeRow(target_row)
            self.sigSettingsChanged.emit()

        # color
        btn_select_color = QPushButton(self.tr("Select Color"))
        btn_select_color.setStyleSheet(f"background-color: {label.color}")
        btn_select_color.setText(label.color.upper())
        btn_select_color.clicked.connect(lambda: btn_item_select_color_clicked(btn_select_color))
        self.table_labels.setCellWidget(idx, 2, btn_select_color)

        # delete
        btn_delete = QPushButton(self.tr("Delete"))
        btn_delete.setIcon(QIcon(":/icon/icons/delete-3.svg"))
        btn_delete.clicked.connect(lambda: btn_item_delete_clicked(btn_delete))
        self.table_labels.setCellWidget(idx, 3, btn_delete)

    def set_labels(self, labels: dict[str, Label]):
        self.table_labels.itemChanged.disconnect(self.on_table_labels_item_changed)
        self.table_labels.setRowCount(0)
        for idx, label in enumerate(labels.values()):
            self.add_row(label, idx)
        self.table_labels.itemChanged.connect(self.on_table_labels_item_changed)
