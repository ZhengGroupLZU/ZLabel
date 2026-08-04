from zlabel.utils.backend import (
    LocalInference,
    LocalStorage,
    RemoteInference,
    RemoteStorage,
    build_backend,
)
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


def test_remote_local_falls_back_to_local_inference(tmp_path):
    # remote inference + local storage is invalid; build_backend must fall back
    b = build_backend(_settings(tmp_path, "remote", "local"))
    assert isinstance(b.inference, LocalInference)
    assert isinstance(b.storage, LocalStorage)
    assert b.needs_login is False


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
