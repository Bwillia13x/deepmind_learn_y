"""API v1 endpoints package."""

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.curriculum import router as curriculum_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.students import router as students_router

__all__ = [
    "analytics_router",
    "auth_router",
    "students_router",
    "sessions_router",
    "reports_router",
    "curriculum_router",
]
