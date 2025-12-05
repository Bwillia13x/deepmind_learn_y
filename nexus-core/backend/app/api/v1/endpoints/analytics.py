"""
Analytics API endpoints.

Provides cohort-level insights for teachers:
- Class-wide engagement trends
- Struggling students alerts
- Curriculum coverage heatmaps
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import (
    CurriculumOutcome,
    EngagementLevel,
    OracySession,
    ScoutReport,
    SessionStatus,
    Student,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# === Pydantic Schemas ===


class EngagementTrendPoint(BaseModel):
    """Single data point in engagement trend."""

    date: str  # YYYY-MM-DD format
    high_engagement_count: int
    medium_engagement_count: int
    low_engagement_count: int
    total_sessions: int
    avg_duration_minutes: float


class EngagementTrendResponse(BaseModel):
    """Engagement trends over time."""

    period_start: datetime
    period_end: datetime
    trend_data: list[EngagementTrendPoint]
    overall_high_percentage: float
    overall_medium_percentage: float
    overall_low_percentage: float


class StrugglingStudentAlert(BaseModel):
    """Alert for students showing low engagement patterns."""

    student_code: str
    grade: int
    primary_language: str
    consecutive_low_engagement_days: int
    last_session_date: datetime | None
    avg_session_duration_minutes: float
    recommended_action: str


class StrugglingStudentsResponse(BaseModel):
    """List of students needing attention."""

    alerts: list[StrugglingStudentAlert]
    total_struggling: int
    threshold_days: int


class CurriculumCoverageItem(BaseModel):
    """Coverage data for a single curriculum outcome."""

    outcome_id: str
    outcome_code: str
    outcome_description: str
    subject: str
    grade: int
    session_count: int
    unique_students: int
    avg_engagement_score: float  # 0-1 scale (LOW=0, MED=0.5, HIGH=1)


class CurriculumCoverageResponse(BaseModel):
    """Curriculum coverage heatmap data."""

    outcomes: list[CurriculumCoverageItem]
    total_outcomes_covered: int
    total_outcomes_available: int
    coverage_percentage: float
    most_practiced_subject: str | None
    least_practiced_subject: str | None


class ClassOverviewStats(BaseModel):
    """Quick stats for class overview."""

    total_students: int
    active_students_this_week: int
    total_sessions_this_week: int
    avg_session_duration_minutes: float
    total_practice_minutes_this_week: float
    high_engagement_rate: float
    reports_pending_review: int


class AnalyticsSummaryResponse(BaseModel):
    """Complete analytics summary for teacher dashboard."""

    overview: ClassOverviewStats
    engagement_trend: EngagementTrendResponse
    struggling_students: StrugglingStudentsResponse
    curriculum_coverage: CurriculumCoverageResponse


# === Helper Functions ===


def calculate_engagement_score(level: EngagementLevel) -> float:
    """Convert engagement level to numeric score."""
    return {
        EngagementLevel.LOW: 0.0,
        EngagementLevel.MEDIUM: 0.5,
        EngagementLevel.HIGH: 1.0,
    }.get(level, 0.5)


# === Endpoints ===


@router.get("/overview", response_model=ClassOverviewStats)
async def get_class_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    school_code: str | None = Query(None, description="Filter by school code"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
) -> ClassOverviewStats:
    """
    Get quick overview stats for the class.

    Returns key metrics for teacher dashboard header.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Base query for students
    student_query = select(Student)
    if school_code:
        student_query = student_query.where(Student.school_code == school_code)

    # Total students
    total_students_result = await db.execute(
        select(func.count(Student.id)).select_from(student_query.subquery())
    )
    total_students = total_students_result.scalar() or 0

    # Sessions in period
    session_query = (
        select(OracySession)
        .where(OracySession.started_at >= cutoff_date)
        .where(OracySession.status == SessionStatus.COMPLETED)
    )
    if school_code:
        session_query = session_query.join(Student).where(Student.school_code == school_code)

    # Active students this week
    active_students_result = await db.execute(
        select(func.count(distinct(OracySession.student_id))).where(
            OracySession.started_at >= cutoff_date
        )
    )
    active_students = active_students_result.scalar() or 0

    # Session stats
    session_stats_result = await db.execute(
        select(
            func.count(OracySession.id).label("total_sessions"),
            func.avg(OracySession.duration_seconds).label("avg_duration"),
            func.sum(OracySession.duration_seconds).label("total_duration"),
        ).where(
            OracySession.started_at >= cutoff_date,
            OracySession.status == SessionStatus.COMPLETED,
        )
    )
    session_stats = session_stats_result.first()

    total_sessions = session_stats.total_sessions if session_stats else 0
    avg_duration = (session_stats.avg_duration or 0) / 60 if session_stats else 0
    total_duration = (session_stats.total_duration or 0) / 60 if session_stats else 0

    # High engagement rate
    engagement_result = await db.execute(
        select(
            func.count(ScoutReport.id).label("total"),
            func.sum(
                case((ScoutReport.engagement_level == EngagementLevel.HIGH, 1), else_=0)
            ).label("high_count"),
        )
        .join(OracySession)
        .where(OracySession.started_at >= cutoff_date)
    )
    engagement_stats = engagement_result.first()
    high_rate = 0.0
    if engagement_stats and engagement_stats.total:
        high_rate = (engagement_stats.high_count or 0) / engagement_stats.total

    # Pending reviews
    pending_result = await db.execute(
        select(func.count(ScoutReport.id)).where(ScoutReport.is_reviewed == False)  # noqa: E712
    )
    pending_reviews = pending_result.scalar() or 0

    return ClassOverviewStats(
        total_students=total_students,
        active_students_this_week=active_students,
        total_sessions_this_week=total_sessions,
        avg_session_duration_minutes=round(avg_duration, 1),
        total_practice_minutes_this_week=round(total_duration, 1),
        high_engagement_rate=round(high_rate, 2),
        reports_pending_review=pending_reviews,
    )


@router.get("/engagement-trend", response_model=EngagementTrendResponse)
async def get_engagement_trend(
    db: Annotated[AsyncSession, Depends(get_db)],
    school_code: str | None = Query(None, description="Filter by school code"),
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
) -> EngagementTrendResponse:
    """
    Get engagement trends over time.

    Returns daily breakdown of engagement levels for charting.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    now = datetime.utcnow()

    # Query sessions with engagement data
    query = (
        select(
            func.date(OracySession.started_at).label("session_date"),
            ScoutReport.engagement_level,
            func.count(OracySession.id).label("session_count"),
            func.avg(OracySession.duration_seconds).label("avg_duration"),
        )
        .join(ScoutReport, OracySession.id == ScoutReport.oracy_session_id)
        .where(
            OracySession.started_at >= cutoff_date,
            OracySession.status == SessionStatus.COMPLETED,
        )
        .group_by(func.date(OracySession.started_at), ScoutReport.engagement_level)
        .order_by(func.date(OracySession.started_at))
    )

    if school_code:
        query = query.join(Student).where(Student.school_code == school_code)

    result = await db.execute(query)
    rows = result.all()

    # Process into daily data points
    daily_data: dict[str, EngagementTrendPoint] = {}

    for row in rows:
        date_str = row.session_date.strftime("%Y-%m-%d")
        if date_str not in daily_data:
            daily_data[date_str] = EngagementTrendPoint(
                date=date_str,
                high_engagement_count=0,
                medium_engagement_count=0,
                low_engagement_count=0,
                total_sessions=0,
                avg_duration_minutes=0,
            )

        point = daily_data[date_str]
        point.total_sessions += row.session_count
        point.avg_duration_minutes = (row.avg_duration or 0) / 60

        if row.engagement_level == EngagementLevel.HIGH:
            point.high_engagement_count = row.session_count
        elif row.engagement_level == EngagementLevel.MEDIUM:
            point.medium_engagement_count = row.session_count
        elif row.engagement_level == EngagementLevel.LOW:
            point.low_engagement_count = row.session_count

    # Calculate overall percentages
    total = sum(p.total_sessions for p in daily_data.values())
    total_high = sum(p.high_engagement_count for p in daily_data.values())
    total_med = sum(p.medium_engagement_count for p in daily_data.values())
    total_low = sum(p.low_engagement_count for p in daily_data.values())

    return EngagementTrendResponse(
        period_start=cutoff_date,
        period_end=now,
        trend_data=sorted(daily_data.values(), key=lambda x: x.date),
        overall_high_percentage=round(total_high / total * 100, 1) if total else 0,
        overall_medium_percentage=round(total_med / total * 100, 1) if total else 0,
        overall_low_percentage=round(total_low / total * 100, 1) if total else 0,
    )


@router.get("/struggling-students", response_model=StrugglingStudentsResponse)
async def get_struggling_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    school_code: str | None = Query(None, description="Filter by school code"),
    threshold_days: int = Query(3, ge=2, le=7, description="Days of low engagement to trigger alert"),
) -> StrugglingStudentsResponse:
    """
    Identify students showing patterns of low engagement.

    Returns students with 3+ consecutive days of low engagement,
    allowing teachers to intervene early.
    """
    alerts: list[StrugglingStudentAlert] = []

    # Get students with their recent sessions
    student_query = select(Student)
    if school_code:
        student_query = student_query.where(Student.school_code == school_code)

    students_result = await db.execute(student_query)
    students = students_result.scalars().all()

    cutoff_date = datetime.utcnow() - timedelta(days=14)

    for student in students:
        # Get recent sessions with engagement data
        session_query = (
            select(
                OracySession.started_at,
                OracySession.duration_seconds,
                ScoutReport.engagement_level,
            )
            .join(ScoutReport, OracySession.id == ScoutReport.oracy_session_id)
            .where(
                OracySession.student_id == student.id,
                OracySession.started_at >= cutoff_date,
                OracySession.status == SessionStatus.COMPLETED,
            )
            .order_by(OracySession.started_at.desc())
        )
        sessions_result = await db.execute(session_query)
        sessions = sessions_result.all()

        if not sessions:
            continue

        # Count consecutive low engagement days
        consecutive_low = 0
        last_date = None

        for session in sessions:
            session_date = session.started_at.date()

            # Skip if same day as last
            if last_date == session_date:
                continue

            if session.engagement_level == EngagementLevel.LOW:
                consecutive_low += 1
                last_date = session_date
            else:
                break  # Streak broken

        if consecutive_low >= threshold_days:
            # Calculate avg duration
            total_duration = sum(s.duration_seconds or 0 for s in sessions)
            avg_duration = (total_duration / len(sessions) / 60) if sessions else 0

            # Generate recommended action
            if consecutive_low >= 5:
                action = "Urgent: Schedule 1:1 check-in with student"
            elif student.primary_language != "English":
                action = f"Consider cultural bridge activities in {student.primary_language}"
            else:
                action = "Review recent Scout Reports for specific challenges"

            alerts.append(
                StrugglingStudentAlert(
                    student_code=student.student_code,
                    grade=student.grade,
                    primary_language=student.primary_language,
                    consecutive_low_engagement_days=consecutive_low,
                    last_session_date=sessions[0].started_at if sessions else None,
                    avg_session_duration_minutes=round(avg_duration, 1),
                    recommended_action=action,
                )
            )

    # Sort by severity (most consecutive days first)
    alerts.sort(key=lambda x: x.consecutive_low_engagement_days, reverse=True)

    return StrugglingStudentsResponse(
        alerts=alerts,
        total_struggling=len(alerts),
        threshold_days=threshold_days,
    )


@router.get("/curriculum-coverage", response_model=CurriculumCoverageResponse)
async def get_curriculum_coverage(
    db: Annotated[AsyncSession, Depends(get_db)],
    school_code: str | None = Query(None, description="Filter by school code"),
    grade: int | None = Query(None, ge=0, le=12, description="Filter by grade"),
    subject: str | None = Query(None, description="Filter by subject"),
    days: int = Query(30, ge=7, le=365, description="Analysis period in days"),
) -> CurriculumCoverageResponse:
    """
    Get curriculum outcome coverage data for heatmap visualization.

    Shows which Alberta Program of Studies outcomes are being practiced
    and which need more attention.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get all available curriculum outcomes
    outcomes_query = select(CurriculumOutcome)
    if grade is not None:
        outcomes_query = outcomes_query.where(CurriculumOutcome.grade == grade)
    if subject:
        outcomes_query = outcomes_query.where(CurriculumOutcome.subject == subject)

    outcomes_result = await db.execute(outcomes_query)
    all_outcomes = outcomes_result.scalars().all()

    # Get coverage data from sessions
    coverage_items: list[CurriculumCoverageItem] = []
    subjects_coverage: dict[str, int] = {}

    for outcome in all_outcomes:
        # Count sessions covering this outcome
        session_query = (
            select(
                func.count(OracySession.id).label("session_count"),
                func.count(distinct(OracySession.student_id)).label("unique_students"),
            )
            .join(ScoutReport, OracySession.id == ScoutReport.oracy_session_id)
            .where(
                OracySession.started_at >= cutoff_date,
                OracySession.status == SessionStatus.COMPLETED,
                OracySession.curriculum_outcome_ids.contains(outcome.id),
            )
        )

        if school_code:
            session_query = session_query.join(Student).where(Student.school_code == school_code)

        result = await db.execute(session_query)
        stats = result.first()

        session_count = stats.session_count if stats else 0
        unique_students = stats.unique_students if stats else 0

        # Get average engagement for this outcome
        engagement_query = (
            select(func.avg(
                case(
                    (ScoutReport.engagement_level == EngagementLevel.HIGH, 1.0),
                    (ScoutReport.engagement_level == EngagementLevel.MEDIUM, 0.5),
                    else_=0.0,
                )
            ))
            .join(OracySession, ScoutReport.oracy_session_id == OracySession.id)
            .where(
                OracySession.started_at >= cutoff_date,
                OracySession.curriculum_outcome_ids.contains(outcome.id),
            )
        )
        engagement_result = await db.execute(engagement_query)
        avg_engagement = engagement_result.scalar() or 0

        coverage_items.append(
            CurriculumCoverageItem(
                outcome_id=outcome.id,
                outcome_code=outcome.outcome_code,
                outcome_description=outcome.outcome_text,
                subject=outcome.subject,
                grade=outcome.grade,
                session_count=session_count,
                unique_students=unique_students,
                avg_engagement_score=round(avg_engagement, 2),
            )
        )

        # Track subject totals
        subjects_coverage[outcome.subject] = subjects_coverage.get(outcome.subject, 0) + session_count

    # Calculate coverage stats
    covered_outcomes = sum(1 for item in coverage_items if item.session_count > 0)
    total_outcomes = len(coverage_items)
    coverage_pct = (covered_outcomes / total_outcomes * 100) if total_outcomes else 0

    # Find most/least practiced subjects
    most_practiced = max(subjects_coverage.keys(), key=lambda k: subjects_coverage[k]) if subjects_coverage else None
    least_practiced = min(subjects_coverage.keys(), key=lambda k: subjects_coverage[k]) if subjects_coverage else None

    return CurriculumCoverageResponse(
        outcomes=coverage_items,
        total_outcomes_covered=covered_outcomes,
        total_outcomes_available=total_outcomes,
        coverage_percentage=round(coverage_pct, 1),
        most_practiced_subject=most_practiced,
        least_practiced_subject=least_practiced,
    )


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    school_code: str | None = Query(None, description="Filter by school code"),
) -> AnalyticsSummaryResponse:
    """
    Get complete analytics summary for teacher dashboard.

    Combines all analytics data into a single response for efficient loading.
    """
    # Call individual endpoints
    overview = await get_class_overview(db, school_code)
    engagement = await get_engagement_trend(db, school_code)
    struggling = await get_struggling_students(db, school_code)
    curriculum = await get_curriculum_coverage(db, school_code)

    return AnalyticsSummaryResponse(
        overview=overview,
        engagement_trend=engagement,
        struggling_students=struggling,
        curriculum_coverage=curriculum,
    )
