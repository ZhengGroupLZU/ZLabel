"""MNN runtime backends using the Module API (MNN.nn.load_module_from_file + onForward)."""

from __future__ import annotations

from pathlib import Path

import MNN.expr as expr
import numpy as np
from MNN.nn import load_module_from_file

#: user-facing inference backend -> MNN backend (None = leave to MNN default / CPU)
BACKEND_MAP: dict[str, object] = {
    "AUTO": None,
    "CPU": expr.Backend.CPU,
    "CUDA": expr.Backend.CUDA,
    "Metal": expr.Backend.METAL,
    "OpenCL": expr.Backend.OPENCL,
}

_FLOAT = expr.float
_INT = expr.int
_INT64 = expr.int64


def configure_backend(backend: str = "AUTO", threads: int = 4) -> None:
    """Configure the global executor. Best-effort: failures fall back to defaults."""
    try:
        expr.set_thread_number(max(1, int(threads)))
    except Exception:
        pass
    target = BACKEND_MAP.get(backend)
    if target is None or backend == "AUTO":
        return
    try:
        expr.set_global_executor_config({"backend": target, "numThread": max(1, int(threads))})
    except Exception:
        # backend unavailable (e.g. no GPU); MNN keeps the default (CPU)
        pass


def _make_input(arr: np.ndarray) -> object:
    if arr.dtype.kind == "i":
        return expr.const(arr.astype(np.int32).tolist(), list(arr.shape), expr.NCHW, _INT)
    arr = arr.astype(np.float32)
    return expr.const(arr.tolist(), list(arr.shape), expr.NCHW, _FLOAT)


class MnnModule:
    """A single MNN model loaded with the Module API; run() returns outputs by name."""

    def __init__(self, model_path: str, input_names: list[str] | None = None, output_names: list[str] | None = None):
        self.path = str(Path(model_path))
        self._net = load_module_from_file(self.path, [], [])
        info = self._net.get_info()
        self.input_names: list[str] = list(input_names or info.get("inputNames") or [])
        self.output_names: list[str] = list(output_names or info.get("outputNames") or [])

    def run(self, feeds: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        inputs = [_make_input(feeds[name]) for name in self.input_names]
        outs = self._net.forward(inputs)
        return {name: out.read() for name, out in zip(self.output_names, outs)}
