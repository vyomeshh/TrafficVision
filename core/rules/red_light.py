# core/rules/red_light.py
"""Red Light / Stop Line Violation Detection Module for TrafficVision AI.

Detects vehicles that cross a configurable virtual stop line, simulating
a red-light violation scenario in traffic surveillance footage.
"""

from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


def draw_stop_line(
    image: np.ndarray,
    stop_line_y: int,
    color: Tuple[int, int, int] = (0, 0, 255),
    dash_length: int = 20,
    gap_length: int = 15,
    thickness: int = 3,
) -> np.ndarray:
    """Draw a dashed horizontal stop line on a copy of the image.

    Args:
        image: BGR image to annotate (will *not* be modified in-place).
        stop_line_y: Y-coordinate of the stop line in pixels.
        color: BGR colour tuple for the line.  Defaults to red.
        dash_length: Length of each dash segment in pixels.
        gap_length: Length of the gap between dashes in pixels.
        thickness: Line thickness in pixels.

    Returns:
        A copy of the image with the dashed stop line drawn.
    """
    annotated: np.ndarray = image.copy()
    img_w: int = annotated.shape[1]

    x: int = 0
    while x < img_w:
        x_end: int = min(x + dash_length, img_w)
        cv2.line(
            annotated,
            (x, stop_line_y),
            (x_end, stop_line_y),
            color,
            thickness,
            cv2.LINE_AA,
        )
        x += dash_length + gap_length

    # Label
    label: str = "STOP LINE"
    (text_w, text_h), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
    )
    label_x: int = img_w - text_w - 12
    label_y: int = stop_line_y - 10

    cv2.putText(
        annotated,
        label,
        (label_x, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
        cv2.LINE_AA,
    )

    return annotated


def check_red_light_violation(
    detections: List[Dict[str, Any]],
    image_shape: Tuple[int, ...],
    stop_line_y_ratio: float = 0.7,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Detect vehicles that have crossed the virtual stop line.

    A vehicle is flagged when the **bottom edge** of its bounding box
    (``y2``) extends below (i.e. has a larger y-value than) the stop line.

    Note:
        ``Person`` detections (class_id = 0) are excluded since only
        motorised vehicles should be checked for red-light violations.

    Args:
        detections: List of detection dicts from
            :meth:`~core.vision.detector.VehicleDetector.detect`.
        image_shape: Shape tuple of the source image, typically
            ``(height, width, channels)``.
        stop_line_y_ratio: Fraction of image height at which the virtual
            stop line is placed.  Defaults to ``0.7`` (70 % from the top).

    Returns:
        A tuple ``(violations, logs)`` where:
            - ``violations`` is a list of violation dicts, each containing:
                - ``type`` (``str``): ``'Red Light Violation'``
                - ``vehicle_type`` (``str``): Class name of the vehicle.
                - ``bbox`` (``List[int]``): Vehicle bounding box.
                - ``confidence`` (``float``): Detection confidence.
                - ``stop_line_y`` (``int``): Y-pixel position of the stop
                  line used for this check.
            - ``logs`` is a list of terminal-style log strings.
    """
    logs: List[str] = []
    violations: List[Dict[str, Any]] = []

    img_height: int = int(image_shape[0])
    stop_line_y: int = int(img_height * stop_line_y_ratio)

    logs.append(
        f"[RED LIGHT] Stop line set at y={stop_line_y} "
        f"({stop_line_y_ratio:.0%} of {img_height}px height)."
    )

    # Only check motorised vehicles (exclude Person class_id=0)
    vehicle_detections: List[Dict[str, Any]] = [
        d for d in detections if d["class_id"] != 0
    ]

    logs.append(
        f"[RED LIGHT] Evaluating {len(vehicle_detections)} vehicle detection(s)..."
    )

    for det in vehicle_detections:
        bbox: List[int] = det["bbox"]
        y2: int = bbox[3]  # Bottom edge of bounding box

        if y2 > stop_line_y:
            violations.append(
                {
                    "type": "Red Light Violation",
                    "vehicle_type": det["class_name"],
                    "bbox": bbox,
                    "confidence": det["confidence"],
                    "stop_line_y": stop_line_y,
                }
            )

            logs.append(
                f"[RED LIGHT] ⚠ {det['class_name']} at {bbox} crossed stop line "
                f"(y2={y2} > {stop_line_y}, conf={det['confidence']:.2f})."
            )
        else:
            logs.append(
                f"[RED LIGHT] {det['class_name']} at {bbox} — "
                f"above stop line (y2={y2} ≤ {stop_line_y})."
            )

    logs.append(
        f"[RED LIGHT] ✔ Check complete — "
        f"{len(violations)} violation(s) flagged. Done."
    )

    return violations, logs
