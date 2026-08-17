"""Post-processing for the local MNN models (NMS, mask upscaling, contour handling)."""

from __future__ import annotations

import cv2
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -80, 80)))


def xywh2xyxy(boxes: np.ndarray) -> np.ndarray:
    x1 = boxes[..., 0] - boxes[..., 2] / 2
    y1 = boxes[..., 1] - boxes[..., 3] / 2
    x2 = boxes[..., 0] + boxes[..., 2] / 2
    y2 = boxes[..., 1] + boxes[..., 3] / 2
    return np.stack([x1, y1, x2, y2], axis=-1)


def nms(boxes_xyxy: np.ndarray, scores: np.ndarray, iou_thresh: float) -> np.ndarray:
    """Class-agnostic NMS. Returns keep indices (desc score)."""
    order = np.argsort(-scores)
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        rest = order[1:]
        xx1 = np.maximum(boxes_xyxy[i, 0], boxes_xyxy[rest, 0])
        yy1 = np.maximum(boxes_xyxy[i, 1], boxes_xyxy[rest, 1])
        xx2 = np.minimum(boxes_xyxy[i, 2], boxes_xyxy[rest, 2])
        yy2 = np.minimum(boxes_xyxy[i, 3], boxes_xyxy[rest, 3])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        area_i = (boxes_xyxy[i, 2] - boxes_xyxy[i, 0]) * (boxes_xyxy[i, 3] - boxes_xyxy[i, 1])
        area_r = (boxes_xyxy[rest, 2] - boxes_xyxy[rest, 0]) * (boxes_xyxy[rest, 3] - boxes_xyxy[rest, 1])
        iou = inter / (area_i + area_r - inter + 1e-9)
        order = rest[iou <= iou_thresh]
    return np.asarray(keep, dtype=np.int64)


def pcs_scores(pred_logits, presence_logit):
    scores = sigmoid(pred_logits)[..., 0]
    presence = sigmoid(presence_logit)
    return scores * presence


def pcs_filter_nms(pred_boxes_xywh, pred_masks, scores, conf=0.25, iou=0.7, agnostic_nms=False):
    """SAM3 PCS postprocess on normalized box outputs. Returns (masks, boxes_xyxy_norm, score, cls)."""
    n_masks = pred_masks.shape[-1]
    pred_masks = pred_masks.reshape(-1, pred_masks.shape[-2], n_masks)
    pred_boxes_xywh = pred_boxes_xywh.reshape(-1, 4)
    scores = scores.reshape(-1)
    nq = pred_boxes_xywh.shape[0]
    keep = scores > conf
    if not np.any(keep):
        return (
            np.zeros((0, *pred_masks.shape[1:]), np.float32),
            np.zeros((0, 4), np.float32),
            np.zeros((0,), np.float32),
            np.zeros((0,), np.int64),
        )
    masks = pred_masks[keep]
    boxes = pred_boxes_xywh[keep]
    sc = scores[keep]
    cls = np.nonzero(keep)[0] // nq
    boxes_xyxy = xywh2xyxy(boxes)
    off = 0.0 if agnostic_nms else 7680.0
    keep2 = nms(boxes_xyxy + cls[:, None] * off, sc, iou)
    return masks[keep2], boxes_xyxy[keep2], sc[keep2], cls[keep2]


def upscale_mask(mask_logits: np.ndarray, target_hw: tuple[int, int], mask_threshold: float = 0.0) -> np.ndarray:
    """Bilinear-upscale a (S,S) mask to (h,w) and threshold to binary."""
    m = mask_logits.astype(np.float32)
    if m.shape != target_hw:
        m = cv2.resize(m, (target_hw[1], target_hw[0]), interpolation=cv2.INTER_LINEAR)
    return (m > mask_threshold).astype(np.uint8)


def upscale_mask_pad(mask_logits: np.ndarray, target_hw: tuple[int, int], mask_threshold: float = 0.0) -> np.ndarray:
    """Upscale a mask from padded-letterbox space back to the original image (crop then resize)."""
    m = mask_logits.astype(np.float32)
    H, W = target_hw
    gain = min(m.shape[0] / H, m.shape[1] / W)
    pad_w = m.shape[1] - round(W * gain)
    pad_h = m.shape[0] - round(H * gain)
    crop = m[: m.shape[0] - pad_h, : m.shape[1] - pad_w]
    if crop.shape[0] > 0 and crop.shape[1] > 0:
        m = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LINEAR)
    else:
        m = np.zeros((H, W), np.float32)
    return (m > mask_threshold).astype(np.uint8)


def contour_filter(contours, min_area_ratio: float, img_shape: tuple[int, int]) -> list:
    """Drop contours smaller than min_area_ratio * image area."""
    img_area = img_shape[0] * img_shape[1]
    min_area = img_area * min_area_ratio
    return [c for c in contours if cv2.contourArea(c) >= min_area]


def reduce_contour_points(
    contour: np.ndarray,
    target_reduction: float = 0.7,
    min_points: int = 5,
    max_points: int = 100,
    max_iterations: int = 10,
) -> np.ndarray:
    """Approximate a contour to a target point count via binary search on epsilon."""
    low, high = 0.1, 10.0
    best = None
    target_points = min(max_points, max(min_points, int(len(contour) * (1 - target_reduction))))
    for _ in range(max_iterations):
        epsilon = (low + high) / 2
        simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
        if len(simplified) == target_points:
            best = simplified
            break
        if len(simplified) < target_points:
            high = epsilon
        else:
            low = epsilon
        if high - low < 0.1:
            best = simplified
            break
    if best is None:
        best = cv2.approxPolyDP(contour, 1.0, closed=True)
    return best.reshape(-1, 2)


def smooth_contour(contour: np.ndarray, window: int = 5) -> np.ndarray:
    """Moving-average smooth of a closed contour to reduce pixel-stair-step jaggies.

    ``window`` is the averaging window size (odd). Returns the same layout as the
    input contour (N,1,2) int32.
    """
    pts = contour.reshape(-1, 2).astype(np.float32)
    n = len(pts)
    if n < window:
        return contour
    half = window // 2
    out = np.empty_like(pts)
    for i in range(n):
        idxs = [(i + j) % n for j in range(-half, half + 1)]
        out[i] = np.mean(pts[idxs], axis=0)
    return out.reshape(-1, 1, 2).astype(np.int32)


def nms_filter(boxes: list[tuple[float, float, float, float]], iou_threshold: float = 0.5) -> list[int]:
    """NMS over xywh boxes; returns kept indices."""
    if not boxes:
        return []
    boxes_xyxy = np.asarray([[x, y, x + w, y + h] for x, y, w, h in boxes], np.float32)
    areas = boxes_xyxy[:, 2] * boxes_xyxy[:, 3]
    order = np.argsort(-areas)
    keep: list[int] = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        rest = order[1:]
        xx1 = np.maximum(boxes_xyxy[i, 0], boxes_xyxy[rest, 0])
        yy1 = np.maximum(boxes_xyxy[i, 1], boxes_xyxy[rest, 1])
        xx2 = np.minimum(boxes_xyxy[i, 2], boxes_xyxy[rest, 2])
        yy2 = np.minimum(boxes_xyxy[i, 3], boxes_xyxy[rest, 3])
        inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
        union = areas[i] + areas[rest] - inter
        iou = inter / np.maximum(union, 1e-9)
        order = rest[iou <= iou_threshold]
    return keep
