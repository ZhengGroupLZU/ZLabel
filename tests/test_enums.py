from zlabel.utils.enums import AutoMode, ReturnType


def test_auto_mode_values():
    assert AutoMode.SAM.value == 1
    assert AutoMode.CV.value == 2
    assert AutoMode.MANUAL.value == 3


def test_auto_mode_combos():
    assert (AutoMode.SAM | AutoMode.CV).value == AutoMode.MANUAL.value


def test_auto_mode_from_value():
    assert AutoMode(1) is AutoMode.SAM
    assert AutoMode(2) is AutoMode.CV


def test_return_type_values():
    assert ReturnType.RECT.value == 1
    assert ReturnType.POLYGON.value == 2
    assert ReturnType.RLE.value == 3
    assert ReturnType(1) is ReturnType.RECT
