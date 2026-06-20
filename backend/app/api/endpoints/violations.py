from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from app.services.fallback_service import get_violations

router = APIRouter()

@router.get("")
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
        return {"success": True, "data": data}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch violations: {exc}"
        )
