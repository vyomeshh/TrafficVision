import io
import csv
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.fallback_service import get_violations

router = APIRouter()

@router.get("/{report_type}")
async def export_report(report_type: str):
    """Generate and return a CSV report."""
    if report_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Unsupported report type")

    try:
        if report_type == "weekly":
            limit = 1000
        elif report_type == "monthly":
            limit = 5000
        else: # daily
            limit = 200
            
        import asyncio
        if asyncio.iscoroutinefunction(get_violations):
            data = await get_violations(limit=limit)
        else:
            data = get_violations(limit=limit)
            
        # fallback_service returns {"violations": [...]}, models returns a list
        if isinstance(data, dict):
            violations = data.get("violations", [])
        else:
            violations = data

        # Generate CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Detection ID", "Date", "Vehicle Type", "Violation Type", "License Plate", "Confidence"])

        for v in violations:
            writer.writerow([
                v.get("detection_id", ""),
                v.get("timestamp", ""),
                v.get("vehicle_type", ""),
                v.get("violation_type", ""),
                v.get("license_plate", ""),
                v.get("confidence", 0.0),
            ])

        output.seek(0)
        filename = f"traffic_violations_{report_type}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {exc}"
        )
