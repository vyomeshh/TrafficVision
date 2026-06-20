"""
TrafficVision AI - FastAPI Application
=======================================

Main API server providing endpoints for traffic violation detection,
analytics, reporting, and real-time processing log streaming.
"""

import asyncio
import base64
import csv
import io
import os
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8s.pt")
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.25"))
STOP_LINE_RATIO = float(os.getenv("STOP_LINE_RATIO", "0.7"))

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Graceful imports for core modules (server starts even if models missing)
# ---------------------------------------------------------------------------
_models_available = False

try:
    from core.vision.preprocessor import preprocess_image
    from core.vision.detector import detect_vehicles, annotate_image
    from core.rules.helmet_check import check_helmet_violations
    from core.rules.triple_riding import check_triple_riding
    from core.rules.red_light import check_red_light_violation
    from core.ocr.plate_reader import recognize_plates
    _models_available = True
except ImportError as exc:
    import traceback
    traceback.print_exc()
    print(f"[WARN] Core model modules not fully available: {exc}")
    print("[WARN] Detection endpoints will return errors until modules are installed.")

    # Stub functions so the server can start
    def preprocess_image(img, **kw):      # noqa: E302
        return img

    def detect_vehicles(img, **kw):       # noqa: E302
        return [], img

    def annotate_image(img, detections, violations=None, plates=None, **kw):  # noqa: E302
        return img

    def check_helmet_violations(img, detections, **kw):   # noqa: E302
        return []

    def check_triple_riding(img, detections, **kw):       # noqa: E302
        return []

    def check_red_light_violation(img, detections, **kw):  # noqa: E302
        return []

    def recognize_plates(img, detections, **kw):           # noqa: E302
        return []

# ---------------------------------------------------------------------------
# Database (graceful import)
# ---------------------------------------------------------------------------
_db_available = False

try:
    from database.db import (
        init_db,
        store_violation,
        get_violations,
        get_analytics,
        get_report,
    )
    _db_available = True
except ImportError as exc:
    print(f"[WARN] Database module not available: {exc}")
    print("[WARN] Using in-memory storage fallback.")

    # In-memory fallback storage
    _in_memory_violations: list[dict] = []

    async def init_db():  # noqa: E302
        print("[DB-FALLBACK] In-memory database initialized.")

    async def store_violation(violation: dict):  # noqa: E302
        _in_memory_violations.append(violation)

    async def get_violations(  # noqa: E302
        vehicle_type=None, violation_type=None, search=None, limit=20, offset=0
    ):
        results = _in_memory_violations[:]
        if vehicle_type:
            results = [v for v in results if v.get("vehicle_type") == vehicle_type]
        if violation_type:
            results = [v for v in results if v.get("violation_type") == violation_type]
        if search:
            results = [
                v for v in results
                if search.lower() in (v.get("plate_text", "") or "").lower()
            ]
        total = len(results)
        return {"violations": results[offset : offset + limit], "total": total}

    async def get_analytics():  # noqa: E302
        return {
            "violation_distribution": {},
            "daily_counts": [],
            "monthly_trend": [],
            "vehicle_classification": {},
            "total_stats": {
                "total_violations": len(_in_memory_violations),
                "total_vehicles": 0,
                "plates_recognized": 0,
                "avg_processing_time_ms": 0,
            },
        }

    async def get_report(report_type: str):  # noqa: E302
        return {"report_type": report_type, "data": _in_memory_violations[:]}

# ---------------------------------------------------------------------------
# In-memory log streaming store  {detection_id: [log_messages]}
# ---------------------------------------------------------------------------
_processing_logs: dict[str, list[str]] = {}
_processing_events: dict[str, asyncio.Event] = {}

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TrafficVision AI",
    description=(
        "Intelligent traffic monitoring API — vehicle detection, violation "
        "identification, and license plate recognition powered by YOLOv8 "
        "and PaddleOCR."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded / processed images as static files
app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """Initialise the database and ensure required directories exist."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    await init_db()
    print("[STARTUP] TrafficVision AI server ready.")
    print(f"[STARTUP] Models available: {_models_available}")
    print(f"[STARTUP] Database available: {_db_available}")


# ===================================================================
# Utility helpers
# ===================================================================

def _generate_detection_id() -> str:
    """Return a human-friendly detection ID like ``TR-2026-A3F``."""
    now = datetime.utcnow()
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"TR-{now.year}-{short_uuid}"


def _encode_image_b64(img: np.ndarray, ext: str = ".jpg") -> str:
    """Encode a NumPy/OpenCV image to a base64 string."""
    success, buffer = cv2.imencode(ext, img)
    if not success:
        return ""
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def _add_log(detection_id: str, message: str):
    """Append a timestamped log line for the given detection run."""
    ts = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
    entry = f"[{ts}] {message}"
    _processing_logs.setdefault(detection_id, []).append(entry)
    # Signal any listeners
    evt = _processing_events.get(detection_id)
    if evt:
        evt.set()


# ===================================================================
# POST /api/detect
# ===================================================================
@app.post("/api/detect")
async def detect(image: UploadFile = File(...)):
    """
    Accept an uploaded traffic image, run the full detection pipeline,
    and return structured results with annotated images.
    """
    detection_id = _generate_detection_id()
    _processing_logs[detection_id] = []
    _processing_events[detection_id] = asyncio.Event()
    start_time = time.perf_counter()

    try:
        # ── 1. Read & save uploaded image ────────────────────────────
        _add_log(detection_id, "Reading uploaded file…")
        contents = await image.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        file_ext = Path(image.filename or "upload.jpg").suffix or ".jpg"
        upload_filename = f"{detection_id}{file_ext}"
        upload_path = UPLOADS_DIR / upload_filename

        with open(upload_path, "wb") as f:
            f.write(contents)
        _add_log(detection_id, f"Saved upload → {upload_filename}")

        # Decode into OpenCV image
        np_arr = np.frombuffer(contents, np.uint8)
        original_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if original_img is None:
            raise HTTPException(status_code=400, detail="Could not decode image.")

        # ── 2. Pre-process ───────────────────────────────────────────
        _add_log(detection_id, "Pre-processing image…")
        processed_img = preprocess_image(original_img)

        # ── 3. YOLOv8 Vehicle Detection ──────────────────────────────
        _add_log(detection_id, "Running YOLOv8 vehicle detection…")
        detections, detection_img = detect_vehicles(
            processed_img,
            model_path=YOLO_MODEL,
            confidence=YOLO_CONFIDENCE,
        )
        vehicles_detected = len(detections)
        _add_log(detection_id, f"Detected {vehicles_detected} vehicle(s).")

        # ── 4. Violation checks ──────────────────────────────────────
        _add_log(detection_id, "Checking for helmet violations…")
        helmet_violations = check_helmet_violations(processed_img, detections)

        _add_log(detection_id, "Checking for triple riding…")
        triple_violations = check_triple_riding(processed_img, detections)

        _add_log(detection_id, "Checking for red-light violations…")
        red_light_violations = check_red_light_violation(
            processed_img,
            detections,
            stop_line_ratio=STOP_LINE_RATIO,
        )

        all_violations = helmet_violations + triple_violations + red_light_violations
        _add_log(
            detection_id,
            f"Found {len(all_violations)} violation(s) "
            f"(helmet={len(helmet_violations)}, triple={len(triple_violations)}, "
            f"red_light={len(red_light_violations)}).",
        )

        # ── 5. Plate recognition ─────────────────────────────────────
        _add_log(detection_id, "Running license plate OCR…")
        plates = recognize_plates(processed_img, detections)
        _add_log(detection_id, f"Recognised {len(plates)} plate(s).")

        # ── 6. Annotate image ────────────────────────────────────────
        _add_log(detection_id, "Annotating image with results…")
        annotated_img = annotate_image(
            processed_img,
            detections,
            violations=all_violations,
            plates=plates,
        )

        # ── 7. Save result images ────────────────────────────────────
        processed_path = RESULTS_DIR / f"{detection_id}_processed.jpg"
        annotated_path = RESULTS_DIR / f"{detection_id}_annotated.jpg"
        cv2.imwrite(str(processed_path), processed_img)
        cv2.imwrite(str(annotated_path), annotated_img)
        _add_log(detection_id, "Saved processed & annotated images.")

        # ── 8. Store violations in DB ────────────────────────────────
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
                "image_path": str(annotated_path),
            }
            await store_violation(violation_record)
        _add_log(detection_id, "Violations persisted to database.")

        # ── 9. Build response ────────────────────────────────────────
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        _add_log(detection_id, f"Pipeline complete in {elapsed_ms} ms.")

        return JSONResponse(
            content={
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
                "processing_logs": _processing_logs.get(detection_id, []),
                "processing_time_ms": elapsed_ms,
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        _add_log(detection_id, f"ERROR: {exc}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "detection_id": detection_id,
                "error": str(exc),
                "processing_logs": _processing_logs.get(detection_id, []),
                "processing_time_ms": elapsed_ms,
            },
        )


# ===================================================================
# GET /api/violations
# ===================================================================
@app.get("/api/violations")
async def list_violations(
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    violation_type: Optional[str] = Query(None, description="Filter by violation type"),
    search: Optional[str] = Query(None, description="Search by plate text"),
    limit: int = Query(20, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Return a paginated list of detected violations with optional filters."""
    try:
        data = await get_violations(
            vehicle_type=vehicle_type,
            violation_type=violation_type,
            search=search,
            limit=limit,
            offset=offset,
        )
        return JSONResponse(content={"success": True, **data})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ===================================================================
# GET /api/analytics
# ===================================================================
@app.get("/api/analytics")
async def analytics():
    """
    Return aggregated analytics for dashboard visualisation:
    - violation_distribution  (pie chart)
    - daily_counts            (bar chart)
    - monthly_trend           (line chart)
    - vehicle_classification  (doughnut chart)
    - total_stats             (KPI cards)
    """
    try:
        data = await get_analytics()
        return JSONResponse(content={"success": True, **data})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ===================================================================
# GET /api/reports/{report_type}
# ===================================================================
@app.get("/api/reports/{report_type}")
async def reports(
    report_type: str,
    format: str = Query("json", regex="^(json|csv)$", description="Output format"),
):
    """
    Generate a daily, weekly, or monthly report.
    Supports JSON and CSV output formats.
    """
    if report_type not in ("daily", "weekly", "monthly"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_type '{report_type}'. Must be daily, weekly, or monthly.",
        )

    try:
        data = await get_report(report_type)

        if format == "csv":
            return _build_csv_response(data, report_type)

        return JSONResponse(content={"success": True, "report_type": report_type, **data})

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _build_csv_response(data: dict, report_type: str) -> StreamingResponse:
    """Convert report data dict to a streaming CSV response."""
    rows = data.get("data", [])
    if not rows:
        rows = []

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("No data available\n")

    output.seek(0)
    filename = f"trafficvision_report_{report_type}_{datetime.utcnow():%Y%m%d}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ===================================================================
# GET /api/health
# ===================================================================
@app.get("/api/health")
async def health():
    """Return system health status."""
    return JSONResponse(
        content={
            "status": "online",
            "timestamp": datetime.utcnow().isoformat(),
            "models_loaded": _models_available,
            "database_connected": _db_available,
            "yolo_model": YOLO_MODEL,
            "yolo_confidence": YOLO_CONFIDENCE,
            "uploads_dir": str(UPLOADS_DIR),
            "results_dir": str(RESULTS_DIR),
        }
    )


# ===================================================================
# GET /api/stream-logs/{detection_id}  (Server-Sent Events)
# ===================================================================
@app.get("/api/stream-logs/{detection_id}")
async def stream_logs(detection_id: str):
    """
    Stream processing logs for a specific detection run via SSE.
    The client receives log lines as ``data: …`` events in real-time.
    """
    if detection_id not in _processing_logs:
        raise HTTPException(status_code=404, detail="Detection ID not found.")

    async def _event_generator():
        sent_index = 0
        while True:
            logs = _processing_logs.get(detection_id, [])
            while sent_index < len(logs):
                yield f"data: {logs[sent_index]}\n\n"
                sent_index += 1

            # Check if processing is complete (last log contains "complete")
            if logs and "complete" in logs[-1].lower():
                yield "data: [STREAM_END]\n\n"
                break

            # Wait for new log entries (or timeout after 30 s)
            evt = _processing_events.get(detection_id)
            if evt:
                evt.clear()
                try:
                    await asyncio.wait_for(evt.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield "data: [STREAM_TIMEOUT]\n\n"
                    break

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ===================================================================
# Root redirect to docs
# ===================================================================
@app.get("/")
async def root():
    """Redirect to API documentation."""
    return JSONResponse(
        content={
            "service": "TrafficVision AI",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
        }
    )
