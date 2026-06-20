from fastapi import APIRouter
from app.services.fallback_service import _models_available, _db_available

router = APIRouter()

@router.get("")
def health_check():
    """Simple status check for the API and dependencies."""
    return {
        "status": "ok",
        "models_loaded": _models_available,
        "database_connected": _db_available,
    }
