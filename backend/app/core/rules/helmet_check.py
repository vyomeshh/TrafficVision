# core/rules/helmet_check.py
"""Helmet Violation Detection Module for TrafficVision AI.

Detects motorcycle riders who are potentially not wearing helmets by
associating Person detections with nearby Motorcycle detections and
analysing the head region of each rider.
"""

from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


def _expand_bbox(
    bbox: List[int],
    scale: float = 1.5,
    img_w: int = 0,
    img_h: int = 0,
) -> Tuple[int, int, int, int]:
    """Expand a bounding box by *scale* around its centre, clamped to image bounds.

    Args:
        bbox: ``[x1, y1, x2, y2]`` pixel coordinates.
        scale: Expansion factor (1.5 = 50 % expansion on each side).
        img_w: Image width for clamping (0 = no clamping).
        img_h: Image height for clamping (0 = no clamping).

    Returns:
        A 4-tuple ``(ex1, ey1, ex2, ey2)`` of the expanded box.
    """
    x1, y1, x2, y2 = bbox
    cx: float = (x1 + x2) / 2.0
    cy: float = (y1 + y2) / 2.0
    half_w: float = (x2 - x1) / 2.0 * scale
    half_h: float = (y2 - y1) / 2.0 * scale

    ex1 = int(max(cx - half_w, 0))
    ey1 = int(max(cy - half_h, 0))
    ex2 = int(min(cx + half_w, img_w) if img_w else cx + half_w)
    ey2 = int(min(cy + half_h, img_h) if img_h else cy + half_h)

    return ex1, ey1, ex2, ey2


def _compute_iou(box_a: List[int], box_b: List[int]) -> float:
    """Compute Intersection-over-Union between two axis-aligned boxes.

    Args:
        box_a: ``[x1, y1, x2, y2]``.
        box_b: ``[x1, y1, x2, y2]``.

    Returns:
        IoU value in ``[0, 1]``.
    """
    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])

    inter_area: float = max(0, xb - xa) * max(0, yb - ya)
    if inter_area == 0:
        return 0.0

    area_a: float = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b: float = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])

    return inter_area / (area_a + area_b - inter_area)


def _point_in_box(px: float, py: float, bbox: Tuple[int, int, int, int]) -> bool:
    """Return ``True`` if point ``(px, py)`` is inside the bbox."""
    return bbox[0] <= px <= bbox[2] and bbox[1] <= py <= bbox[3]


def _analyse_head_region(
    image: np.ndarray,
    person_bbox: List[int],
) -> float:
    """Analyse the head region of a rider to estimate helmet presence.

    Currently uses a **placeholder heuristic** — since no dedicated helmet
    classifier is loaded, every rider is flagged as a *potential* violation
    with a fixed confidence score.

    The heuristic examines the upper 40 % of the person bounding box and
    computes a simple colour-variance metric.  Low variance in the head
    region is loosely correlated with a bare head, while high variance
    *may* indicate a helmet.  This is intentionally conservative (flags
    more violations) until a proper helmet classification model is
    integrated.

    Args:
        image: Full BGR image.
        person_bbox: ``[x1, y1, x2, y2]`` of the person detection.

    Returns:
        A confidence score ∈ (0, 1] indicating how likely it is that the
        rider is **not** wearing a helmet.  Higher = more likely violation.
    """
    x1, y1, x2, y2 = person_bbox
    head_y2: int = y1 + int((y2 - y1) * 0.4)

    # Clamp to image dimensions
    h, w = image.shape[:2]
    cx1 = max(0, x1)
    cy1 = max(0, y1)
    cx2 = min(w, x2)
    cy2 = min(h, head_y2)

    if cx2 <= cx1 or cy2 <= cy1:
        return 0.85  # Cannot crop — flag conservatively.

    head_crop: np.ndarray = image[cy1:cy2, cx1:cx2]

    # Colour-variance heuristic
    if head_crop.size == 0:
        return 0.85

    hsv_crop: np.ndarray = cv2.cvtColor(head_crop, cv2.COLOR_BGR2HSV)
    _, saturation, _ = cv2.split(hsv_crop)
    mean_sat: float = float(np.mean(saturation))

    # Helmets tend to be brightly / uniformly coloured → higher saturation.
    # Bare heads tend towards low saturation (hair / skin).
    # This is a rough placeholder; a real model would replace this.
    if mean_sat > 80:
        # Possibly wearing a helmet — lower violation confidence.
        return 0.45
    else:
        # Likely no helmet — higher violation confidence.
        return 0.85


def check_helmet_violation(
    detections: List[Dict[str, Any]],
    image: np.ndarray,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Detect potential no-helmet violations among motorcycle riders.

    For every ``Motorcycle`` detection, the function searches for nearby
    ``Person`` detections (via IoU > 0.1 **or** person centre inside the
    expanded motorcycle bbox).  Each matched person's head region is then
    analysed to estimate helmet presence.

    Args:
        detections: List of detection dicts from
            :meth:`~core.vision.detector.VehicleDetector.detect`.
        image: The BGR image corresponding to the detections (used for
            head-region cropping).

    Returns:
        A tuple ``(violations, logs)`` where:
            - ``violations`` is a list of violation dicts, each containing:
                - ``type`` (``str``): ``'No Helmet'``
                - ``vehicle_type`` (``str``): ``'Motorcycle'``
                - ``bbox`` (``List[int]``): Motorcycle bounding box.
                - ``confidence`` (``float``): Violation confidence.
                - ``rider_bbox`` (``List[int]``): Rider bounding box.
            - ``logs`` is a list of terminal-style log strings.
    """
    logs: List[str] = []
    violations: List[Dict[str, Any]] = []

    img_h, img_w = image.shape[:2]

    # Partition detections by class
    motorcycles: List[Dict[str, Any]] = [
        d for d in detections if d["class_name"] == "Motorcycle"
    ]
    persons: List[Dict[str, Any]] = [
        d for d in detections if d["class_name"] == "Person"
    ]

    logs.append(
        f"[HELMET CHECK] Found {len(motorcycles)} motorcycle(s) and "
        f"{len(persons)} person(s) in frame."
    )

    if not motorcycles:
        logs.append("[HELMET CHECK] No motorcycles detected — skipping. Done.")
        return violations, logs

    for moto in motorcycles:
        moto_bbox: List[int] = moto["bbox"]
        expanded: Tuple[int, int, int, int] = _expand_bbox(
            moto_bbox, scale=1.5, img_w=img_w, img_h=img_h
        )

        riders_found: int = 0

        for person in persons:
            person_bbox: List[int] = person["bbox"]

            # Check association: IoU > 0.1 OR person centre inside expanded moto bbox
            iou: float = _compute_iou(moto_bbox, person_bbox)
            pcx: float = (person_bbox[0] + person_bbox[2]) / 2.0
            pcy: float = (person_bbox[1] + person_bbox[3]) / 2.0
            inside: bool = _point_in_box(pcx, pcy, expanded)

            if iou < 0.1 and not inside:
                continue

            riders_found += 1

            # Analyse head region for helmet presence
            violation_confidence: float = _analyse_head_region(image, person_bbox)

            if violation_confidence >= 0.5:
                violations.append(
                    {
                        "type": "No Helmet",
                        "vehicle_type": "Motorcycle",
                        "bbox": moto_bbox,
                        "confidence": round(violation_confidence, 4),
                        "rider_bbox": person_bbox,
                    }
                )

                logs.append(
                    f"[HELMET CHECK] ⚠ Rider at {person_bbox} on motorcycle at "
                    f"{moto_bbox} — no helmet (conf={violation_confidence:.2f})."
                )
            else:
                logs.append(
                    f"[HELMET CHECK] ✔ Rider at {person_bbox} appears to have a helmet "
                    f"(conf={1 - violation_confidence:.2f})."
                )

        if riders_found == 0:
            logs.append(
                f"[HELMET CHECK] Motorcycle at {moto_bbox} — no associated rider found."
            )

    logs.append(
        f"[HELMET CHECK] ✔ Check complete — {len(violations)} violation(s) flagged. Done."
    )

    return violations, logs
