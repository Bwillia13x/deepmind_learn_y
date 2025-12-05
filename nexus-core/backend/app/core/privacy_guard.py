"""
Privacy Guard - PII Scrubbing Middleware for NEXUS.

This module implements the core privacy protection layer as defined in
.context/02_privacy_charter.md. All data passing through the system
must be scrubbed of Personally Identifiable Information (PII) before
logging or sending to external LLM providers.

CRITICAL: This middleware is the first line of defense for FOIP compliance.
"""

import re
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class PIIPattern:
    """Compiled regex patterns for PII detection."""

    # Email addresses
    EMAIL = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )

    # Phone numbers (North American format with variations, including 7-digit local)
    PHONE = re.compile(
        r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{3}[-.\s]?\d{4}\b",
    )

    # Names (basic pattern - capitalized word pairs)
    # Note: This is intentionally broad to catch potential names
    NAME = re.compile(
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
    )

    # Social Insurance Numbers (Canadian SIN)
    SIN = re.compile(
        r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b",
    )

    # Student/ID numbers (generic numeric IDs)
    STUDENT_ID = re.compile(
        r"\b(?:student|id|#)[-:\s]*\d{5,10}\b",
        re.IGNORECASE,
    )

    # Addresses (basic street address pattern)
    ADDRESS = re.compile(
        r"\b\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Court|Ct)\b",
        re.IGNORECASE,
    )


class PIIPlaceholder:
    """Replacement placeholders for scrubbed PII."""

    EMAIL = "<EMAIL>"
    PHONE = "<PHONE>"
    NAME = "<NAME>"
    SIN = "<SIN>"
    STUDENT_ID = "<STUDENT_ID>"
    ADDRESS = "<ADDRESS>"


def scrub_pii(text: str) -> str:
    """
    Scrub all PII from the given text.

    Applies regex patterns to detect and replace personally identifiable
    information with safe placeholders. Order matters - more specific
    patterns are applied first.

    Args:
        text: The input text that may contain PII.

    Returns:
        The text with all detected PII replaced with placeholders.

    Example:
        >>> scrub_pii("Call John Smith at 555-123-4567")
        'Call <NAME> at <PHONE>'
    """
    if not text:
        return text

    # Apply patterns in order of specificity (most specific first)
    result = text

    # Email (very specific pattern)
    result = PIIPattern.EMAIL.sub(PIIPlaceholder.EMAIL, result)

    # Student IDs (with keyword context) - MUST come before SIN
    result = PIIPattern.STUDENT_ID.sub(PIIPlaceholder.STUDENT_ID, result)

    # SIN (specific format)
    result = PIIPattern.SIN.sub(PIIPlaceholder.SIN, result)

    # Phone numbers
    result = PIIPattern.PHONE.sub(PIIPlaceholder.PHONE, result)

    # Addresses
    result = PIIPattern.ADDRESS.sub(PIIPlaceholder.ADDRESS, result)

    # Names (last, as it's the broadest pattern)
    result = PIIPattern.NAME.sub(PIIPlaceholder.NAME, result)

    return result


def scrub_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively scrub PII from all string values in a dictionary.

    Args:
        data: Dictionary that may contain PII in string values.

    Returns:
        New dictionary with all string values scrubbed.
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = scrub_pii(value)
        elif isinstance(value, dict):
            result[key] = scrub_dict(value)
        elif isinstance(value, list):
            result[key] = [
                scrub_dict(item) if isinstance(item, dict) else scrub_pii(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def contains_pii(text: str) -> bool:
    """
    Check if text contains any detectable PII.

    Args:
        text: The input text to check.

    Returns:
        True if any PII pattern matches, False otherwise.
    """
    if not text:
        return False

    return any(
        [
            PIIPattern.EMAIL.search(text),
            PIIPattern.PHONE.search(text),
            PIIPattern.NAME.search(text),
            PIIPattern.SIN.search(text),
            PIIPattern.STUDENT_ID.search(text),
            PIIPattern.ADDRESS.search(text),
        ]
    )


class PrivacyViolationError(Exception):
    """Raised when unscrubbed PII is detected in a restricted context."""

    def __init__(self, message: str = "PII detected in restricted context"):
        self.message = message
        super().__init__(self.message)


class PrivacyGuardMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that scrubs PII from all logged request/response data.

    This middleware intercepts all requests and ensures that any logging
    or analytics only receives PII-scrubbed data. The actual request/response
    data passed to handlers is NOT modified - only logging is sanitized.

    Per .context/02_privacy_charter.md:
    - All logs must be PII-free
    - Original data flows through for processing
    - Scrubbed data used only for observability
    """

    def __init__(
        self,
        app: ASGIApp,
        log_callback: Callable[[dict[str, Any]], None] | None = None,
    ):
        """
        Initialize the privacy guard middleware.

        Args:
            app: The ASGI application to wrap.
            log_callback: Optional callback for logging sanitized request data.
        """
        super().__init__(app)
        self.log_callback = log_callback

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, scrubbing PII from any logged data.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response.
        """
        # Build sanitized log entry
        sanitized_log = {
            "method": request.method,
            "path": str(request.url.path),
            "query_params": scrub_dict(dict(request.query_params)),
        }

        # Read and sanitize body for logging (if present)
        # Note: Body can only be read once, so we're careful here
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    import json

                    try:
                        body_json = json.loads(body)
                        sanitized_log["body"] = scrub_dict(body_json)
                    except json.JSONDecodeError:
                        sanitized_log["body"] = scrub_pii(body.decode("utf-8", errors="replace"))
            except Exception:
                # If we can't read the body, that's okay for logging purposes
                sanitized_log["body"] = "<unreadable>"

        # Call the logging callback if provided
        if self.log_callback:
            self.log_callback(sanitized_log)

        # Process the actual request (unmodified)
        response = await call_next(request)

        return response


def create_privacy_guard_middleware(
    log_callback: Callable[[dict[str, Any]], None] | None = None,
) -> type[PrivacyGuardMiddleware]:
    """
    Factory function to create a configured PrivacyGuardMiddleware class.

    Args:
        log_callback: Optional callback for logging sanitized request data.

    Returns:
        Configured middleware class for use with FastAPI.
    """

    class ConfiguredPrivacyGuard(PrivacyGuardMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(app, log_callback=log_callback)

    return ConfiguredPrivacyGuard
