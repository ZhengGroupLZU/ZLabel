from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtGui import QColor

from zlabel.utils import Label
from zlabel.widgets.dialog_settings import DialogSettings
from zlabel.widgets.zsettings import ZSettings


@pytest.fixture
def settings(tmp_path) -> ZSettings:
    s = ZSettings(root_dir=tmp_path)
    s.project.storage_mode = "local"
    s.inference_mode = "local"
    s.host = "http://127.0.0.1:8000"
    s.username = "rainy"
    s.password = "secret"
    s.alpha = 0.4
    s.random_select = True
    s.enable_catmull_rom = True
    s.project.labels = {Label.new("A", "#ff0000").id: Label.new("A", "#ff0000")}
    s.project.instance_statuses = ["normal_seed", "moldy_seed"]
    s.projects = [(0, "proj1"), (1, "proj2")]
    s.project_idx = 0
    return s


@pytest.fixture
def dialog(qtbot, settings) -> DialogSettings:
    d = DialogSettings(settings=settings)
    qtbot.addWidget(d)
    d.resize(700, 600)
    d.show()
    return d


def test_load_settings_populates_widgets(dialog):
    assert dialog.ledit_host.text() == "http://127.0.0.1:8000"
    assert dialog.ledit_username.text() == "rainy"
    assert dialog.ledit_password.text() == "secret"
    assert dialog.dspbox_alpha.value() == pytest.approx(0.4)
    assert dialog.ckbox_random.isChecked()
    assert dialog.ckbox_catmull_rom.isChecked()
    assert dialog.table_labels.rowCount() == 1
    assert dialog.table_statuses.rowCount() == 2
    assert dialog.combo_projects.count() == 2


def test_edit_host_updates_settings_and_emits(dialog, settings, qtbot):
    dialog.ledit_host.setText("http://10.0.0.1:9000")
    with qtbot.waitSignal(dialog.sigSettingsChanged, timeout=1000):
        dialog.ledit_host.editingFinished.emit()
    assert settings.host == "http://10.0.0.1:9000"


def test_edit_alpha_updates_settings(dialog, settings):
    dialog.dspbox_alpha.setValue(0.7)
    dialog.dspbox_alpha.editingFinished.emit()
    assert settings.alpha == pytest.approx(0.7)


def test_inference_mode_toggles_widgets(dialog, settings):
    # local mode (index 1): backend/model widgets enabled
    dialog.cmbox_inference_mode.setCurrentIndex(1)
    assert dialog.cmbox_backend.isEnabled()
    assert dialog.ledit_model_dir.isEnabled()
    # remote mode (index 0): disabled
    dialog.cmbox_inference_mode.setCurrentIndex(0)
    assert not dialog.cmbox_backend.isEnabled()
    assert not dialog.ledit_model_dir.isEnabled()
    assert settings.inference_mode == "remote"


def test_add_label_row(dialog):
    dialog.on_btn_label_add_clicked()
    assert dialog.table_labels.rowCount() == 2


def test_edit_label_name_updates_project(dialog, settings, qtbot):
    # edit the name cell of the first row
    item = dialog.table_labels.item(0, 1)
    with qtbot.waitSignal(dialog.sigSettingsChanged, timeout=1000):
        item.setText("Seed")
    names = [lbl.name for lbl in settings.project.labels.values()]
    assert "Seed" in names


def test_clear_labels(dialog, settings):
    dialog.on_btn_label_clear_clicked()
    assert dialog.table_labels.rowCount() == 0
    assert len(settings.project.labels) == 0


def test_add_status(dialog, settings, qtbot, mock_qt_dialogs):
    mock_qt_dialogs.input_result = ("germinated", True)
    with qtbot.waitSignal(dialog.sigSettingsChanged, timeout=1000):
        dialog.on_add_status()
    assert "germinated" in settings.project.instance_statuses
    assert dialog.table_statuses.rowCount() == 3


def test_del_status(dialog, settings):
    dialog.table_statuses.setCurrentCell(0, 0)
    dialog.on_del_status()
    assert "normal_seed" not in settings.project.instance_statuses


def test_germ_preset(dialog, settings, qtbot):
    with qtbot.waitSignal(dialog.sigSettingsChanged, timeout=1000):
        dialog.combo_preset.setCurrentIndex(1)  # Germ preset
    names = {lbl.name for lbl in settings.project.labels.values()}
    assert {"Seed", "Root", "Shoot", "Seedling", "Dish", "Timestamp"} <= names
    assert settings.project.key_label is not None
    assert "normal_seed" in settings.project.instance_statuses


def test_empty_preset(dialog, settings):
    dialog.on_empty_preset()
    assert len(settings.project.labels) == 0


def test_new_project(dialog, settings, qtbot, mock_qt_dialogs):
    mock_qt_dialogs.input_result = ("brandnew", True)
    with qtbot.waitSignal(dialog.sigProjectChanged, timeout=1000):
        dialog.on_new_project()
    assert settings.project_name == "brandnew"


def test_delete_project(dialog, settings, qtbot):
    with qtbot.waitSignal(dialog.sigProjectChanged, timeout=1000):
        dialog.on_delete_project()
    assert len(settings.projects) == 1


def test_browse_model_dir(dialog, settings, mock_qt_dialogs):
    mock_qt_dialogs.directory_result = "C:/models/mnn"
    dialog.on_browse_model_dir()
    assert dialog.ledit_model_dir.text() == "C:/models/mnn"
    assert settings.model_dir == "C:/models/mnn"


def test_apply_and_cancel_signals(dialog, qtbot):
    with qtbot.waitSignal(dialog.sigApplyClicked, timeout=1000):
        dialog.btn_apply.click()
    with qtbot.waitSignal(dialog.sigCancelClicked, timeout=1000):
        dialog.btn_cancel.click()


def test_unknown_setting_key_raises(dialog):
    with pytest.raises(ValueError):
        dialog.on_settings_changed("no_such_key")


def test_settings_tabs_split(dialog):
    tabs = dialog.tabWidget
    assert tabs.count() == 4
    assert [tabs.tabText(i) for i in range(tabs.count())] == ["Application", "Remote", "Inference", "Project"]
    assert tabs.indexOf(dialog.tab_application) == 0
    assert tabs.indexOf(dialog.tab_remote) == 1
    assert tabs.indexOf(dialog.tab_inference) == 2

    def in_tab(widget, tab):
        p = widget.parent()
        while p is not None:
            if p is tab:
                return True
            p = p.parent()
        return False

    assert in_tab(dialog.dspbox_alpha, dialog.tab_application)
    assert in_tab(dialog.ckbox_auto_dish, dialog.tab_application)
    assert in_tab(dialog.ledit_host, dialog.tab_remote)
    assert in_tab(dialog.ledit_username, dialog.tab_remote)
    assert in_tab(dialog.cmbox_inference_mode, dialog.tab_inference)
    assert in_tab(dialog.spin_upload_size, dialog.tab_inference)
