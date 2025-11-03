import copy
import os
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import requests
import json
from io import BytesIO
from PIL import Image

from zlabel.utils.logger import ZLogger


class AlistApiHelper(object):
    def __init__(
        self,
        host: str = "",
        url_prefix: str = "",
    ) -> None:
        self.logger = ZLogger("AlistApiHelper")
        self.host = host
        self.url_prefix = url_prefix

        self.username = ""
        self.password = ""
        self.user_token = ""
        self.headers = {"User-Agent": "ZLabel/1.0.0"}

    def login(self, username: str, password: str):
        self.username = username
        self.password = password
        body = {
            "username": username,
            "password": password,
        }
        payload = json.dumps(body)
        url = f"{self.host}/api/auth/login"
        headers = copy.deepcopy(self.headers)
        headers["Content-Type"] = "application/json"
        try:
            response = requests.post(url, data=payload, headers=headers)
            if response.status_code == 200:
                user_token: str = response.json()["data"]["token"]
                self.user_token = user_token
                return user_token
        except Exception as e:
            self.logger.error(f"login error with {e=}")
            return None

    def get_img_url(self, name: str):
        return f"{self.host}/{self.url_prefix}/{name}"

    def get_image_by_api(self, url: str, token: str | None = None):
        token = token or self.user_token
        if token is None:
            self.logger.error("No user_token, login first")
            return None
        headers = copy.deepcopy(self.headers)
        headers["Authorization"] = token  # type: ignore
        resp = requests.get(url, headers=headers, stream=True)
        if resp.status_code == 200:
            try:
                # bio = BytesIO(resp.content)
                # bio.seek(0)
                resp.raw.decode_content = True
                image = Image.open(resp.raw)
                return image
            except Exception as e:
                self.logger.error(f"Convert to image failed, {e=}")
        self.logger.error(f"Get {url=} failed, {resp.status_code=}, {resp.text=}")
        return None

    def get_image_by_name(self, name: str):
        url = self.get_img_url(name)
        return self.get_image_by_api(url)

    def upload_file(self, filename: str):
        url = f"{self.host}/api/fs/put"
        fs = open(filename, "r", encoding="utf-8")
        data = fs.read().encode("utf-8")
        fs.close()

        headers = {
            "Authorization": self.user_token,
            "User-Agent": "ZLabel/1.0.0",
            "Content-Type": "text/plain",
            # "Content-Length": f"{length}",
            "File-Path": "",
        }
        resp = None
        msg = []
        for path in [
            f"/labelspace/{self.username}/{filename}",
            f"/datasets/seeds_data/exported_pngs_label/{Path(filename).name}",
        ]:
            headers["File-Path"] = path
            try:
                resp = requests.put(url, data=data, headers=headers)
                if resp.status_code == 200:
                    if resp.json()["message"] == "success":
                        msg.append("success")
            except Exception as e:
                self.logger.error(f"Upload file failed, {e=}, {resp=}")
                msg.append(resp.text if resp else str(e))
        return ", ".join(msg)

    def get_anno_by_api(self, url: str, token: str | None = None):
        token = token or self.user_token
        if token is None:
            self.logger.error("No user_token, login first")
            return None
        headers = copy.deepcopy(self.headers)
        headers["Authorization"] = token  # type: ignore
        resp = None
        try:
            resp = requests.get(url, headers=headers)
            return resp.text
        except Exception as e:
            if resp is not None:
                self.logger.error(f"Get {url=} failed, {e=}, {resp.text=}")
            else:
                self.logger.error(f"Get {url=} failed, {e=}")
            return None

    def get_anno_by_name(self, name: str):
        url = f"{self.host}/d/datasets/seeds_data/exported_pngs_label/{name}"
        return self.get_anno_by_api(url)


class SamApiHelper(object):
    def __init__(
        self,
        username: str,
        password: str,
        sam_api: str = "http://127.0.0.1:8000",
    ) -> None:
        self.logger = ZLogger("SamApiHelper")
        self.username = username
        self.password = password
        self.user_token = ""

        self.sam_api: str = sam_api
        self.login_api: str = f"{self.sam_api}/api/v1/login"
        self.predict_api: str = f"{self.sam_api}/api/v1/predict"
        self.set_image_api: str = f"{self.sam_api}/api/v1/set_image"
        self.get_image_api: str = f"{self.sam_api}/api/v1/get_image"
        self.get_zlabel_api: str = f"{self.sam_api}/api/v1/get_zlabel"
        self.save_zlabel_api: str = f"{self.sam_api}/api/v1/save_zlabel"
        self.get_tasks_api: str = f"{self.sam_api}/api/v1/get_tasks"

        self.headers = {
            "User-Agent": "ZLabel/1.0.0",
        }

    def predict_v0(
        self,
        anno_id: str,
        image: Image.Image,
        points: List[Dict[str, float]] | None = None,
        labels: List[float] | None = None,
        rects: List[Dict[str, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
    ) -> Dict[str, Any]:
        anno = {
            "id": anno_id,
            "points": points,
            "labels": labels,
            "rects": rects,
        }
        data = {
            "data": json.dumps(anno),
            "threshold": threshold,
            "mode": mode,
        }
        img = BytesIO()
        image.save(img, format="png")
        files = {"image": (anno_id, img.getvalue())}

        resp = requests.post(self.predict_api, data=data, files=files)
        try:
            return resp.json()
        except Exception:
            print(f"Predict Failed, {resp.text=}")
            return {"anno_id": anno_id, "status": False, "msg": resp.text}

    def predict(
        self,
        anno_id: str,
        image_name: str,
        points: List[Dict[str, float]] | None = None,
        labels: List[float] | None = None,
        rects: List[Dict[str, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
        return_type: int = 1,  # RECT = 1 POLYGON = 2 RLE = 3
    ) -> Dict[str, Any]:
        anno = {
            "id": anno_id,
            "points": points,
            "labels": labels,
            "rects": rects,
        }
        data = {
            "data": json.dumps(anno),
            "threshold": threshold,
            "mode": mode,
            "image_name": image_name,
            "return_type": return_type,
        }
        resp = requests.post(self.predict_api, data=data, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()["data"]
        self.logger.warning(f"Predict Failed, {resp.text=}")
        return {"anno_id": anno_id, "status": False, "msg": resp.text}

    def preupload_image(self, anno_id: str, image: Image.Image):
        img = BytesIO()
        image.save(img, format="png")
        files = {"image": (anno_id, img.getvalue())}

        try:
            resp = requests.post(self.set_image_api, files=files)
            self.logger.info(f"Uploaded image, {resp.text=}")
        except Exception as e:
            self.logger.error(f"Uploaded image Failed, {e=}")

    def login(self, username: str = "", password: str = "") -> str | None:
        self.username = username or self.username
        self.password = password or self.password
        resp = requests.post(
            self.login_api,
            params={"username": self.username, "password": self.password},
            headers=self.headers,
        )
        try:
            resp_json: dict = resp.json()
        except Exception as e:
            self.logger.error(f"Login failed, parse json error, {e=}, {resp.text=}")
            return None

        if resp.status_code == 200 and resp_json.get("message", None) == "success":
            self.user_token = resp_json["data"]["token"]
            self.headers["Authorization"] = self.user_token
            return self.user_token
        else:
            self.logger.error(f"Login failed, {resp_json=}")
            return None

    def get_image(self, name: str):
        resp = requests.get(self.get_image_api, params={"name": name}, headers=self.headers)
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content))
        else:
            self.logger.error(f"Get image failed, {resp.text=}")
            return None

    def get_zlabel(self, name: str):
        resp = requests.get(self.get_zlabel_api, params={"name": name}, headers=self.headers)
        if resp.status_code == 200:
            return resp.text
        else:
            self.logger.error(f"Get anno failed, {resp.text=}")
            return None

    def get_tasks(self, num: int = 50, finished: int = 1):
        """
        finished: -1: all, 0: unfinished, 1: finished
        """
        resp = requests.get(
            self.get_tasks_api,
            params={"num": num, "finished": finished},
            headers=self.headers,
        )
        if resp.status_code == 200:
            return resp.json()["data"]
        else:
            self.logger.error(f"Get tasks failed, {resp.text=}")

    def save_zlabel(self, filename: str):
        fs = open(filename, "r", encoding="utf-8")
        data = fs.read().encode("utf-8")
        fs.close()
        form = {
            "username": self.username,
            "zlabel": data,
            "filename": Path(filename).name,
        }
        resp = requests.put(self.save_zlabel_api, data=form, headers=self.headers)
        if resp.status_code == 200:
            self.logger.info(resp.text)
            d = resp.json()
            if d["message"] == "success":
                return True
        else:
            self.logger.error(f"Save anno failed, {resp.text=}")
