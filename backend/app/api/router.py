from fastapi import APIRouter

from app.api.endpoints import detect, violations, analytics, reports, health, logs

api_router = APIRouter()

api_router.include_router(detect.router, prefix="/detect", tags=["Detection"])
api_router.include_router(violations.router, prefix="/violations", tags=["Violations"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(logs.router, prefix="/stream-logs", tags=["Logs"])
