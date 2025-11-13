import json
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from zlabel.utils.logger import ZLogger


class ZLServerApiHelper:
    def __init__(
        self,
        username: str,
        password: str,
        sam_api: str = "http://127.0.0.1:8000",
    ) -> None:
        self.logger = ZLogger("ZLServerApiHelper")
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
        self.get_projects_api: str = f"{self.sam_api}/api/v1/get_projects"
        self.get_tasks_api: str = f"{self.sam_api}/api/v1/get_tasks"

        self.headers = {
            "User-Agent": "ZLabel/1.0.0",
        }

    def predict_v0(
        self,
        anno_id: str,
        image: Image.Image,
        points: list[dict[str, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[dict[str, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
    ) -> dict[str, Any]:
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
        points: list[dict[str, float]] | None = None,
        labels: list[float] | None = None,
        rects: list[dict[str, float]] | None = None,
        threshold: int = 100,
        mode: int = 1,
        return_type: int = 1,  # RECT = 1 POLYGON = 2 RLE = 3
    ) -> dict[str, Any]:
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
            resp_json: dict[str, Any] = resp.json()
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

    def get_projects(self) -> list[dict[str, int | str]] | None:
        """
        {
            "message": "success",
            "data": [
                {
                    "id": project.id,
                    "name": project.name,
                }
            ]
        }
        """
        resp = requests.get(self.get_projects_api, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()["data"]
        else:
            self.logger.error(f"Get projects failed, {resp.text=}")
            return None

    def get_tasks(self, project_id: int = -1, num: int = 50, finished: int = 1):
        """
        finished: -1: all, 0: unfinished, 1: finished
        """
        resp = requests.get(
            self.get_tasks_api,
            params={"project_id": project_id, "num": num, "finished": finished},
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
