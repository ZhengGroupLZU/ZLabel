import os
from typing import Optional

from qtpy.QtCore import QObject, QThread, Signal

from zlabel.utils import AlistApiHelper


class ZLoginThread(QThread):
    login_success = Signal(str)
    login_fail = Signal()

    def __init__(
        self,
        api: AlistApiHelper,
        username: str,
        password: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.api = api
        self.username = username
        self.password = password

    def run(self) -> None:
        token = self.api.login(self.username, self.password)
        if token is None:
            self.login_fail.emit()
        else:
            self.login_success.emit(token)
        self.finished.emit()


class ZUploadFileThread(QThread):
    success = Signal(str)
    fail = Signal(str)

    def __init__(
        self,
        api: AlistApiHelper,
        filename: str,
        username: str | None = None,
        password: str | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.api = api
        self.filename = filename
        self.username = username
        self.password = password

    def run(self) -> None:
        if not self.api.user_token and self.username and self.password:
            self.api.login(self.username, self.password)
        if os.path.exists(self.filename):
            r = self.api.upload_file(self.filename)
            if isinstance(r, str):
                self.fail.emit(f"Upload failed with {r=}")
            else:
                self.success.emit("Upload success!")
        self.finished.emit()
