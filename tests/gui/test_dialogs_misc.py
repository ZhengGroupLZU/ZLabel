from __future__ import annotations

import pytest
from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtWidgets import QLabel, QPushButton

from zlabel.widgets.dialog_about import DialogAbout
from zlabel.widgets.dialog_processing import DialogProcessing
from zlabel.widgets.dialog_shortcut import DialogShortcut
from zlabel.widgets.switch_button import SwitchBtn
from zlabel.widgets.zwidgets import Toast, ZPushButton, ZSlider, ZSwitchButton


def test_about_dialog_shows(qtbot):
    from zlabel import __version__

    d = DialogAbout(parent=None)
    qtbot.addWidget(d)
    d.show()
    assert d.isVisible()
    assert d.textBrowser is not None
    html = d.textBrowser.toHtml()
    assert __version__ in html
    assert "Apache" in html
    assert "as is" in html
    assert "https://github.com/ZhengGroupLZU/ZLabel" in html


def test_about_dialog_retranslate_keeps_version(qtbot):
    from zlabel import __version__

    d = DialogAbout(parent=None)
    qtbot.addWidget(d)
    d.retranslateUi(d)
    html = d.textBrowser.toHtml()
    assert __version__ in html
    assert "https://github.com/ZhengGroupLZU/ZLabel" in html


def test_shortcut_dialog_shows(qtbot):
    d = DialogShortcut(parent=None)
    qtbot.addWidget(d)
    d.show()
    assert d.isVisible()


def test_processing_dialog_timer(qtbot):
    d = DialogProcessing()
    qtbot.addWidget(d)
    d.show()
    assert d.animation_timer.isActive()
    d.hide()
    assert not d.animation_timer.isActive()


def test_processing_cancel_rejects(qtbot):
    d = DialogProcessing()
    qtbot.addWidget(d)
    d.show()
    with qtbot.waitSignal(d.rejected, timeout=1000):
        d.cancel_button.click()


def test_toast_auto_closes(qtbot):
    t = Toast("hello", timeout=200)
    qtbot.addWidget(t)
    t.show()
    qtbot.wait(400)
    assert not t.isVisible()


def test_zpushbutton_single_and_double(qtbot):
    b = ZPushButton("click")
    qtbot.addWidget(b)
    singles, doubles = [], []
    b.singleClicked.connect(lambda: singles.append(1))
    b.doubleClicked.connect(lambda: doubles.append(1))
    qtbot.mouseClick(b, Qt.MouseButton.LeftButton)
    qtbot.wait(700)  # longer than the single-click timer
    assert len(singles) == 1
    assert len(doubles) == 0

    # two quick presses within the double-click interval
    pos = b.rect().center()
    from PySide6.QtTest import QTest

    QTest.mousePress(b, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    QTest.mouseRelease(b, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    QTest.mousePress(b, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    QTest.mouseRelease(b, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    qtbot.wait(100)
    assert len(doubles) == 1


def test_zswitchbutton_emits(qtbot):
    s = ZSwitchButton()
    qtbot.addWidget(s)
    emitted = []
    s.sigCheckStateChanged.connect(emitted.append)
    qtbot.mouseClick(s, Qt.MouseButton.LeftButton)
    # emits a bool on every release (app syncs the setting from this signal)
    assert len(emitted) == 1
    assert isinstance(emitted[0], bool)


def test_switchbtn_emits(qtbot):
    s = SwitchBtn()
    qtbot.addWidget(s)
    emitted = []
    s.checkedChanged.connect(emitted.append)
    qtbot.mouseClick(s, Qt.MouseButton.LeftButton)
    assert emitted == [True]
    # programmatic setChecked does NOT emit
    s.setChecked(False)
    assert emitted == [True]


def test_zslider_value_changes(qtbot):
    sl = ZSlider()
    qtbot.addWidget(sl)
    values = []
    sl.valueChanged.connect(values.append)
    sl.setValue(75)
    assert values == [75]
    assert sl.label.text() == "75"
