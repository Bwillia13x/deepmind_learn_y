"""
Sessions API endpoints.

CRUD operations for Oracy Sessions.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.db.models import EngagementLevel, OracySession, ScoutReport, SessionStatus

router = APIRouter(prefix="/sessions", tags=["sessions"])


# === Pydantic Schemas ===


class OracySessionResponse(BaseModel):
    """Response schema for an oracy session."""

    id: str
    student_id: str
    status: SessionStatus
    duration_seconds: int | None = None
    turn_count: int
    transcript_summary: str | None = None
    curriculum_outcome_ids: str | None = None
    avg_response_latency_ms: float | None = None
    started_at: datetime
    ended_at: datetime | None = None

    class Config:
        from_attributes = True


class OracySessionListResponse(BaseModel):
    """Response schema for a list of oracy sessions."""

    sessions: list[OracySessionResponse]
    total: int
    page: int
    page_size: int


class ScoutReportResponse(BaseModel):
    """Response schema for a scout report."""

    id: str
    oracy_session_id: str
    engagement_level: EngagementLevel
    insight_text: str
    linguistic_observations: str | None = None
    curriculum_connections: str | None = None
    recommended_next_steps: str | None = None
    is_reviewed: bool
    teacher_notes: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    class Config:
        from_attributes = True


class ScoutReportUpdate(BaseModel):
    """Request schema for updating a scout report."""

    teacher_notes: str | None = Field(None, max_length=2000)
    is_reviewed: bool | None = None


class AudioChunk(BaseModel):
    """A single audio chunk from offline queue."""

    audio_data: str  # Base64 encoded audio
    timestamp: int  # Unix timestamp in ms


class OfflineSyncRequest(BaseModel):
    """Request schema for syncing offline audio chunks."""

    session_id: str
    chunks: list[AudioChunk]


class OfflineSyncResponse(BaseModel):
    """Response schema for offline sync."""

    synced_count: int
    session_id: str
    status: str


# === Endpoints ===


@router.get("", response_model=OracySessionListResponse)
async def list_oracy_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    student_id: str | None = Query(None, description="Filter by student ID"),
    status_filter: SessionStatus | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> OracySessionListResponse:
    """
    List oracy sessions with optional filters.

    Supports pagination and filtering by student and status.
    """
    query = select(OracySession)

    if student_id:
        query = query.where(OracySession.student_id == student_id)
    if status_filter:
        query = query.where(OracySession.status == status_filter)

    # Count total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get page
    query = query.order_by(OracySession.started_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return OracySessionListResponse(
        sessions=[OracySessionResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{session_id}", response_model=OracySessionResponse)
async def get_oracy_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OracySessionResponse:
    """Get a specific oracy session by ID."""
    result = await db.execute(
        select(OracySession).where(OracySession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oracy session {session_id} not found",
        )

    return OracySessionResponse.model_validate(session)


@router.get("/{session_id}/report", response_model=ScoutReportResponse)
async def get_scout_report(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScoutReportResponse:
    """Get the scout report for an oracy session."""
    result = await db.execute(
        select(OracySession)
        .where(OracySession.id == session_id)
        .options(selectinload(OracySession.scout_report))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oracy session {session_id} not found",
        )

    if not session.scout_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scout report found for session {session_id}",
        )

    return ScoutReportResponse.model_validate(session.scout_report)


@router.patch("/{session_id}/report", response_model=ScoutReportResponse)
async def update_scout_report(
    session_id: str,
    update: ScoutReportUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScoutReportResponse:
    """
    Update a scout report.

    Teachers can add notes and mark reports as reviewed.
    """
    result = await db.execute(
        select(ScoutReport).where(ScoutReport.oracy_session_id == session_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scout report found for session {session_id}",
        )

    # Apply updates
    if update.teacher_notes is not None:
        report.teacher_notes = update.teacher_notes
    if update.is_reviewed is not None:
        report.is_reviewed = update.is_reviewed
        if update.is_reviewed:
            report.reviewed_at = datetime.now()

    await db.commit()
    await db.refresh(report)

    return ScoutReportResponse.model_validate(report)


@router.post("/sync", response_model=OfflineSyncResponse)
async def sync_offline_audio(
    sync_request: OfflineSyncRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OfflineSyncResponse:
    """
    Sync offline audio chunks from PWA.

    When the app was offline, audio chunks are queued locally.
    This endpoint receives them when back online for processing.

    Note: Audio is processed for transcript but NOT stored (per privacy charter).
    """
    import logging

    logger = logging.getLogger(__name__)

    session_id = sync_request.session_id
    chunks = sync_request.chunks

    logger.info(f"Received {len(chunks)} offline chunks for session {session_id}")

    # Verify session exists
    result = await db.execute(
        select(OracySession).where(OracySession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oracy session {session_id} not found",
        )

    # Process chunks (in production, would send to STT service)
    synced_count = 0
    for chunk in sorted(chunks, key=lambda c: c.timestamp):
        # In production: decode base64, send to STT, append to transcript
        # For now, just count as synced
        synced_count += 1
        logger.debug(f"Processed chunk at timestamp {chunk.timestamp}")

    # Update session turn count
    session.turn_count += synced_count

    await db.commit()

    return OfflineSyncResponse(
        synced_count=synced_count,
        session_id=session_id,
        status="synced",
    )
