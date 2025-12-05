"""
Reports API endpoints.

Endpoints for accessing and managing Scout Reports.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import TeacherAccess, get_db
from app.db.models import EngagementLevel, OracySession, ScoutReport, Teacher

router = APIRouter(prefix="/reports", tags=["reports"])


# === Pydantic Schemas ===


class ScoutReportResponse(BaseModel):
    """Response schema for a scout report."""

    id: str
    oracy_session_id: str
    teacher_id: str | None = None
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


class ScoutReportWithSessionResponse(ScoutReportResponse):
    """Scout report with embedded session info."""

    session_duration_seconds: int | None = None
    session_turn_count: int = 0
    student_code: str | None = None


class ScoutReportListResponse(BaseModel):
    """Response schema for a list of scout reports."""

    reports: list[ScoutReportWithSessionResponse]
    total: int
    page: int
    page_size: int


class ScoutReportUpdate(BaseModel):
    """Request schema for updating a scout report."""

    teacher_notes: str | None = Field(None, max_length=2000)
    is_reviewed: bool | None = None


class CopyableReportResponse(BaseModel):
    """Response schema optimized for copying to IPP documents."""

    insight_text: str
    linguistic_observations: str | None = None
    curriculum_connections: str | None = None
    recommended_next_steps: str | None = None
    formatted_text: str  # Ready-to-copy formatted text


# === Endpoints ===


@router.get("", response_model=ScoutReportListResponse)
async def list_scout_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    _teacher: TeacherAccess,  # Require teacher access in production
    teacher_id: str | None = Query(None, description="Filter by teacher ID"),
    is_reviewed: bool | None = Query(None, description="Filter by review status"),
    engagement_level: EngagementLevel | None = Query(None, description="Filter by engagement"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ScoutReportListResponse:
    """
    List scout reports with optional filters.

    Teachers can use this to find reports needing review.
    Requires authentication in production.
    """
    query = select(ScoutReport).options(
        selectinload(ScoutReport.oracy_session).selectinload(OracySession.student)
    )

    if teacher_id:
        query = query.where(ScoutReport.teacher_id == teacher_id)
    if is_reviewed is not None:
        query = query.where(ScoutReport.is_reviewed == is_reviewed)
    if engagement_level:
        query = query.where(ScoutReport.engagement_level == engagement_level)

    # Count total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get page
    query = query.order_by(ScoutReport.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = result.scalars().all()

    # Build response with session info
    response_reports = []
    for report in reports:
        session = report.oracy_session
        student_code = session.student.student_code if session and session.student else None

        response_reports.append(
            ScoutReportWithSessionResponse(
                id=report.id,
                oracy_session_id=report.oracy_session_id,
                teacher_id=report.teacher_id,
                engagement_level=report.engagement_level,
                insight_text=report.insight_text,
                linguistic_observations=report.linguistic_observations,
                curriculum_connections=report.curriculum_connections,
                recommended_next_steps=report.recommended_next_steps,
                is_reviewed=report.is_reviewed,
                teacher_notes=report.teacher_notes,
                created_at=report.created_at,
                reviewed_at=report.reviewed_at,
                session_duration_seconds=session.duration_seconds if session else None,
                session_turn_count=session.turn_count if session else 0,
                student_code=student_code,
            )
        )

    return ScoutReportListResponse(
        reports=response_reports,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}", response_model=ScoutReportWithSessionResponse)
async def get_scout_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _teacher: TeacherAccess,  # Require teacher access in production
) -> ScoutReportWithSessionResponse:
    """Get a specific scout report by ID. Requires authentication in production."""
    result = await db.execute(
        select(ScoutReport)
        .where(ScoutReport.id == report_id)
        .options(
            selectinload(ScoutReport.oracy_session).selectinload(OracySession.student)
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scout report {report_id} not found",
        )

    session = report.oracy_session
    student_code = session.student.student_code if session and session.student else None

    return ScoutReportWithSessionResponse(
        id=report.id,
        oracy_session_id=report.oracy_session_id,
        teacher_id=report.teacher_id,
        engagement_level=report.engagement_level,
        insight_text=report.insight_text,
        linguistic_observations=report.linguistic_observations,
        curriculum_connections=report.curriculum_connections,
        recommended_next_steps=report.recommended_next_steps,
        is_reviewed=report.is_reviewed,
        teacher_notes=report.teacher_notes,
        created_at=report.created_at,
        reviewed_at=report.reviewed_at,
        session_duration_seconds=session.duration_seconds if session else None,
        session_turn_count=session.turn_count if session else 0,
        student_code=student_code,
    )


@router.patch("/{report_id}", response_model=ScoutReportResponse)
async def update_scout_report(
    report_id: str,
    update: ScoutReportUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _teacher: TeacherAccess,  # Require teacher access in production
) -> ScoutReportResponse:
    """
    Update a scout report.

    Teachers can add notes and mark reports as reviewed.
    Requires authentication in production.
    """
    result = await db.execute(
        select(ScoutReport).where(ScoutReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scout report {report_id} not found",
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


@router.get("/{report_id}/copy", response_model=CopyableReportResponse)
async def get_copyable_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _teacher: TeacherAccess,  # Require teacher access in production
) -> CopyableReportResponse:
    """
    Get a scout report formatted for copying to IPP documents.

    This is the "killer feature" for teachers - one-click copy.
    Requires authentication in production.
    """
    result = await db.execute(
        select(ScoutReport).where(ScoutReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scout report {report_id} not found",
        )

    # Format for IPP copy
    sections = []
    sections.append(f"OBSERVATION SUMMARY\n{report.insight_text}")

    if report.linguistic_observations:
        sections.append(f"LANGUAGE DEVELOPMENT\n{report.linguistic_observations}")

    if report.curriculum_connections:
        sections.append(f"CURRICULUM CONNECTIONS\n{report.curriculum_connections}")

    if report.recommended_next_steps:
        sections.append(f"RECOMMENDED NEXT STEPS\n{report.recommended_next_steps}")

    formatted_text = "\n\n".join(sections)

    return CopyableReportResponse(
        insight_text=report.insight_text,
        linguistic_observations=report.linguistic_observations,
        curriculum_connections=report.curriculum_connections,
        recommended_next_steps=report.recommended_next_steps,
        formatted_text=formatted_text,
    )


class TranscriptResponse(BaseModel):
    """Response schema for session transcript."""

    report_id: str
    session_id: str
    student_code: str | None = None
    transcript_summary: str | None = None
    session_duration_seconds: int | None = None
    session_turn_count: int = 0
    started_at: datetime
    ended_at: datetime | None = None


@router.get("/{report_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _teacher: TeacherAccess,  # Require teacher access in production
) -> TranscriptResponse:
    """
    Get the transcript summary for a scout report's oracy session.

    Teachers can review the PII-scrubbed conversation summary
    to better understand the context behind the Scout Report insights.
    Requires authentication in production.

    Note: Full audio is NEVER stored per privacy charter. Only the
    summarized, anonymized transcript text is available.
    """
    result = await db.execute(
        select(ScoutReport)
        .where(ScoutReport.id == report_id)
        .options(
            selectinload(ScoutReport.oracy_session).selectinload(OracySession.student)
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scout report {report_id} not found",
        )

    session = report.oracy_session
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No oracy session found for report {report_id}",
        )

    student_code = session.student.student_code if session.student else None

    return TranscriptResponse(
        report_id=report_id,
        session_id=session.id,
        student_code=student_code,
        transcript_summary=session.transcript_summary,
        session_duration_seconds=session.duration_seconds,
        session_turn_count=session.turn_count,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )
