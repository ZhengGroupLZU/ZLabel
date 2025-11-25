from pyqtgraph.Qt.QtCore import QObject, QThread, Signal

from zlabel.utils.api_helper import ZLServerApiHelper


class ZLoginThread(QThread):
    login_success = Signal(str)
    login_fail = Signal()

    def __init__(
        self,
        api: ZLServerApiHelper,
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
