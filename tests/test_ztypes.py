import numpy as np

from zlabel.models.ztypes import Polygon, Rect


def test_rle_roundtrip():
    mask = np.zeros((8, 8), dtype=np.uint8)
    mask[2:5, 3:6] = 1
    rle = Polygon.rle_encode(mask)
    decoded = Polygon.rle_decode(rle, shape=(8, 8))
    assert (decoded == mask).all()


def test_rle_encode_empty_mask():
    assert Polygon.rle_encode(np.zeros((4, 4), dtype=np.uint8)) == ""


def test_rect_props():
    r = Rect(x=1, y=2, w=3, h=4)
    assert r.x1 == 4
    assert r.y1 == 6
    assert r.to_list() == [1, 2, 3, 4]
    assert r.to_list_x1y1() == [1, 2, 4, 6]
