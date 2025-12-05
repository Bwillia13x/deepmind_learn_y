"""
NEXUS Backend Application.

Main FastAPI application entry point with middleware configuration
and route registration. Privacy-first design per .context/02_privacy_charter.md.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.privacy_guard import create_privacy_guard_middleware, scrub_pii

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def privacy_log_callback(data: dict[str, Any]) -> None:
    """
    Callback for logging sanitized request data.

    All logged data has already passed through PII scrubbing.
    """
    # Only log in debug mode to avoid excessive output
    if settings.debug:
        logger.debug(f"Request: {data.get('method')} {data.get('path')}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    if not settings.is_production:
        # Initialize database tables in development
        await init_db()
        logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Digital Para-Educator Assistant for Alberta K-12 Schools",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# === Middleware ===

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Privacy Guard middleware (logs sanitized data only)
PrivacyGuardMiddleware = create_privacy_guard_middleware(
    log_callback=privacy_log_callback if settings.debug else None
)
app.add_middleware(PrivacyGuardMiddleware)


# === Routes ===

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


# API version info
@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if not settings.is_production else "disabled",
    }


# Include API v1 routes
app.include_router(v1_router, prefix="/api")


# === Error Handlers ===


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> dict[str, str]:
    """
    Global exception handler with PII scrubbing.

    Ensures no PII leaks in error responses.
    """
    # Scrub error message before logging or returning
    error_message = scrub_pii(str(exc))
    logger.error(f"Unhandled exception: {error_message}")

    return {
        "detail": "An internal error occurred. Please try again later."
        if settings.is_production
        else error_message
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
    )
