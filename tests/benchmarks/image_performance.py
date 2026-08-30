"""ZLabel image rendering performance benchmark.

This is a standalone, headless-friendly benchmark inspired by pyqtgraph's
VideoSpeedTest.py.  It measures:

  * Canvas pan / zoom FPS (the main interaction bottleneck)
  * Canvas + RawImageWidget + RawImageGLWidget setImage() update FPS
  * ImageItem.render() / display build / GL texture upload timings

Usage::

    uv run python benchmarks/image_performance.py
    uv run python benchmarks/image_performance.py --size 8000x6000 --duration 2
    uv run python benchmarks/image_performance.py --backend canvas
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass, field

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.widgets.RawImageWidget import RawImageWidget

try:
    from pyqtgraph.widgets.RawImageWidget import RawImageGLWidget
except Exception:  # pragma: no cover - optional OpenGL widget
    RawImageGLWidget = None

from zlabel.widgets.canvas import DISPLAY_MAX_SIDE, Canvas
from zlabel.widgets.zworker import build_display_image

pg.setConfigOptions(useOpenGL=True, imageAxisOrder="row-major", useCupy=False, useNumba=False)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def make_image(height: int, width: int, seed: int = 0) -> np.ndarray:
    """Generate a large RGB uint8 test image with some spatial structure."""
    rng = np.random.default_rng(seed)
    img = rng.integers(0, 255, (height, width, 3), dtype=np.uint8)
    # add a smooth gradient so pan/zoom has visible content, not pure noise
    yy, xx = np.mgrid[0:height, 0:width]
    img[..., 0] = (img[..., 0] + (xx * 255 // max(1, width)) // 4).astype(np.uint8)
    img[..., 1] = (img[..., 1] + (yy * 255 // max(1, height)) // 4).astype(np.uint8)
    return np.ascontiguousarray(img)


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------
@dataclass
class BenchResult:
    name: str
    action: str
    frames: int
    elapsed: float
    fps: float
    notes: str = ""

    def as_row(self) -> tuple[str, str, float, float, int]:
        return self.name, self.action, self.fps, self.elapsed, self.frames


@dataclass
class BenchSuite:
    results: list[BenchResult] = field(default_factory=list)

    def add(self, name: str, action: str, frames: int, elapsed: float, notes: str = ""):
        self.results.append(
            BenchResult(name=name, action=action, frames=frames, elapsed=elapsed, fps=frames / elapsed, notes=notes)
        )

    def print_table(self):
        width_name = max(len(r.name) for r in self.results + [BenchResult("Backend", "", 0, 0, 0)])
        width_action = max(len(r.action) for r in self.results + [BenchResult("", "Action", 0, 0, 0)])
        print()
        print(
            f"{'Backend':<{width_name}}  {'Action':<{width_action}}  {'FPS':>10}  {'Frames':>8}  {'Seconds':>8}  Notes"
        )
        print("-" * (width_name + width_action + 50))
        for r in self.results:
            print(
                f"{r.name:<{width_name}}  {r.action:<{width_action}}  {r.fps:>10.1f}  "
                f"{r.frames:>8}  {r.elapsed:>8.2f}  {r.notes}"
            )
        print()


def run_loop(callback, duration: float, app: QtWidgets.QApplication) -> tuple[int, float]:
    """Call ``callback`` as fast as possible for ``duration`` seconds.

    ``app.processEvents()`` is called after every frame so Qt paints the
    widgets and delivers timer events.
    """
    start = time.perf_counter()
    frames = 0
    phase = 0.0
    while True:
        now = time.perf_counter()
        if now - start >= duration:
            break
        phase += 0.06
        callback(phase)
        app.processEvents()
        frames += 1
    elapsed = time.perf_counter() - start
    return frames, elapsed


# ---------------------------------------------------------------------------
# Canvas scenarios
# ---------------------------------------------------------------------------
def create_canvas(img: np.ndarray, show: bool = True) -> Canvas:
    canvas = Canvas()
    canvas.resize(1100, 750)
    canvas.update_image(img)
    canvas.fit_view()
    if show:
        canvas.show()
    return canvas


def canvas_pan_step(canvas: Canvas, phase: float):
    h, w = canvas._image_hw
    vw = w * 0.35
    vh = h * 0.35
    cx = w / 2 + w * 0.25 * math.sin(phase)
    cy = h / 2 + h * 0.25 * math.cos(phase * 0.7)
    x0 = min(max(cx - vw / 2, 0.0), w - vw)
    y0 = min(max(cy - vh / 2, 0.0), h - vh)
    canvas.view_box.setRange(xRange=[x0, x0 + vw], yRange=[y0, y0 + vh], padding=0)


def canvas_zoom_step(canvas: Canvas, phase: float):
    h, w = canvas._image_hw
    scale = 0.2 + 1.8 * (0.5 + 0.5 * math.sin(phase))
    vw = w / scale
    vh = h / scale
    cx, cy = w / 2, h / 2
    x0 = cx - vw / 2
    y0 = cy - vh / 2
    canvas.view_box.setRange(xRange=[x0, x0 + vw], yRange=[y0, y0 + vh], padding=0)


def bench_canvas_motion(canvas: Canvas, action: str, duration: float, app) -> BenchResult:
    if action == "pan":
        step = canvas_pan_step
    elif action == "zoom":
        step = canvas_zoom_step
    else:
        raise ValueError(action)

    start = time.perf_counter()
    frames = 0
    phase = 0.0
    while time.perf_counter() - start < duration:
        phase += 0.06
        step(canvas, phase)
        app.processEvents()
        frames += 1
    elapsed = time.perf_counter() - start
    return BenchResult("Canvas(GLImageItem)", action, frames, elapsed, fps=frames / elapsed)


def bench_setimage(widget, arr: np.ndarray, duration: float, app) -> BenchResult:
    def step(_phase):
        if hasattr(widget, "autoDownsample"):
            # ImageItem accepts autoLevels / autoRange keywords
            widget.setImage(arr, autoLevels=False, levels=(0, 255))
        else:
            # RawImageWidget / RawImageGLWidget forward kwargs to makeARGB
            widget.setImage(arr, levels=(0, 255))

    frames, elapsed = run_loop(step, duration, app)
    return BenchResult(type(widget).__name__, "setImage", frames, elapsed, fps=frames / elapsed)


# ---------------------------------------------------------------------------
# Render / display timing
# ---------------------------------------------------------------------------
def bench_render_and_display(img: np.ndarray, app: QtWidgets.QApplication) -> dict[str, object]:
    canvas = create_canvas(img, show=False)
    result: dict[str, object] = {}

    t0 = time.perf_counter()
    canvas.update_image(img)
    result["display_build_ms"] = (time.perf_counter() - t0) * 1000.0

    # force a full ImageItem render (downsample disabled; measures QImage path)
    item = canvas.image_item
    item._renderRequired = True
    item._imageHasNans = None
    t0 = time.perf_counter()
    item.render()
    result["imageitem_render_ms"] = (time.perf_counter() - t0) * 1000.0
    canvas.close()

    # GL texture upload for the single display texture.
    gl_canvas = create_canvas(img, show=True)
    app.processEvents()
    gl_item = gl_canvas.image_item
    upload_ms: float | None = None
    if hasattr(gl_item, "_sync_texture") and gl_item._gl_state is not None:
        viewport = gl_canvas.viewport()
        viewport.makeCurrent()
        try:
            gl_item._texture_image = None  # force a real upload
            t0 = time.perf_counter()
            gl_item._sync_texture(viewport)
            upload_ms = (time.perf_counter() - t0) * 1000.0
        finally:
            viewport.doneCurrent()
    result["texture_upload_ms"] = upload_ms
    gl_canvas.close()
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_size(text: str) -> tuple[int, int]:
    try:
        h, w = (int(x) for x in text.lower().split("x"))
    except Exception:
        raise argparse.ArgumentTypeError("size must look like 6000x4000 (height x width)")
    return h, w


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", default="6000x4000", type=parse_size, help="image size HEIGHTxWIDTH, e.g. 6000x4000")
    parser.add_argument("--duration", default=3.0, type=float, help="seconds per benchmark scenario (default: 3)")
    parser.add_argument(
        "--backend",
        default="all",
        choices=["canvas", "raw", "rawgl", "all"],
        help="which backends to include (default: all)",
    )
    parser.add_argument(
        "--action",
        default="all",
        choices=["pan", "zoom", "setimage", "all"],
        help="which scenario to run (default: all)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    height, width = args.size
    duration = max(0.1, args.duration)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1])

    print(f"Image: {width}x{height} RGB uint8, duration={duration:.1f}s per scenario")

    img = make_image(height, width)
    display = build_display_image(img, DISPLAY_MAX_SIDE)
    suite = BenchSuite()

    include_canvas = args.backend in ("canvas", "all")
    include_raw = args.backend in ("raw", "all")
    include_rawgl = args.backend in ("rawgl", "all") and RawImageGLWidget is not None

    if not (include_canvas or include_raw or include_rawgl):
        print("RawImageGLWidget is not available; nothing to run.")
        return 1

    # ---- Canvas pan / zoom ----
    if include_canvas and args.action in ("pan", "all"):
        canvas = create_canvas(img)
        suite.results.append(bench_canvas_motion(canvas, "pan", duration, app))
        canvas.close()

    if include_canvas and args.action in ("zoom", "all"):
        canvas = create_canvas(img)
        suite.results.append(bench_canvas_motion(canvas, "zoom", duration, app))
        canvas.close()

    # ---- setImage throughput on every backend ----
    if args.action in ("setimage", "all"):
        if include_canvas:
            canvas = create_canvas(img)
            suite.results.append(bench_setimage(canvas.image_item, display, duration, app))
            canvas.close()

        if include_raw:
            raw = RawImageWidget()
            raw.resize(1100, 750)
            raw.show()
            suite.results.append(bench_setimage(raw, display, duration, app))
            raw.close()

        if include_rawgl and RawImageGLWidget is not None:
            rawgl = RawImageGLWidget()
            rawgl.resize(1100, 750)
            rawgl.show()
            suite.results.append(bench_setimage(rawgl, display, duration, app))
            rawgl.close()

    # ---- render / display timings ----
    if include_canvas and args.action in ("all", "pan", "zoom", "setimage"):
        timings = bench_render_and_display(img, app)
        print(f"\nDisplay build:           {timings['display_build_ms']:.2f} ms")
        print(f"ImageItem.render():      {timings['imageitem_render_ms']:.2f} ms")
        upload_ms = timings.get("texture_upload_ms")
        if upload_ms is not None:
            print(f"GL texture upload:        {upload_ms:.2f} ms")
        else:
            print("GL texture upload:        n/a (non-GL fallback)")

    suite.print_table()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
