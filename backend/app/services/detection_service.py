import base64
import cv2
import time
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException

from app.services.log_service import log_service
from app.services.fallback_service import (
    preprocess_image,
    detect_vehicles,
    annotate_image,
    check_helmet_violation,
    check_triple_riding,
    check_red_light_violation,
    PlateReader,
    store_violation
)

import os
from dotenv import load_dotenv
load_dotenv()

YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8s.pt")
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.25"))
STOP_LINE_RATIO = float(os.getenv("STOP_LINE_RATIO", "0.7"))

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR.parent / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def _encode_image_b64(img) -> str | None:
    """Helper to convert OpenCV BGR image to base64 JPEG string."""
    if img is None:
        return None
    success, buffer = cv2.imencode(".jpg", img)
    if not success:
        return None
    return base64.b64encode(buffer).decode("utf-8")

async def process_detection(detection_id: str, contents: bytes, filename: str) -> dict:
    start_time = time.perf_counter()
    log_service.init_detection(detection_id)
    log_service.add_log(detection_id, f"Processing started for {detection_id}")
    
    file_ext = Path(filename).suffix or ".jpg"
    upload_filename = f"{detection_id}{file_ext}"
    upload_path = UPLOADS_DIR / upload_filename

    with open(upload_path, "wb") as f:
        f.write(contents)
    log_service.add_log(detection_id, f"Saved upload -> {upload_filename}")

    # 2. Pre-process
    log_service.add_log(detection_id, "Pre-processing image...")
    try:
        original_img, processed_img, prep_logs = preprocess_image(str(upload_path))
        log_service.add_raw_logs(detection_id, prep_logs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode or process image: {exc}")

    # 3. YOLOv8 Vehicle Detection
    log_service.add_log(detection_id, "Running YOLOv8 vehicle detection...")
    detections, detection_img = detect_vehicles(
        processed_img,
        confidence=YOLO_CONFIDENCE,
    )
    vehicles_detected = len([d for d in detections if d.get("class_name") != "Person"])
    log_service.add_log(detection_id, f"Detected {vehicles_detected} vehicle(s).")

    # 4. Violation checks
    log_service.add_log(detection_id, "Checking for helmet violations...")
    helmet_violations, hl = check_helmet_violation(detections, processed_img)
    log_service.add_raw_logs(detection_id, hl)

    log_service.add_log(detection_id, "Checking for triple riding...")
    triple_violations, tl = check_triple_riding(detections)
    log_service.add_raw_logs(detection_id, tl)

    log_service.add_log(detection_id, "Checking for red-light violations...")
    red_light_violations, rl = check_red_light_violation(
        detections,
        processed_img.shape,
        stop_line_y_ratio=STOP_LINE_RATIO,
    )
    log_service.add_raw_logs(detection_id, rl)

    all_violations = helmet_violations + triple_violations + red_light_violations
    log_service.add_log(
        detection_id,
        f"Found {len(all_violations)} violation(s) "
        f"(helmet={len(helmet_violations)}, triple={len(triple_violations)}, "
        f"red_light={len(red_light_violations)})."
    )

    # 5. Plate recognition
    log_service.add_log(detection_id, "Running license plate OCR...")
    plates = PlateReader().process(processed_img, detections)
    log_service.add_log(detection_id, f"Recognised {len(plates)} plate(s).")

    # 6. Annotate image
    log_service.add_log(detection_id, "Annotating image with results...")
    annotated_img = annotate_image(
        processed_img,
        detections,
        violations=all_violations,
        plates=plates,
    )

    # 7. Save result images
    processed_path = RESULTS_DIR / f"{detection_id}_processed.jpg"
    annotated_path = RESULTS_DIR / f"{detection_id}_annotated.jpg"
    cv2.imwrite(str(processed_path), processed_img)
    cv2.imwrite(str(annotated_path), annotated_img)
    log_service.add_log(detection_id, "Saved processed & annotated images.")

    # 8. Store violations in DB
    for v in all_violations:
        violation_record = {
            "detection_id": detection_id,
            "violation_type": v.get("type", "unknown"),
            "vehicle_type": v.get("vehicle_type", "unknown"),
            "confidence": v.get("confidence", 0.0),
            "plate_text": next(
                (p.get("text") for p in plates if p.get("vehicle_id") == v.get("vehicle_id")),
                None,
            ),
            "bbox": v.get("bbox"),
            "timestamp": datetime.utcnow().isoformat(),
            "image_path": annotated_path.name,
        }
        import asyncio
        if asyncio.iscoroutinefunction(store_violation):
            await store_violation(violation_record)
        else:
            store_violation(violation_record)
    log_service.add_log(detection_id, "Violations persisted to database.")

    # 9. Build response
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    log_service.add_log(detection_id, f"Pipeline complete in {elapsed_ms} ms.")

    return {
        "success": True,
        "detection_id": detection_id,
        "vehicles_detected": vehicles_detected,
        "violations": all_violations,
        "plates_recognized": plates,
        "images": {
            "original": _encode_image_b64(original_img),
            "processed": _encode_image_b64(processed_img),
            "annotated": _encode_image_b64(annotated_img),
        },
        "processing_logs": log_service.get_logs(detection_id),
        "processing_time_ms": elapsed_ms,
    }
