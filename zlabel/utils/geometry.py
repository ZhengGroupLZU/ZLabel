"""Geometry helpers for seed-germination annotations (dish ellipse fitting)."""

from __future__ import annotations

import math

import numpy as np


def fit_ellipse_polygon(points: list[tuple[float, float]], n: int = 36) -> list[tuple[float, float]] | None:
    """Fit an ellipse to contour points (OpenCV fitEllipse) and sample ``n`` points.

    Returns None when cv2 is unavailable or fewer than 5 points are given.
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
    t = np.linspace(0, 2.0 * np.pi, n, endpoint=False)
    a, b = ma_ax / 2.0, mi_ax / 2.0
    ang = np.deg2rad(angle)
    cos, sin = np.cos(t), np.sin(t)
    x = cx + a * cos * np.cos(ang) - b * sin * np.sin(ang)
    y = cy + a * cos * np.sin(ang) + b * sin * np.cos(ang)
    return [(float(xi), float(yi)) for xi, yi in zip(x, y)]


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
