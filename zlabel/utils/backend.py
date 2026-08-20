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
        crop_box: tuple[int, int, int, int] | None = None,  # (l, t, r, b) in image coords
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

    def __init__(
        self,
        api: ZLServerApiHelper,
        storage: Storage | None = None,
        upload_image_size: int = 1024,
    ) -> None:
        self.api = api
        self.storage = storage
        self.upload_image_size = upload_image_size
        self._last_image: str | None = None

    def login(self, username: str = "", password: str = "") -> str | None:
        return self.api.login(username, password)

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
        crop_box: tuple[int, int, int, int] | None = None,
    ) -> dict[str, Any]:
        # With local storage the image only exists on this machine, so upload it
        # along with every predict (the server uses the uploaded file directly).
        # set_image is still called when the image changes to pre-warm the model
        # and cache the bytes server-side. The image is resized (long edge capped
        # at upload_image_size) before upload to bound bandwidth.
        image = None
        scale = None
        crop_off = (0, 0)
        is_local = self.storage is not None and not getattr(self.storage, "requires_server", True)
        if is_local:
            from zlabel.models.ztypes import SamReturn

            orig = self.storage.get_image(image_name)
            if orig is None:
                return SamReturn(
                    anno_id=anno_id,
                    status=False,
                    mode="",
                    msg=f"image not found: {image_name}",
                ).model_dump()
            box = _clip_crop_box(crop_box, orig.width, orig.height)
            if box is not None:
                left, top, right, bottom = box
                crop_off = (left, top)
                orig = orig.crop((left, top, right, bottom))
            image = _resize_long_edge(orig, self.upload_image_size)
            if image.size != orig.size:
                scale = (orig.size[0] / image.size[0], orig.size[1] / image.size[1])
            if image_name != self._last_image:
                if not self.api.set_image(image_name, image):
                    return SamReturn(
                        anno_id=anno_id,
                        status=False,
                        mode="",
                        msg=f"failed to upload image: {image_name}",
                    ).model_dump()
                self._last_image = image_name
        # Prompt coordinates are given in the full original image space: first
        # shift to the crop space, then (when the upload was resized) scale them
        # down to match the uploaded size.
        if crop_off != (0, 0) and (points or rects):
            if points:
                points = _translate_points(points, *crop_off)
            if rects:
                rects = _translate_rects(rects, *crop_off)
        if scale is not None and (points or rects):
            inv = (1.0 / scale[0], 1.0 / scale[1])
            if points:
                points = [
                    (
                        {"x": p["x"] * inv[0], "y": p["y"] * inv[1]}
                        if isinstance(p, dict)
                        else (p[0] * inv[0], p[1] * inv[1])
                    )
                    for p in points
                ]
            if rects:
                rects = [
                    {
                        "x": r["x"] * inv[0],
                        "y": r["y"] * inv[1],
                        "w": r["w"] * inv[0],
                        "h": r["h"] * inv[1],
                    }
                    if isinstance(r, dict)
                    else (r[0] * inv[0], r[1] * inv[1], r[2] * inv[0], r[3] * inv[1])
                    for r in rects
                ]
        resp = self.api.predict(
            anno_id=anno_id,
            image_name=image_name,
            points=points,
            labels=labels,
            rects=rects,
            threshold=threshold,
            mode=mode,
            return_type=return_type,
            image=image,
        )
        if scale is not None and resp.get("data"):
            resp = {**resp, "data": _scale_results(resp["data"], scale, image.size, orig.size)}
        if crop_off != (0, 0) and resp.get("data"):
            resp = {**resp, "data": _translate_results(resp["data"], *crop_off)}
        return resp


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
        tasks: list[dict[str, Any]] = []
        for rel, group, day in self._iter_images():
            anno_id = id_md5(f"{self.project_name}/{rel}")
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
            tasks.append({
                "id": len(tasks),
                "project_id": project_id,
                "anno_id": anno_id,
                "filename": rel,
                "labels": [],
                "finished": is_finished,
                "group": group,
                "day": day,
            })
        if random_select:
            random.shuffle(tasks)
        else:
            tasks.sort(key=lambda t: (t["group"], t["day"], t["filename"]))
        return tasks[:num]

    def _iter_images(self):
        """Yield (rel_path, group, day) for images under image_dir.

        Sequence layout `species/dish/D{n}.png` (two subdirs + D-numbered
        filename) is recognized as a group: group = "species/dish", day = n.
        Anything else yields group="" / day=0.
        """
        import re as _re

        for p in sorted(self.image_dir.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            rel = p.relative_to(self.image_dir).as_posix()
            m = _re.fullmatch(r"D(\d+)\.(?:png|jpe?g)", p.name, _re.IGNORECASE)
            parts = rel.split("/")
            group, day = "", 0
            if m is not None and len(parts) >= 3:
                group = "/".join(parts[:-1])
                day = int(m.group(1))
            yield rel, group, day

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
        model_dir: str = "",
        backend: str = "AUTO",
    ) -> None:
        self.storage = storage
        self.model_name = model_name
        self.model_dir = model_dir or str(resource_dir() / "models" / "mnn")
        self.backend = backend
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
                    from zlabel.models.process_backend import ProcessPredictor

                    self.logger.info(
                        f"Setting up local inference {self.model_name} from {self.model_dir} (backend={self.backend})"
                    )
                    self._model = ProcessPredictor(
                        model_dir=self.model_dir,
                        model_name=self.model_name,
                        backend=self.backend,
                    )
                    self.model_status = "ready"
                except Exception as e:
                    self.model_status = "error"
                    self.model_error = str(e)
                    self.logger.error(f"Failed to set up local inference, {e=}")
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
        crop_box: tuple[int, int, int, int] | None = None,
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

        # Optionally focus inference on the dish region: crop the image to the
        # dish bbox and shift the prompt coordinates by the same offset.
        crop_off = (0, 0)
        box = _clip_crop_box(crop_box, img.width, img.height)
        if box is not None:
            left, top, right, bottom = box
            crop_off = (left, top)
            img = img.crop((left, top, right, bottom))
        if crop_off != (0, 0):
            if points:
                points = _translate_points(points, *crop_off)
            if rects:
                rects = _translate_rects(rects, *crop_off)

        try:
            # zlabel.models.worker imports cv2 + MNN lazily at module level,
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

        np_img = np.asarray(img.convert("RGB"), dtype=np.uint8)[..., ::-1].copy()  # RGB -> BGR
        model.set_image(np_img)
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
                pts = [Point(x=p["x"], y=p["y"]) if isinstance(p, dict) else Point(x=p[0], y=p[1]) for p in points]
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
            if crop_off != (0, 0) and data:
                data = _translate_local_results(data, *crop_off)
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
        token = self.storage.login(username, password)
        infer_login = getattr(self.inference, "login", None)
        if infer_login is not None:
            token = infer_login(username, password) or token
        return token

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
        crop_box: tuple[int, int, int, int] | None = None,
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
            crop_box=crop_box,
        )


def _resize_long_edge(image: Image.Image, max_side: int) -> Image.Image:
    """Aspect-preserving resize so the long edge is at most ``max_side`` px.

    Images already smaller are returned unchanged (no upscaling).
    """
    w, h = image.size
    if max(w, h) <= max_side:
        return image
    r = max_side / max(w, h)
    return image.resize((max(1, round(w * r)), max(1, round(h * r))), Image.Resampling.LANCZOS)


def _scale_results(
    data: list[Any],
    scale: tuple[float, float],
    upload_hw: tuple[int, int],
    orig_hw: tuple[int, int],
) -> list[Any]:
    """Map Rect/Polygon/RLE results from the uploaded (resized) image back to the
    original image pixel coordinates by multiplying by the resize scale."""
    from zlabel.models.ztypes import Polygon

    sx, sy = scale
    out: list[Any] = []
    for item in data:
        if isinstance(item, str):
            out.append(_scale_rle(item, upload_hw, orig_hw))
        elif isinstance(item, dict) and "points" in item:
            out.append({"points": [{"x": p["x"] * sx, "y": p["y"] * sy} for p in item["points"]]})
        elif isinstance(item, dict) and {"x", "y", "w", "h"} <= set(item):
            out.append({
                "x": item["x"] * sx,
                "y": item["y"] * sy,
                "w": item["w"] * sx,
                "h": item["h"] * sy,
            })
        else:
            out.append(item)
    return out


def _scale_rle(
    rle: str,
    upload_hw: tuple[int, int],
    orig_hw: tuple[int, int],
) -> str:
    """Decode an RLE mask at upload size, resize to the original size, re-encode."""
    from zlabel.models.ztypes import Polygon

    uw, uh = upload_hw
    ow, oh = orig_hw
    mask = Polygon.rle_decode(rle, (uh, uw))
    img = Image.fromarray((mask * 255).astype(np.uint8))
    img = img.resize((ow, oh), Image.Resampling.NEAREST)
    return Polygon.rle_encode((np.asarray(img) > 127).astype(np.uint8))


def _clip_crop_box(box: tuple[int, int, int, int] | None, w: int, h: int) -> tuple[int, int, int, int] | None:
    """Clip a (l, t, r, b) crop box to the image bounds; None when empty."""
    if box is None:
        return None
    left, top, right, bottom = (int(v) for v in box)
    left, top = max(0, left), max(0, top)
    right, bottom = min(w, right), min(h, bottom)
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom


def _translate_points(points, dx: float, dy: float):
    """Shift prompt points by (-dx, -dy) (full-image -> crop coordinates)."""
    out = []
    for p in points:
        if isinstance(p, dict):
            out.append({"x": p["x"] - dx, "y": p["y"] - dy})
        else:
            out.append((p[0] - dx, p[1] - dy))
    return out


def _translate_rects(rects, dx: float, dy: float):
    """Shift prompt rects by (-dx, -dy); size unchanged."""
    out = []
    for r in rects:
        if isinstance(r, dict):
            out.append({"x": r["x"] - dx, "y": r["y"] - dy, "w": r["w"], "h": r["h"]})
        else:
            out.append((r[0] - dx, r[1] - dy, r[2], r[3]))
    return out


def _translate_local_results(data, dx: float, dy: float):
    """Translate local Rect/Polygon results by (+dx, +dy) (crop -> full image)."""
    from zlabel.models.ztypes import Point, Polygon, Rect

    out = []
    for item in data:
        if isinstance(item, Rect):
            out.append(Rect(x=item.x + dx, y=item.y + dy, w=item.w, h=item.h))
        elif isinstance(item, Polygon):
            out.append(Polygon(points=[Point(x=p.x + dx, y=p.y + dy) for p in item.points]))
        else:
            out.append(item)  # RLE (str) left as-is
    return out


def _translate_results(data, dx: float, dy: float):
    """Translate wire-format Rect/Polygon result dicts by (+dx, +dy)."""
    out = []
    for item in data:
        if isinstance(item, dict) and "points" in item:
            out.append({"points": [{"x": p["x"] + dx, "y": p["y"] + dy} for p in item["points"]]})
        elif isinstance(item, dict) and {"x", "y", "w", "h"} <= set(item):
            out.append({"x": item["x"] + dx, "y": item["y"] + dy, "w": item["w"], "h": item["h"]})
        else:
            out.append(item)
    return out


def build_backend(settings: Any) -> ZLabelBackend:
    """Build a backend from settings.

    inference_mode and storage are independent axes:
    - remote/remote: HTTP predict + remote OpenList storage
    - local/remote: in-process inference + remote OpenList storage
    - local/local: fully offline
    - remote/local: local images are uploaded via set_image before each predict
      (server caches them by image_name); login goes through the inference API.
    """
    storage_mode = getattr(settings.project, "storage_mode", "remote")
    inference_mode = getattr(settings, "inference_mode", "remote")

    api = ZLServerApiHelper(settings.username, settings.password, settings.host)

    if storage_mode == "local":
        storage: Storage = LocalStorage(
            root_dir=settings.root_dir,
            project_name=settings.project_name,
            local_dir=getattr(settings.project, "local_dir", ""),
        )
    else:
        storage = RemoteStorage(api)

    if inference_mode == "local":
        inference: Inference = LocalInference(
            storage=storage,
            model_name=getattr(settings, "model_name", "EdgeSAM"),
            model_dir=getattr(settings, "model_dir", ""),
            backend=getattr(settings, "inference_backend", "AUTO"),
        )
    else:
        inference = RemoteInference(
            api=api,
            storage=storage,
            upload_image_size=getattr(settings, "upload_image_size", 1024),
        )
    return ZLabelBackend(inference=inference, storage=storage)
