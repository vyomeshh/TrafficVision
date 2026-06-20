# core/rules/triple_riding.py
"""Triple Riding Detection Module for TrafficVision AI.

Detects instances where three or more persons are riding on a single
motorcycle — a common traffic violation in dense urban areas.
"""

from typing import Any, Dict, List, Tuple


def _expand_bbox(
    bbox: List[int],
    scale: float = 1.5,
) -> Tuple[int, int, int, int]:
    """Expand a bounding box by *scale* around its centre.

    Args:
        bbox: ``[x1, y1, x2, y2]`` pixel coordinates.
        scale: Expansion factor (1.5 = 50 % expansion on each side).

    Returns:
        A 4-tuple ``(ex1, ey1, ex2, ey2)`` of the expanded box.
    """
    x1, y1, x2, y2 = bbox
    cx: float = (x1 + x2) / 2.0
    cy: float = (y1 + y2) / 2.0
    half_w: float = (x2 - x1) / 2.0 * scale
    half_h: float = (y2 - y1) / 2.0 * scale

    return int(cx - half_w), int(cy - half_h), int(cx + half_w), int(cy + half_h)


def _bboxes_intersect(b1: List[int], b2: List[int]) -> bool:
    """Return True if bounding boxes b1 and b2 overlap."""
    return not (b1[0] > b2[2] or b2[0] > b1[2] or b1[1] > b2[3] or b2[1] > b1[3])


def check_triple_riding(
    detections: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Detect triple-riding violations on motorcycles.

    For every ``Motorcycle`` detection, the function counts the number of
    ``Person`` detections whose centre point falls inside the motorcycle
    bounding box expanded by 50 %.  If the count is **≥ 3**, the
    motorcycle is flagged as a triple-riding violation.

    Args:
        detections: List of detection dicts from
            :meth:`~core.vision.detector.VehicleDetector.detect`.

    Returns:
        A tuple ``(violations, logs)`` where:
            - ``violations`` is a list of violation dicts, each containing:
                - ``type`` (``str``): ``'Triple Riding'``
                - ``vehicle_type`` (``str``): ``'Motorcycle'``
                - ``bbox`` (``List[int]``): Motorcycle bounding box.
                - ``confidence`` (``float``): Average confidence of the
                  matched person detections.
                - ``rider_count`` (``int``): Number of riders detected.
            - ``logs`` is a list of terminal-style log strings.
    """
    logs: List[str] = []
    violations: List[Dict[str, Any]] = []

    # Partition detections by class
    motorcycles: List[Dict[str, Any]] = [
        d for d in detections if d["class_name"] == "Motorcycle"
    ]
    persons: List[Dict[str, Any]] = [
        d for d in detections if d["class_name"] == "Person"
    ]

    logs.append(
        f"[TRIPLE RIDING] Found {len(motorcycles)} motorcycle(s) and "
        f"{len(persons)} person(s) in frame."
    )

    if not motorcycles:
        logs.append("[TRIPLE RIDING] No motorcycles detected — skipping. Done.")
        return violations, logs

    for moto in motorcycles:
        moto_bbox: List[int] = moto["bbox"]
        expanded: Tuple[int, int, int, int] = _expand_bbox(moto_bbox, scale=1.5)

        matched_persons: List[Dict[str, Any]] = []

        for person in persons:
            person_bbox: List[int] = person["bbox"]
            if _bboxes_intersect(person_bbox, expanded):
                matched_persons.append(person)

        rider_count: int = len(matched_persons)

        logs.append(
            f"[TRIPLE RIDING] Motorcycle at {moto_bbox} — "
            f"{rider_count} rider(s) associated."
        )

        if rider_count >= 3:
            # Average the confidence scores of all matched persons
            avg_confidence: float = sum(
                p["confidence"] for p in matched_persons
            ) / rider_count

            violations.append(
                {
                    "type": "Triple Riding",
                    "vehicle_type": "Motorcycle",
                    "bbox": moto_bbox,
                    "confidence": round(avg_confidence, 4),
                    "rider_count": rider_count,
                }
            )

            logs.append(
                f"[TRIPLE RIDING] ⚠ VIOLATION — {rider_count} riders on "
                f"motorcycle at {moto_bbox} (avg conf={avg_confidence:.2f})."
            )

    logs.append(
        f"[TRIPLE RIDING] ✔ Check complete — "
        f"{len(violations)} violation(s) flagged. Done."
    )

    return violations, logs
