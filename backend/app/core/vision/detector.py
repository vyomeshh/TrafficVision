# core/vision/detector.py
"""YOLOv8 Vehicle Detection Engine for TrafficVision AI.

Provides the ``VehicleDetector`` class that wraps the Ultralytics YOLOv8
model to detect vehicles and persons in traffic surveillance imagery,
with utilities for annotation and bounding-box rendering.
"""

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO


# ── Class-ID ↔ friendly-name mapping ────────────────────────────────
VEHICLE_CLASS_MAP: Dict[int, str] = {
    0: "Person",
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
}

#: Set of class IDs the detector will keep from raw YOLO output.
TARGET_CLASS_IDS: set = set(VEHICLE_CLASS_MAP.keys())

# ── Colour palette for annotation ───────────────────────────────────
COLOR_NORMAL: Tuple[int, int, int] = (0, 200, 0)       # Green  (BGR)
COLOR_VIOLATION: Tuple[int, int, int] = (0, 0, 220)    # Red    (BGR)
COLOR_LABEL_BG: Tuple[int, int, int] = (30, 30, 30)    # Dark grey
COLOR_LABEL_FG: Tuple[int, int, int] = (255, 255, 255) # White


class VehicleDetector:
    """Detects vehicles and persons using a YOLOv8s model.

    Attributes:
        model: The loaded Ultralytics YOLO model instance.
        logs: Cumulative list of terminal-style processing logs.
        confidence_threshold: Minimum confidence for a detection to be kept.
    """

    def __init__(
        self,
        model_path: str = "yolov8s.pt",
        confidence_threshold: float = 0.35,
    ) -> None:
        """Initialise the detector and load the YOLOv8 model weights.

        Args:
            model_path: Path or name of the YOLOv8 weights file.  Defaults
                to ``'yolov8s.pt'`` which Ultralytics will auto-download if
                not already cached.
            confidence_threshold: Minimum detection confidence in ``[0, 1]``.
        """
        self.logs: List[str] = []
        self.confidence_threshold: float = confidence_threshold

        self.logs.append(f"[DETECTOR] Loading YOLOv8 model from '{model_path}'...")
        self.model: YOLO = YOLO(model_path)
        self.logs.append(f"[DETECTOR] Loading YOLOv8 model from '{model_path}'... Done.")

    # ── Detection ────────────────────────────────────────────────────
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Run inference on a BGR image and return filtered detections.

        Only detections whose class ID is in ``TARGET_CLASS_IDS`` (Person,
        Car, Motorcycle, Bus, Truck) and whose confidence meets the
        threshold are returned.

        Args:
            image: A BGR ``np.ndarray`` (H × W × 3).

        Returns:
            A list of detection dictionaries, each containing:
                - ``class_name`` (``str``): Human-readable class label.
                - ``class_id`` (``int``): COCO class ID.
                - ``confidence`` (``float``): Model confidence ∈ [0, 1].
                - ``bbox`` (``List[int]``): ``[x1, y1, x2, y2]`` pixel coords.
        """
        self.logs.append("[DETECTOR] Running YOLOv8 inference...")

        results = self.model(image, verbose=False)

        detections: List[Dict[str, Any]] = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                class_id: int = int(box.cls[0].item())
                confidence: float = float(box.conf[0].item())

                if class_id not in TARGET_CLASS_IDS:
                    continue
                if confidence < self.confidence_threshold:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    {
                        "class_name": VEHICLE_CLASS_MAP[class_id],
                        "class_id": class_id,
                        "confidence": round(confidence, 4),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    }
                )

        self.logs.append(
            f"[DETECTOR] Inference complete — {len(detections)} target object(s) detected. Done."
        )

        # Per-class summary
        class_counts: Dict[str, int] = {}
        for det in detections:
            name = det["class_name"]
            class_counts[name] = class_counts.get(name, 0) + 1
        for cls_name, count in sorted(class_counts.items()):
            self.logs.append(f"[DETECTOR]   ├─ {cls_name}: {count}")

        return detections

    # ── Annotation ───────────────────────────────────────────────────
    def annotate(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        violations: Optional[List[Dict[str, Any]]] = None,
    ) -> np.ndarray:
        """Draw bounding boxes and labels on a copy of the image.

        Normal detections are drawn in **green**; any detection whose
        bounding box matches a violation entry is drawn in **red**.

        Args:
            image: Original BGR image (will *not* be modified in-place).
            detections: List of detection dicts from :meth:`detect`.
            violations: Optional list of violation dicts.  Each must have a
                ``'bbox'`` key so the annotator can match them to detections.

        Returns:
            An annotated copy of the input image.
        """
        self.logs.append("[DETECTOR] Annotating detections on image...")

        annotated: np.ndarray = image.copy()

        # Build a set of violation bboxes for O(1) lookup.
        violation_bboxes: set = set()
        if violations:
            for v in violations:
                bbox = v.get("bbox")
                if bbox is not None:
                    violation_bboxes.add(tuple(bbox))

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            class_name: str = det["class_name"]
            confidence: float = det["confidence"]

            is_violation: bool = tuple(det["bbox"]) in violation_bboxes
            color: Tuple[int, int, int] = COLOR_VIOLATION if is_violation else COLOR_NORMAL
            thickness: int = 3 if is_violation else 2

            # Bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            # Label background + text
            label: str = f"{class_name} {confidence:.0%}"
            if is_violation:
                label = f"[VIOLATION] {label}"

            (text_w, text_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
            )
            label_y1: int = max(y1 - text_h - baseline - 6, 0)
            label_y2: int = y1

            cv2.rectangle(
                annotated,
                (x1, label_y1),
                (x1 + text_w + 8, label_y2),
                COLOR_LABEL_BG,
                cv2.FILLED,
            )
            cv2.putText(
                annotated,
                label,
                (x1 + 4, label_y2 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                1,
                cv2.LINE_AA,
            )

        self.logs.append(
            f"[DETECTOR] Annotating detections on image... "
            f"{len(detections)} boxes drawn ({len(violation_bboxes)} violations). Done."
        )

        return annotated

# Global detector instance for easy import
_detector_instance = VehicleDetector()

def detect_vehicles(img, **kwargs):
    if 'confidence' in kwargs:
        _detector_instance.confidence_threshold = kwargs['confidence']
    return _detector_instance.detect(img), img

def annotate_image(img, detections, violations=None, plates=None, **kwargs):
    return _detector_instance.annotate(img, detections, violations, **kwargs)
