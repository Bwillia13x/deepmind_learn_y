"""API v1 package."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics_router,
    auth_router,
    curriculum_router,
    reports_router,
    sessions_router,
    students_router,
)
from app.api.v1.websockets import voice_router

# Create main v1 router
router = APIRouter(prefix="/v1")

# Include REST API routers
router.include_router(auth_router)
router.include_router(students_router)
router.include_router(sessions_router)
router.include_router(reports_router)
router.include_router(curriculum_router)
router.include_router(analytics_router)

# Include WebSocket router
router.include_router(voice_router)

__all__ = ["router"]
