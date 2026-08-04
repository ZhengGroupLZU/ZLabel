import random
import shutil
import threading
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np
from PIL import Image

from zlabel.utils.api_helper import ZLServerApiHelper
from zlabel.utils.logger import ZLogger
from zlabel.utils.paths import resource_dir
from zlabel.utils.project import id_md5


@runtime_checkable
class Inference(Protocol):
    requires_server: bool

    def predict(
        self,
        anno_id: str,
        image_name: str,
        points: list[tuple[float, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[tuple[float, float, float, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
        return_type: int = 1,  # RECT = 1 POLYGON = 2 RLE = 3
    ) -> dict[str, Any]: ...


@runtime_checkable
class Storage(Protocol):
    requires_server: bool

    def login(self, username: str = "", password: str = "") -> str | None: ...
    def get_projects(self) -> list[dict[str, int | str]] | None: ...
    def get_tasks(
        self,
        project_id: int = -1,
        num: int = 50,
        finished: int = 1,
        random_select: bool = True,
    ) -> list[dict[str, Any]] | None: ...
    def get_image(self, name: str) -> Image.Image | None: ...
    def get_zlabel(self, name: str) -> str | None: ...
    def save_zlabel(self, filename: str) -> bool | None: ...
    def preupload_image(self, anno_id: str, image: Image.Image): ...


class RemoteInference:
    requires_server = True

    def __init__(self, api: ZLServerApiHelper) -> None:
        self.api = api

    def predict(
        self,
        anno_id: str,
        image_name: str,
        points: list[tuple[float, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[tuple[float, float, float, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
        return_type: int = 1,
    ) -> dict[str, Any]:
        return self.api.predict(
            anno_id=anno_id,
            image_name=image_name,
            points=points,
            labels=labels,
            rects=rects,
            threshold=threshold,
            mode=mode,
            return_type=return_type,
        )


class RemoteStorage:
    requires_server = True

    def __init__(self, api: ZLServerApiHelper) -> None:
        self.api = api

    @property
    def user_token(self) -> str:
        return self.api.user_token

    @property
    def logger(self) -> ZLogger:
        return self.api.logger

    def login(self, username: str = "", password: str = "") -> str | None:
        return self.api.login(username, password)

    def get_projects(self) -> list[dict[str, int | str]] | None:
        return self.api.get_projects()

    def get_tasks(
        self,
        project_id: int = -1,
        num: int = 50,
        finished: int = 1,
        random_select: bool = True,
    ) -> list[dict[str, Any]] | None:
        return self.api.get_tasks(project_id, num, finished, random_select)

    def get_image(self, name: str) -> Image.Image | None:
        return self.api.get_image(name)

    def get_zlabel(self, name: str) -> str | None:
        return self.api.get_zlabel(name)

    def save_zlabel(self, filename: str) -> bool | None:
        return self.api.save_zlabel(filename)

    def preupload_image(self, anno_id: str, image: Image.Image):
        return self.api.preupload_image(anno_id, image)


class LocalStorage:
    requires_server = False

    def __init__(self, root_dir: Path, project_name: str, local_dir: str = "") -> None:
        self.root_dir = Path(root_dir)
        self.project_name = project_name
        # Optional user-selected directory. When set, it is used directly as the
        # images folder (annotations go to a sibling `annos/` subfolder).
        self.local_dir = local_dir
        self.user_token: str = "local"
        self.logger = ZLogger("LocalStorage")

    @property
    def project_root(self) -> Path:
        return self.root_dir / "projects"

    @property
    def project_dir(self) -> Path:
        if self.local_dir:
            return Path(self.local_dir)
        return self.project_root / self.project_name

    @property
    def image_dir(self) -> Path:
        if self.local_dir:
            return Path(self.local_dir)
        return self.project_root / self.project_name / "images"

    @property
    def anno_dir(self) -> Path:
        if self.local_dir:
            return Path(self.local_dir) / "annos"
        return self.project_root / self.project_name / "annos"

    def login(self, username: str = "", password: str = "") -> str | None:
        return self.user_token

    def get_projects(self) -> list[dict[str, int | str]]:
        projects: list[dict[str, int | str]] = []
        for d in sorted(self.project_root.glob("*")):
            if d.is_dir():
                projects.append({"id": len(projects), "name": d.name})
        return projects

    def get_tasks(
        self,
        project_id: int = -1,
        num: int = 50,
        finished: int = 1,
        random_select: bool = True,
    ) -> list[dict[str, Any]]:
        if not self.image_dir.exists():
            return []
        files = sorted(
            p
            for p in self.image_dir.iterdir()
            if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg")
        )
        tasks: list[dict[str, Any]] = []
        for f in files:
            anno_id = id_md5(f"{self.project_name}/{f.name}")
            is_finished = (self.anno_dir / f"{anno_id}.zlabel").exists()
            if finished == -1:
                pass
            elif finished == 0:
                if is_finished:
                    continue
            elif finished == 1:
                if not is_finished:
                    continue
            else:
                raise ValueError("finished must be -1, 0 or 1")
            tasks.append(
                {
                    "id": len(tasks),
                    "project_id": project_id,
                    "anno_id": anno_id,
                    "filename": f.name,
                    "labels": [],
                    "finished": is_finished,
                }
            )
        if random_select:
            random.shuffle(tasks)
        else:
            tasks.sort(key=lambda t: t["filename"])
        return tasks[:num]

    def get_image(self, name: str) -> Image.Image | None:
        p = self.image_dir / name
        if not p.exists():
            self.logger.error(f"Get image failed, {name=} not found in {self.image_dir}")
            return None
        return Image.open(p)

    def get_zlabel(self, name: str) -> str | None:
        p = self.anno_dir / name
        if not p.exists():
            self.logger.error(f"Get anno failed, {name=} not found in {self.anno_dir}")
            return None
        return p.read_text(encoding="utf-8")

    def save_zlabel(self, filename: str) -> bool:
        src = Path(filename)
        if not src.exists():
            return False
        if src.parent == self.anno_dir:
            return True
        self.anno_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, self.anno_dir / src.name)
        return True

    def preupload_image(self, anno_id: str, image: Image.Image):
        return None


class LocalInference:
    requires_server = False

    def __init__(
        self,
        storage: Storage,
        model_name: str = "EdgeSAM",
        encoder_path: str = "",
        decoder_path: str = "",
    ) -> None:
        self.storage = storage
        self.model_name = model_name
        self.encoder_path = encoder_path or str(resource_dir() / "edge_sam_3x_encoder.onnx")
        self.decoder_path = decoder_path or str(resource_dir() / "edge_sam_3x_decoder.onnx")
        self.logger = ZLogger("LocalInference")
        self._model: Any = None
        self._lock = threading.Lock()
        self.model_status: str = "idle"  # idle | ready | error
        self.model_error: str = ""

    def _get_model(self):
        with self._lock:
            if self._model is None:
                if self.model_status == "error":
                    raise RuntimeError(self.model_error)
                try:
                    from zlabel.models.sam_onnx import SAM2, EdgeSam, SamOnnxModel

                    cls = {"SAM": SamOnnxModel, "EdgeSAM": EdgeSam, "SAM2": SAM2}.get(
                        self.model_name, EdgeSam
                    )
                    self.logger.info(
                        f"Loading local model {cls.__name__}: encoder={self.encoder_path}, decoder={self.decoder_path}"
                    )
                    self._model = cls(self.encoder_path, self.decoder_path)
                    self.model_status = "ready"
                except Exception as e:
                    self.model_status = "error"
                    self.model_error = str(e)
                    self.logger.error(f"Failed to load local model, {e=}")
                    raise
        return self._model

    def predict(
        self,
        anno_id: str,
        image_name: str,
        points: list[tuple[float, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[tuple[float, float, float, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
        return_type: int = 1,
    ) -> dict[str, Any]:
        from zlabel.models.ztypes import Point, Rect, SamReturn
        from zlabel.utils.enums import AutoMode, ReturnType

        auto_mode = AutoMode(mode)
        img = self.storage.get_image(image_name)
        if img is None:
            return SamReturn(
                anno_id=anno_id,
                status=False,
                mode=auto_mode.name,
                msg=f"image not found: {image_name}",
            ).model_dump()

        try:
            # zlabel.models.worker imports cv2 + onnxruntime at module level,
            # so it may not be importable on remote-only installs.
            from zlabel.models.worker import ZSamWorker
        except ImportError as e:
            self.logger.error(f"Local inference deps not installed, {e=}")
            return SamReturn(
                anno_id=anno_id,
                status=False,
                mode=auto_mode.name,
                msg=f"local inference deps not installed: {e}",
            ).model_dump()

        try:
            model = self._get_model()
        except Exception as e:
            return SamReturn(
                anno_id=anno_id,
                status=False,
                mode=auto_mode.name,
                msg=str(e),
            ).model_dump()

        np_img = np.asarray(img.convert("RGB"), dtype=np.uint8)
        worker = ZSamWorker(
            model=model,
            anno_id=anno_id,
            img=np_img,
            auto_mode=auto_mode,
            threshold=threshold,
            return_type=ReturnType(return_type),
        )
        try:
            # ZSamPredictWorker sends the wire format ({x,y} / {x,y,w,h} dicts);
            # accept plain tuples too so direct callers/tests keep working.
            if points is not None and labels is not None and len(points) == len(labels):
                pts = [
                    Point(x=p["x"], y=p["y"]) if isinstance(p, dict) else Point(x=p[0], y=p[1])
                    for p in points
                ]
                data = worker.run_point(pts, labels)
                status, msg = True, "success"
            elif rects is not None:
                rs = [
                    Rect(x=r["x"], y=r["y"], w=r["w"], h=r["h"])
                    if isinstance(r, dict)
                    else Rect(x=r[0], y=r[1], w=r[2], h=r[3])
                    for r in rects
                ]
                data = worker.run_rect(rs)
                status, msg = True, "success"
            else:
                data, status, msg = (
                    None,
                    False,
                    f"Either points/label/rects is None, {anno_id=}",
                )
        except Exception as e:
            self.logger.error(f"Predict failed, {e=}")
            data, status, msg = None, False, str(e)
        return SamReturn(
            anno_id=anno_id,
            status=status,
            mode=auto_mode.name,
            msg=msg,
            data=data,
        ).model_dump()


class ZLabelBackend:
    def __init__(self, inference: Inference, storage: Storage) -> None:
        self.inference = inference
        self.storage = storage

    @property
    def logger(self) -> ZLogger:
        return getattr(self.storage, "logger", ZLogger("ZLabelBackend"))

    @property
    def user_token(self) -> str:
        return getattr(self.storage, "user_token", "")

    @property
    def needs_login(self) -> bool:
        return self.storage.requires_server or self.inference.requires_server

    @property
    def anno_dir(self) -> Path | None:
        """Directory where the storage backend keeps annotations, if any."""
        return getattr(self.storage, "anno_dir", None)

    def login(self, username: str = "", password: str = "") -> str | None:
        return self.storage.login(username, password)

    def get_projects(self) -> list[dict[str, int | str]] | None:
        return self.storage.get_projects()

    def get_tasks(
        self,
        project_id: int = -1,
        num: int = 50,
        finished: int = 1,
        random_select: bool = True,
    ) -> list[dict[str, Any]] | None:
        return self.storage.get_tasks(project_id, num, finished, random_select)

    def get_image(self, name: str) -> Image.Image | None:
        return self.storage.get_image(name)

    def get_zlabel(self, name: str) -> str | None:
        return self.storage.get_zlabel(name)

    def save_zlabel(self, filename: str) -> bool | None:
        return self.storage.save_zlabel(filename)

    def preupload_image(self, anno_id: str, image: Image.Image):
        return self.storage.preupload_image(anno_id, image)

    def predict(
        self,
        anno_id: str,
        image_name: str,
        points: list[tuple[float, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[tuple[float, float, float, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
        return_type: int = 1,
    ) -> dict[str, Any]:
        return self.inference.predict(
            anno_id=anno_id,
            image_name=image_name,
            points=points,
            labels=labels,
            rects=rects,
            threshold=threshold,
            mode=mode,
            return_type=return_type,
        )


def build_backend(settings: Any) -> ZLabelBackend:
    """Build a backend from settings.

    inference_mode and storage are independent axes:
    - remote/remote: today's behavior (HTTP predict + OpenList storage)
    - local/remote: in-process inference + remote OpenList storage
    - local/local: fully offline

    remote inference + local storage is invalid (the server cannot fetch the
    local image), so it silently falls back to local inference.
    """
    storage_mode = getattr(settings.project, "storage_mode", "remote")
    inference_mode = getattr(settings, "inference_mode", "remote")

    api: ZLServerApiHelper | None = None
    if storage_mode == "local":
        storage: Storage = LocalStorage(
            root_dir=settings.root_dir,
            project_name=settings.project_name,
            local_dir=getattr(settings.project, "local_dir", ""),
        )
    else:
        api = ZLServerApiHelper(settings.username, settings.password, settings.host)
        storage = RemoteStorage(api)

    if inference_mode == "local" or storage_mode == "local":
        inference: Inference = LocalInference(
            storage=storage,
            model_name=getattr(settings, "model_name", "EdgeSAM"),
            encoder_path=getattr(settings, "encoder_path", ""),
            decoder_path=getattr(settings, "decoder_path", ""),
        )
    else:
        assert api is not None
        inference = RemoteInference(api)
    return ZLabelBackend(inference=inference, storage=storage)
