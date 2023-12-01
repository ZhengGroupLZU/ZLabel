import logging
from rich.logging import RichHandler


class ZLogger(logging.Logger):
    def __init__(self, name: str, level: int = logging.DEBUG) -> None:
        super().__init__(name, level)
        self.format = "%(asctime)s-%(message)s"
        self.addHandler(RichHandler(rich_tracebacks=True))
