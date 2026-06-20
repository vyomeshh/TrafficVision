from typing import List, Dict, Any, Tuple

def check_wrong_side_driving(detections: List[Dict[str, Any]], image_width: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Check for wrong-side driving.
    Uses a simple spatial heuristic: assuming left-hand traffic, 
    the right side of the image (x > 70% of width) is defined as a wrong-side zone
    for vehicles moving away or incorrectly positioned.
    """
    violations = []
    logs = ["[WRONG-SIDE] Starting wrong-side driving check..."]

    # Define wrong-side threshold (e.g. rightmost 30% of the frame)
    wrong_side_threshold = int(image_width * 0.7)

    for det in detections:
        c_name = det.get("class_name")
        if c_name in ["Person", "Unknown"]:
            continue  # Only check vehicles
            
        x1, y1, x2, y2 = det["bbox"]
        x_center = (x1 + x2) / 2.0

        if x_center > wrong_side_threshold:
            violations.append({
                "type": "Wrong-Side Driving",
                "vehicle_type": c_name,
                "bbox": det["bbox"],
                "confidence": round(det.get("confidence", 0.5), 4)
            })
            logs.append(f"[WRONG-SIDE] Vehicle {c_name} detected in wrong-side zone (x={x_center:.1f} > {wrong_side_threshold}).")

    logs.append(f"[WRONG-SIDE] Check complete. Found {len(violations)} violation(s).")
    return violations, logs
