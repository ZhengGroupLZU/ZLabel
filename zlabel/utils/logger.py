import logging
import os
from rich.logging import RichHandler

LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class ZLogger(logging.Logger):
    def __init__(self, name: str, level: str | None = None) -> None:
        level = level or "DEBUG"
        level_ = LEVEL_MAP.get(str(level), logging.DEBUG)
        super().__init__(name, level_)
        self.format = "%(asctime)s-%(message)s"
        self.addHandler(RichHandler(rich_tracebacks=True))

    def setLevel(self, level: str | int) -> None:
        if isinstance(level, str):
            level = LEVEL_MAP.get(level, logging.DEBUG)
        super().setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)
