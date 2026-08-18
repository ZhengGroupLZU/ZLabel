"""Geometry helpers for seed-germination annotations (dish ellipse fitting)."""

from __future__ import annotations

import math

import numpy as np


def fit_ellipse_polygon(points: list[tuple[float, float]], n: int = 36) -> list[tuple[float, float]] | None:
    """Fit an ellipse to contour points (OpenCV fitEllipse) and sample ``n`` points.

    Returns None when cv2 is unavailable or fewer than 5 points are given.
    """
    params = fit_ellipse_params(points)
    if params is None:
        return None
    cx, cy, angle, (ma_ax, mi_ax) = params
    t = np.linspace(0, 2.0 * np.pi, n, endpoint=False)
    a, b = ma_ax / 2.0, mi_ax / 2.0
    ang = np.deg2rad(angle)
    cos, sin = np.cos(t), np.sin(t)
    x = cx + a * cos * np.cos(ang) - b * sin * np.sin(ang)
    y = cy + a * cos * np.sin(ang) + b * sin * np.cos(ang)
    return [(float(xi), float(yi)) for xi, yi in zip(x, y)]


def fit_ellipse_params(
    points: list[tuple[float, float]],
) -> tuple[float, float, float, tuple[float, float]] | None:
    """Fit an ellipse to contour points, returning ``(cx, cy, angle_deg, (ma_ax, mi_ax))``.

    ``angle_deg`` is OpenCV's ellipse orientation (degrees). Returns None when
    cv2 is unavailable or fewer than 5 points are given. Useful to estimate the
    rotation of a dish between two frames for alignment.
    """
    try:
        import cv2
    except ImportError:
        return None
    pts = np.asarray(points, np.float32).reshape(-1, 1, 2)
    if len(pts) < 5:
        return None
    try:
        (cx, cy), (ma_ax, mi_ax), angle = cv2.fitEllipse(pts)
    except cv2.error:
        return None
    return float(cx), float(cy), float(angle), (float(ma_ax), float(mi_ax))


def rotate_point(
    p: tuple[float, float],
    angle_deg: float,
    center: tuple[float, float] = (0.0, 0.0),
) -> tuple[float, float]:
    """Rotate ``p`` around ``center`` by ``angle_deg`` degrees."""
    ang = math.radians(angle_deg)
    cos, sin = math.cos(ang), math.sin(ang)
    dx, dy = p[0] - center[0], p[1] - center[1]
    return (
        center[0] + dx * cos - dy * sin,
        center[1] + dx * sin + dy * cos,
    )


def rotate_rect(
    rect: tuple[float, float, float, float],
    angle_deg: float,
    center: tuple[float, float],
) -> tuple[float, float, float, float]:
    """Rotate a (x, y, w, h) rect around ``center`` by ``angle_deg``.

    The rotation is applied to the rect's anchor corner, so the returned rect
    stays axis-aligned at the rotated anchor; width/height are unchanged.
    """
    x, y = rotate_point((rect[0], rect[1]), angle_deg, center)
    return (x, y, rect[2], rect[3])


def similarity_transform(
    p: tuple[float, float],
    angle_deg: float,
    scale: float,
    src_center: tuple[float, float] = (0.0, 0.0),
    tgt_center: tuple[float, float] = (0.0, 0.0),
) -> tuple[float, float]:
    """Map a point from the source frame to the target frame by a similarity
    transform: ``p' = tgt_center + scale * R(angle) * (p - src_center)``.

    Combines translation (source -> target center), rotation and uniform scale
    in one step - the alignment used when propagating annotations between
    frames whose dish differs in position, orientation and camera distance.
    """
    ang = math.radians(angle_deg)
    cos, sin = math.cos(ang), math.sin(ang)
    dx, dy = p[0] - src_center[0], p[1] - src_center[1]
    rx = scale * (dx * cos - dy * sin)
    ry = scale * (dx * sin + dy * cos)
    return (tgt_center[0] + rx, tgt_center[1] + ry)


def rect_crop_box(x: float, y: float, w: float, h: float, rotation: float) -> tuple[int, int, int, int]:
    """Axis-aligned crop region covering a rectangle that is rotated around its
    anchor (``rotation`` degrees, as stored for rotated-view rectangles).

    Returns (left, top, right, bottom). Without rotation it is simply the
    rectangle itself.
    """
    if rotation:
        ang = math.radians(rotation)
        cos, sin = math.cos(ang), math.sin(ang)
        xs = [x + ox * cos - oy * sin for ox, oy in ((0, 0), (w, 0), (w, h), (0, h))]
        ys = [y + ox * sin + oy * cos for ox, oy in ((0, 0), (w, 0), (w, h), (0, h))]
        return (
            int(math.floor(min(xs))),
            int(math.floor(min(ys))),
            int(math.ceil(max(xs))),
            int(math.ceil(max(ys))),
        )
    return int(x), int(y), int(x + w), int(y + h)


def polygon_area(points: list[tuple[float, float]]) -> float:
    """Shoelace area of a polygon."""
    n = len(points)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def circularity(points: list[tuple[float, float]]) -> float:
    """Shape compactness: 4*pi*area / perimeter^2. 1.0 = perfect circle."""
    area = polygon_area(points)
    if area <= 0 or len(points) < 3:
        return 0.0
    perimeter = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        perimeter += math.hypot(x2 - x1, y2 - y1)
    if perimeter <= 0:
        return 0.0
    return 4.0 * math.pi * area / (perimeter * perimeter)
