from typing import List, Tuple, Dict, Any
import cv2
import numpy as np

def check_seatbelt_compliance(detections: List[Dict[str, Any]], image: np.ndarray) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Check for seatbelt non-compliance.
    Uses a heuristic: If a 'Person' is detected intersecting a 'Car' or 'Truck', 
    we analyze the upper torso region for strong diagonal edges (seatbelts).
    """
    violations = []
    logs = ["[SEATBELT] Starting seatbelt compliance check..."]

    # 1. Separate persons and vehicles
    persons = [d for d in detections if d.get("class_name") == "Person"]
    vehicles = [d for d in detections if d.get("class_name") in ["Car", "Truck"]]

    if not persons or not vehicles:
        logs.append("[SEATBELT] No persons or vehicles found for seatbelt check.")
        return violations, logs

    # Helper for intersection
    def bboxes_intersect(b1, b2):
        return not (b1[0] > b2[2] or b2[0] > b1[2] or b1[1] > b2[3] or b2[1] > b1[3])

    # 2. Check each person
    for person in persons:
        p_bbox = person["bbox"]
        
        # Check if person is inside/intersecting a vehicle
        in_vehicle = False
        for v in vehicles:
            if bboxes_intersect(p_bbox, v["bbox"]):
                in_vehicle = True
                break
                
        if not in_vehicle:
            continue

        # Extract upper torso (top 60% of person)
        x1, y1, x2, y2 = p_bbox
        torso_y2 = y1 + int((y2 - y1) * 0.6)
        
        # Boundary checks
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        torso_y2 = min(image.shape[0], torso_y2)

        if x2 <= x1 or torso_y2 <= y1:
            continue

        torso_roi = image[y1:torso_y2, x1:x2]
        
        # Convert to grayscale and run Canny
        gray = cv2.cvtColor(torso_roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough Lines to find diagonal lines
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=30, minLineLength=20, maxLineGap=5)
        
        has_seatbelt = False
        if lines is not None:
            for line in lines:
                x_1, y_1, x_2, y_2 = line[0]
                if x_2 - x_1 == 0:
                    continue
                angle = np.abs(np.arctan((y_2 - y_1) / (x_2 - x_1)) * 180 / np.pi)
                # Diagonal line roughly between 30 and 60 degrees
                if 30 <= angle <= 60:
                    has_seatbelt = True
                    break

        if not has_seatbelt:
            violations.append({
                "type": "Seatbelt Non-Compliance",
                "vehicle_type": "Car/Truck",
                "bbox": p_bbox,  # Mark the person
                "confidence": round(person.get("confidence", 0.5), 4)
            })
            logs.append(f"[SEATBELT] No seatbelt detected for person at {p_bbox}.")

    logs.append(f"[SEATBELT] Seatbelt check complete. Found {len(violations)} violation(s).")
    return violations, logs
