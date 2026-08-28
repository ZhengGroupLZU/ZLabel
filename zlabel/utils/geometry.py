"""Geometry helpers for seed-germination annotations (dish ellipse fitting)."""

from __future__ import annotations

import math

import numpy as np


def fit_ellipse_polygon(points: np.ndarray, n: int = 36) -> list[tuple[float, float]] | None:
    """Fit an ellipse to contour points (OpenCV fitEllipse) and sample ``n`` points.

    ``points`` is an (N, 2) float array. Returns None when cv2 is unavailable
    or fewer than 5 points are given.
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
    points: np.ndarray,
) -> tuple[float, float, float, tuple[float, float]] | None:
    """Fit an ellipse to contour points, returning ``(cx, cy, angle_deg, (ma_ax, mi_ax))``.

    ``points`` is an (N, 2) float array. Returns None when cv2 is unavailable
    or fewer than 5 points are given. Useful to estimate the rotation of a dish
    between two frames for alignment.
    """
    try:
        import cv2
    except ImportError:
        return None
    if points is None or len(points) < 5:
        return None
    pts = np.asarray(points, np.float32).reshape(-1, 1, 2)
    try:
        (cx, cy), (ma_ax, mi_ax), angle = cv2.fitEllipse(pts)
    except cv2.error:
        return None
    return float(cx), float(cy), float(angle), (float(ma_ax), float(mi_ax))


def rotate_point(
    points: np.ndarray,
    angle_deg: float,
    center: tuple[float, float] = (0.0, 0.0),
) -> np.ndarray:
    """Rotate every point in an (N, 2) array around ``center`` by ``angle_deg``."""
    ang = math.radians(angle_deg)
    cos, sin = math.cos(ang), math.sin(ang)
    dx = points[:, 0] - center[0]
    dy = points[:, 1] - center[1]
    return np.column_stack(
        (center[0] + dx * cos - dy * sin, center[1] + dx * sin + dy * cos)
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
    x, y = rotate_point(np.asarray([(rect[0], rect[1])], dtype=float), angle_deg, center)[0]
    return float(x), float(y), rect[2], rect[3]


def similarity_transform(
    points: np.ndarray,
    angle_deg: float,
    scale: float,
    src_center: tuple[float, float] = (0.0, 0.0),
    tgt_center: tuple[float, float] = (0.0, 0.0),
) -> np.ndarray:
    """Map points from the source frame to the target frame by a similarity
    transform: ``p' = tgt_center + scale * R(angle) * (p - src_center)``.

    ``points`` is an (N, 2) float array; returns an (N, 2) float array.
    """
    ang = math.radians(angle_deg)
    cos, sin = math.cos(ang), math.sin(ang)
    dx = points[:, 0] - src_center[0]
    dy = points[:, 1] - src_center[1]
    rx = scale * (dx * cos - dy * sin)
    ry = scale * (dx * sin + dy * cos)
    return np.column_stack((tgt_center[0] + rx, tgt_center[1] + ry))


def rect_crop_box(x: float, y: float, w: float, h: float, rotation: float) -> tuple[int, int, int, int]:
    """Axis-aligned crop region covering a rectangle that is rotated around its
    anchor (``rotation`` degrees, as stored for rotated-view rectangles).

    Returns (left, top, right, bottom). Without rotation it is simply the
    rectangle itself.
    """
    if rotation:
        ang = math.radians(rotation)
        cos, sin = math.cos(ang), math.sin(ang)
        corners = np.asarray([(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)])
        xs = x + corners[:, 0] * cos - corners[:, 1] * sin
        ys = y + corners[:, 0] * sin + corners[:, 1] * cos
        return (
            int(math.floor(float(xs.min()))),
            int(math.floor(float(ys.min()))),
            int(math.ceil(float(xs.max()))),
            int(math.ceil(float(ys.max()))),
        )
    return int(x), int(y), int(x + w), int(y + h)


def polygon_area(points: np.ndarray) -> float:
    """Shoelace area of an (N, 2) polygon array."""
    if points is None or len(points) < 3:
        return 0.0
    x = points[:, 0]
    y = points[:, 1]
    s = float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    return abs(s) / 2.0


def circularity(points: np.ndarray) -> float:
    """Shape compactness: 4*pi*area / perimeter^2. 1.0 = perfect circle."""
    area = polygon_area(points)
    if area <= 0 or points is None or len(points) < 3:
        return 0.0
    x = points[:, 0]
    y = points[:, 1]
    perimeter = float(np.sum(np.hypot(np.diff(x, append=x[0]), np.diff(y, append=y[0]))))
    if perimeter <= 0:
        return 0.0
    return 4.0 * math.pi * area / (perimeter * perimeter)
