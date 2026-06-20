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
    import asyncio
    try:
        if asyncio.iscoroutinefunction(get_violations):
            data = await get_violations(
                vehicle_type=vehicle_type,
                violation_type=violation_type,
                search=search,
                limit=limit,
                offset=offset,
            )
        else:
            filters = {}
            if vehicle_type: filters["vehicle_type"] = vehicle_type
            if violation_type: filters["violation_type"] = violation_type
            if search: filters["plate_search"] = search
            db_data = get_violations(
                filters=filters,
                limit=limit,
                offset=offset,
            )
            # Make response match fallback dict structure
            data = {"violations": db_data, "total": len(db_data)}
        return {"success": True, "data": data}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch violations: {exc}"
        )
