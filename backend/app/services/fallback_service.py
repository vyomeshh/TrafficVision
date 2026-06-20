import traceback

class FallbackModels:
    @staticmethod
    def preprocess_image(image_path: str):
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError("Could not read image")
        return img, img, ["[PREPROCESS] Fallback stub used."]

    @staticmethod
    def detect_vehicles(img, **kw):
        return [], img

    @staticmethod
    def annotate_image(img, detections, violations=None, plates=None, **kw):
        return img

    @staticmethod
    def check_helmet_violation(detections, img, **kw):
        return [], []

    @staticmethod
    def check_triple_riding(detections, **kw):
        return [], []

    @staticmethod
    def check_red_light_violation(detections, image_shape, **kw):
        return [], []

    @staticmethod
    def check_seatbelt_compliance(detections, img, **kw):
        return [], []

    @staticmethod
    def check_wrong_side_driving(detections, img_width, **kw):
        return [], []

    @staticmethod
    def check_illegal_parking(detections, img_shape, **kw):
        return [], []

    class PlateReaderFallback:
        def process(self, img, detections, **kw):
            return []

_models_available = False
try:
    from app.core.vision.preprocessor import preprocess_image
    from app.core.vision.detector import detect_vehicles, annotate_image
    from app.core.rules.helmet_check import check_helmet_violation
    from app.core.rules.triple_riding import check_triple_riding
    from app.core.rules.red_light import check_red_light_violation
    from app.core.rules.seatbelt import check_seatbelt_compliance
    from app.core.rules.wrong_side import check_wrong_side_driving
    from app.core.rules.illegal_parking import check_illegal_parking
    from app.core.ocr.plate_reader import PlateReader
    _models_available = True
except ImportError as exc:
    traceback.print_exc()
    print(f"[WARN] Core model modules not fully available: {exc}")
    print("[WARN] Detection endpoints will return errors until modules are installed.")
    preprocess_image = FallbackModels.preprocess_image
    detect_vehicles = FallbackModels.detect_vehicles
    annotate_image = FallbackModels.annotate_image
    check_helmet_violation = FallbackModels.check_helmet_violation
    check_triple_riding = FallbackModels.check_triple_riding
    check_red_light_violation = FallbackModels.check_red_light_violation
    check_seatbelt_compliance = FallbackModels.check_seatbelt_compliance
    check_wrong_side_driving = FallbackModels.check_wrong_side_driving
    check_illegal_parking = FallbackModels.check_illegal_parking
    PlateReader = FallbackModels.PlateReaderFallback

_db_available = False
_in_memory_violations = []

try:
    from app.database.connection import init_db
    from app.database.models import (
        insert_violation as store_violation,
        get_violations,
        get_analytics,
        get_daily_counts as get_report,
    )
    _db_available = True
except ImportError as exc:
    print(f"[WARN] Database module not available: {exc}")
    print("[WARN] Using in-memory storage fallback.")

    def init_db():
        print("[DB-FALLBACK] In-memory database initialized.")

    async def store_violation(violation: dict):
        _in_memory_violations.append(violation)

    async def get_violations(
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

    async def get_analytics():
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
    
    async def get_report(start_date=None, end_date=None):
        # Generate some mock daily data for the CSV if in-memory is empty, 
        # or aggregate the in-memory violations
        from datetime import datetime, timedelta
        if not _in_memory_violations:
            return [{
                "date": datetime.utcnow().strftime('%Y-%m-%d'),
                "total": 0,
                "helmet_violations": 0,
                "triple_riding_violations": 0,
                "red_light_violations": 0,
            }]
            
        # Very simple aggregation by date for in-memory
        report_map = {}
        for v in _in_memory_violations:
            ts_str = v.get("timestamp", datetime.utcnow().isoformat())
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                d_str = dt.strftime('%Y-%m-%d')
            except ValueError:
                d_str = datetime.utcnow().strftime('%Y-%m-%d')
                
            if d_str not in report_map:
                report_map[d_str] = {"date": d_str, "total": 0, "helmet_violations": 0, "triple_riding_violations": 0, "red_light_violations": 0}
                
            report_map[d_str]["total"] += 1
            vt = v.get("violation_type")
            if vt == "No Helmet":
                report_map[d_str]["helmet_violations"] += 1
            elif vt == "Triple Riding":
                report_map[d_str]["triple_riding_violations"] += 1
            elif vt == "Red Light Violation":
                report_map[d_str]["red_light_violations"] += 1
                
        return list(report_map.values())
