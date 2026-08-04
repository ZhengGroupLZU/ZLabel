def test_get_projects(local_storage):
    projects = local_storage.get_projects()
    assert {"id": 0, "name": "proj"} in projects


def test_get_tasks_all(local_storage):
    tasks = local_storage.get_tasks(finished=-1, random_select=False)
    assert {t["filename"] for t in tasks} == {"a.png", "b.jpg"}


def test_get_tasks_unfinished(local_storage):
    tasks = local_storage.get_tasks(finished=0, random_select=False)
    assert len(tasks) == 2


def test_get_tasks_limit(local_storage):
    tasks = local_storage.get_tasks(finished=-1, num=1, random_select=False)
    assert len(tasks) == 1


def test_get_tasks_finished(local_storage):
    t = local_storage.get_tasks(finished=0, random_select=False)[0]
    (local_storage.anno_dir / f"{t['anno_id']}.zlabel").write_text("{}", encoding="utf-8")
    tasks = local_storage.get_tasks(finished=1, random_select=False)
    assert [x["filename"] for x in tasks] == [t["filename"]]
    # unfinished excludes it now
    tasks_u = local_storage.get_tasks(finished=0, random_select=False)
    assert t["filename"] not in {x["filename"] for x in tasks_u}


def test_get_tasks_bad_finished(local_storage):
    import pytest

    with pytest.raises(ValueError):
        local_storage.get_tasks(finished=42)


def test_get_image(local_storage):
    img = local_storage.get_image("a.png")
    assert img is not None and img.width == 64


def test_get_image_missing(local_storage):
    assert local_storage.get_image("nope.png") is None


def test_get_zlabel(local_storage):
    (local_storage.anno_dir / "abc.zlabel").write_text('{"id": "abc"}', encoding="utf-8")
    assert local_storage.get_zlabel("abc.zlabel") == '{"id": "abc"}'


def test_get_zlabel_missing(local_storage):
    assert local_storage.get_zlabel("nope.zlabel") is None


def test_save_zlabel_same_dir_noop(local_storage):
    anno = local_storage.anno_dir / "a1.zlabel"
    anno.parent.mkdir(parents=True, exist_ok=True)
    anno.write_text("{}", encoding="utf-8")
    assert local_storage.save_zlabel(str(anno)) is True


def test_save_zlabel_copy(local_storage, tmp_path):
    src = tmp_path / "a1.zlabel"
    src.write_text("{}", encoding="utf-8")
    assert local_storage.save_zlabel(str(src)) is True
    assert (local_storage.anno_dir / "a1.zlabel").read_text(encoding="utf-8") == "{}"


def test_save_zlabel_missing(local_storage, tmp_path):
    assert local_storage.save_zlabel(str(tmp_path / "nope.zlabel")) is False


def test_login_returns_token(local_storage):
    assert local_storage.login() == "local"


def test_preupload_is_noop(local_storage):
    assert local_storage.preupload_image("a1", None) is None


def test_custom_local_dir(local_storage_custom):
    assert str(local_storage_custom.image_dir).endswith("custom")
    assert local_storage_custom.anno_dir == local_storage_custom.image_dir / "annos"
    tasks = local_storage_custom.get_tasks(finished=-1, random_select=False)
    assert [t["filename"] for t in tasks] == ["x.png"]


def test_custom_local_dir_anno(local_storage_custom):
    t = local_storage_custom.get_tasks(finished=0, random_select=False)[0]
    (local_storage_custom.anno_dir / f"{t['anno_id']}.zlabel").write_text("{}", encoding="utf-8")
    finished = local_storage_custom.get_tasks(finished=1, random_select=False)
    assert [x["filename"] for x in finished] == ["x.png"]
