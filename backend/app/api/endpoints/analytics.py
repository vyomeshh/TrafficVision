from fastapi import APIRouter, HTTPException

from app.services.fallback_service import get_analytics

router = APIRouter()

@router.get("")
async def dashboard_analytics():
    """Return aggregated statistics for the dashboard charts."""
    import asyncio
    try:
        if asyncio.iscoroutinefunction(get_analytics):
            data = await get_analytics()
        else:
            data = get_analytics()
        return {"success": True, "data": data}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load analytics: {exc}"
        )
