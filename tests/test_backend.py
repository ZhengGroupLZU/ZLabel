import numpy as np

from zlabel.utils.backend import (
    LocalInference,
    LocalStorage,
    RemoteInference,
    RemoteStorage,
    build_backend,
)
from zlabel.utils.project import id_md5
from zlabel.widgets.zsettings import ZSettings


def _settings(tmp_path, inference: str, storage: str, host: str = ""):
    s = ZSettings(root_dir=tmp_path)
    s.inference_mode = inference
    s.project.storage_mode = storage
    s.host = host
    s.username = "u"
    s.password = "p"
    return s


def test_remote_remote(tmp_path):
    b = build_backend(_settings(tmp_path, "remote", "remote", host="http://127.0.0.1:8000"))
    assert isinstance(b.inference, RemoteInference)
    assert isinstance(b.storage, RemoteStorage)
    assert b.needs_login is True


def test_local_remote(tmp_path):
    b = build_backend(_settings(tmp_path, "local", "remote", host="http://127.0.0.1:8000"))
    assert isinstance(b.inference, LocalInference)
    assert isinstance(b.storage, RemoteStorage)
    assert b.needs_login is True


def test_local_local(tmp_path):
    b = build_backend(_settings(tmp_path, "local", "local"))
    assert isinstance(b.inference, LocalInference)
    assert isinstance(b.storage, LocalStorage)
    assert b.needs_login is False


def test_remote_local(tmp_path):
    # remote inference + local storage: local images are uploaded via set_image.
    b = build_backend(_settings(tmp_path, "remote", "local", host="http://127.0.0.1:8000"))
    assert isinstance(b.inference, RemoteInference)
    assert isinstance(b.storage, LocalStorage)
    assert b.needs_login is True


class _FakeApi:
    def __init__(self):
        self.uploads: list[str] = []
        self.predict_images: list[str] = []
        self.return_data: list[dict] | None = None
        self.token = None

    def set_image(self, name: str, image) -> bool:
        self.uploads.append(name)
        return True

    def predict(self, **kwargs):
        self.predict_images.append(kwargs.get("image"))
        return {
            "status": True,
            "data": self.return_data or [],
            "msg": "ok",
            "anno_id": kwargs["anno_id"],
        }

    def login(self, username="", password=""):
        self.token = "tok"
        return "tok"


def test_remote_local_uploads_once(local_storage):
    fake = _FakeApi()
    inf = RemoteInference(api=fake, storage=local_storage)
    inf.predict(anno_id="t", image_name="a.png", points=[(1, 1)], labels=[1.0])
    assert fake.uploads == ["a.png"]
    # same image again: no set_image re-upload, but predict still carries the image
    inf.predict(anno_id="t", image_name="a.png", points=[(2, 2)], labels=[1.0])
    assert fake.uploads == ["a.png"]
    # switched image: set_image again
    inf.predict(anno_id="t", image_name="b.jpg", points=[(1, 1)], labels=[1.0])
    assert fake.uploads == ["a.png", "b.jpg"]
    # every local predict uploads the image file along with the request
    assert len(fake.predict_images) == 3
    assert all(img is not None for img in fake.predict_images)


def test_remote_local_resizes_before_upload(local_storage):
    fake = _FakeApi()
    inf = RemoteInference(api=fake, storage=local_storage, upload_image_size=32)
    inf.predict(anno_id="t", image_name="a.png", points=[(1, 1)], labels=[1.0])
    img = fake.predict_images[0]
    assert max(img.size) <= 32
    assert img.size == (32, 32)  # a.png is 64x64
    # smaller images are not upscaled
    fake2 = _FakeApi()
    inf2 = RemoteInference(api=fake2, storage=local_storage, upload_image_size=1024)
    inf2.predict(anno_id="t", image_name="b.jpg", points=[(1, 1)], labels=[1.0])
    assert max(fake2.predict_images[0].size) <= 32


def test_remote_local_scales_results_back(local_storage):
    fake = _FakeApi()
    fake.return_data = [{"x": 10, "y": 20, "w": 5, "h": 5}]
    inf = RemoteInference(api=fake, storage=local_storage, upload_image_size=32)
    resp = inf.predict(anno_id="t", image_name="a.png", points=[(1, 1)], labels=[1.0])
    # a.png is 64x64, uploaded at 32x32 -> scale 2
    assert resp["data"] == [{"x": 20, "y": 40, "w": 10, "h": 10}]


def test_remote_local_scales_polygon_and_rle_back(local_storage):
    fake = _FakeApi()
    fake.return_data = [{"points": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}]
    inf = RemoteInference(api=fake, storage=local_storage, upload_image_size=32)
    resp = inf.predict(anno_id="t", image_name="a.png", points=[(1, 1)], labels=[1.0])
    assert resp["data"] == [{"points": [{"x": 2, "y": 4}, {"x": 6, "y": 8}]}]

    # RLE: 2x2 mask at upload size -> 4x4 at original size (64x64 -> 32x32, scale 2)
    from zlabel.models.ztypes import Polygon

    m = Polygon.rle_encode(np.asarray([[1, 0], [0, 1]], np.uint8))
    fake2 = _FakeApi()
    fake2.return_data = [m]
    inf2 = RemoteInference(api=fake2, storage=local_storage, upload_image_size=32)
    resp2 = inf2.predict(anno_id="t", image_name="a.png", points=[(1, 1)], labels=[1.0])
    mask = Polygon.rle_decode(resp2["data"][0], (64, 64))
    assert mask.shape == (64, 64)
    assert mask[:2, :2].sum() >= 1  # top-left content retained after upscaling


def test_remote_local_no_scale_when_not_resized(local_storage):
    fake = _FakeApi()
    fake.return_data = [{"x": 3, "y": 4, "w": 1, "h": 1}]
    inf = RemoteInference(api=fake, storage=local_storage, upload_image_size=1024)
    resp = inf.predict(anno_id="t", image_name="a.png", points=[(1, 1)], labels=[1.0])
    assert resp["data"] == [{"x": 3, "y": 4, "w": 1, "h": 1}]


def test_remote_local_missing_image(local_storage):
    fake = _FakeApi()
    inf = RemoteInference(api=fake, storage=local_storage)
    resp = inf.predict(anno_id="t", image_name="nope.png", points=[(1, 1)], labels=[1.0])
    assert resp["status"] is False
    assert "not found" in resp["msg"]
    assert fake.uploads == []
    assert fake.predict_images == []


def test_remote_login(local_storage):
    fake = _FakeApi()
    inf = RemoteInference(api=fake, storage=local_storage)
    assert inf.login("u", "p") == "tok"
    assert fake.token == "tok"


def test_anno_dir(local_backend):
    assert local_backend.anno_dir is not None
    assert local_backend.anno_dir.name == "annos"


def test_anno_dir_remote(tmp_path):
    b = build_backend(_settings(tmp_path, "remote", "remote", host="http://127.0.0.1:8000"))
    assert b.anno_dir is None


def test_proxy_get_tasks(local_backend, make_image):
    imgdir = local_backend.storage.image_dir
    imgdir.mkdir(parents=True)
    make_image().save(imgdir / "a.png")
    tasks = local_backend.get_tasks(finished=-1, random_select=False)
    assert [t["filename"] for t in tasks] == ["a.png"]


def test_predict_missing_image(local_backend):
    resp = local_backend.predict(
        anno_id="x", image_name="nope.png", points=[(1, 1)], labels=[1.0]
    )
    assert resp["status"] is False
    assert "not found" in resp["msg"]


def test_user_token_local(local_backend):
    assert local_backend.user_token == "local"


def test_instance_id_int_coercion():
    from zlabel.utils.project import Annotation, PolygonResult, RectangleResult

    # numeric-string instance_id coerces to int
    raw = PolygonResult.new().model_dump()
    raw["instance_id"] = "7"
    assert PolygonResult.model_validate(raw).instance_id == 7
    # legacy uuid string -> 0
    raw["instance_id"] = "abc-123-uuid"
    assert PolygonResult.model_validate(raw).instance_id == 0
    # Annotation.instances string keys coerced to int (invalid keys dropped)
    a = Annotation(
        id="x", image_path="p", original_width=1, original_height=1,
        instances={"3": "normal_seed", "bad": "dead_seed"},
    )
    assert a.instances == {3: "normal_seed"}
    # RectangleResult also carries instance_id
    r = RectangleResult.new(instance_id=2)
    assert r.instance_id == 2


def test_rect_crop_box_rotated():
    from zlabel.utils.geometry import rect_crop_box

    # no rotation: unchanged
    assert rect_crop_box(10, 20, 30, 10, 0) == (10, 20, 40, 30)
    # 45deg rotation around the anchor expands the axis-aligned bbox
    box = rect_crop_box(50, 50, 10, 10, 45)
    assert (box[2] - box[0]) > 10 and (box[3] - box[1]) > 10
    assert box[0] < 43 and box[2] > 56 and box[3] > 63
    # the rotated corners are inside the bbox
    import math

    c, s = math.cos(math.radians(45)), math.sin(math.radians(45))
    for ox, oy in ((0, 0), (10, 0), (10, 10), (0, 10)):
        px = 50 + ox * c - oy * s
        py = 50 + ox * s + oy * c
        assert box[0] <= px <= box[2] and box[1] <= py <= box[3]


def test_circularity_and_area():
    import math

    from zlabel.utils.geometry import circularity, polygon_area

    def circle(cx, cy, r, n=24):
        return [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]

    big = circle(10, 10, 10)
    small = circle(50, 50, 4)
    # elongated (not round)
    el = [(90 + 20 * math.cos(t), 60 + 3 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]

    assert circularity(big) > 0.95
    assert circularity(el) < 0.5
    assert polygon_area(big) > polygon_area(el) > polygon_area(small)

    # ranking: roundness first, then area (mirrors _select_best_dish)
    from zlabel.utils import id_uuid4
    from zlabel.utils.project import Label, PolygonResult

    def key(r):
        return round(circularity(r.points), 2), polygon_area(r.points)

    lbl = Label(id=id_uuid4(), name="Dish")
    rs = [PolygonResult.new(labels=[lbl], points=p) for p in (el, small, big)]
    best = max(rs, key=key)
    assert best.points == big  # the big round circle wins over the bigger-but-elongated one


def test_local_tasks_sequence_grouping(tmp_path, make_image):
    from zlabel.utils.backend import LocalStorage

    base = tmp_path / "projects" / "proj"
    imgdir = base / "images"
    (imgdir / "wheat" / "dish1").mkdir(parents=True)
    (imgdir / "flat").mkdir()
    make_image().save(imgdir / "wheat" / "dish1" / "D1.png")
    make_image().save(imgdir / "wheat" / "dish1" / "D2.png")
    make_image().save(imgdir / "wheat" / "dish1" / "D10.png")
    make_image().save(imgdir / "flat" / "x.png")
    storage = LocalStorage(root_dir=tmp_path, project_name="proj")
    tasks = storage.get_tasks(finished=-1, random_select=False)
    by = {t["filename"]: t for t in tasks}
    assert by["wheat/dish1/D1.png"]["group"] == "wheat/dish1"
    assert by["wheat/dish1/D1.png"]["day"] == 1
    assert by["wheat/dish1/D10.png"]["day"] == 10
    assert by["flat/x.png"]["group"] == ""
    assert by["flat/x.png"]["day"] == 0
    # numeric day ordering (D2 < D10), group first then day then filename
    keys = [t["filename"] for t in tasks]
    assert keys.index("wheat/dish1/D2.png") < keys.index("wheat/dish1/D10.png")
    # anno id derives from the relative path (incl. subdirs)
    assert by["wheat/dish1/D1.png"]["anno_id"] == id_md5("proj/wheat/dish1/D1.png")
