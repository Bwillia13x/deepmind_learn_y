"""Core module exports."""

from app.core.config import get_settings, settings
from app.core.database import Base, close_db, get_db, get_db_context, init_db
from app.core.privacy_guard import (
    PIIPattern,
    PIIPlaceholder,
    PrivacyGuardMiddleware,
    PrivacyViolationError,
    contains_pii,
    create_privacy_guard_middleware,
    scrub_dict,
    scrub_pii,
)

__all__ = [
    # Config
    "settings",
    "get_settings",
    # Database
    "Base",
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    # Privacy
    "scrub_pii",
    "scrub_dict",
    "contains_pii",
    "PIIPattern",
    "PIIPlaceholder",
    "PrivacyViolationError",
    "PrivacyGuardMiddleware",
    "create_privacy_guard_middleware",
]
