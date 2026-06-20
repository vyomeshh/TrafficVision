import io
import csv
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.fallback_service import get_report

router = APIRouter()

@router.get("/{report_type}")
async def export_report(report_type: str):
    """Generate and return a CSV report."""
    if report_type != "daily":
        raise HTTPException(status_code=400, detail="Unsupported report type")

    try:
        # Last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        data = await get_report(start_date, end_date)

        # Generate CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Total Violations", "Helmet", "Triple Riding", "Red Light"])

        for row in data:
            writer.writerow([
                row.get("date", ""),
                row.get("total", 0),
                row.get("helmet_violations", 0),
                row.get("triple_riding_violations", 0),
                row.get("red_light_violations", 0),
            ])

        output.seek(0)
        filename = f"traffic_violations_{end_date.strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {exc}"
        )
