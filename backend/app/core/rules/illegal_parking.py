from typing import List, Dict, Any, Tuple

def check_illegal_parking(detections: List[Dict[str, Any]], image_shape: Tuple[int, int]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Check for illegal parking.
    Uses a predefined spatial 'No Parking' polygon/zone. 
    If a vehicle intersects this zone, it is flagged.
    """
    violations = []
    logs = ["[PARKING] Starting illegal parking check..."]

    height, width = image_shape[:2]
    # Define a default No Parking Zone: top-left 25% of the frame
    npz_x1, npz_y1 = 0, 0
    npz_x2, npz_y2 = int(width * 0.25), int(height * 0.25)

    def bboxes_intersect(b1, b2):
        return not (b1[0] > b2[2] or b2[0] > b1[2] or b1[1] > b2[3] or b2[1] > b1[3])

    no_parking_bbox = [npz_x1, npz_y1, npz_x2, npz_y2]

    for det in detections:
        c_name = det.get("class_name")
        if c_name in ["Person", "Unknown"]:
            continue  # Only check vehicles
            
        v_bbox = det["bbox"]

        if bboxes_intersect(v_bbox, no_parking_bbox):
            violations.append({
                "type": "Illegal Parking",
                "vehicle_type": c_name,
                "bbox": v_bbox,
                "confidence": round(det.get("confidence", 0.5), 4)
            })
            logs.append(f"[PARKING] Vehicle {c_name} detected in No Parking Zone {no_parking_bbox}.")

    logs.append(f"[PARKING] Check complete. Found {len(violations)} violation(s).")
    return violations, logs
