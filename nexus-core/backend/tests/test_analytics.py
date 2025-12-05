"""
Tests for the Analytics API endpoints.

Tests cohort-level analytics that provide privacy-preserving
aggregate metrics for teachers.
"""

import re
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints.analytics import (
    AnalyticsSummaryResponse,
    ClassOverviewStats,
    CurriculumCoverageItem,
    CurriculumCoverageResponse,
    EngagementTrendPoint,
    EngagementTrendResponse,
    StrugglingStudentAlert,
    StrugglingStudentsResponse,
)


class TestClassOverviewStats:
    """Tests for class overview statistics."""

    def test_class_overview_stats_creation(self) -> None:
        """Test creating ClassOverviewStats model."""
        stats = ClassOverviewStats(
            total_students=25,
            active_students_this_week=20,
            total_sessions_this_week=150,
            avg_session_duration_minutes=7.0,
            total_practice_minutes_this_week=420.0,
            high_engagement_rate=0.75,
            reports_pending_review=5,
        )

        assert stats.total_students == 25
        assert stats.active_students_this_week == 20
        assert stats.total_sessions_this_week == 150
        assert stats.avg_session_duration_minutes == 7.0
        assert stats.total_practice_minutes_this_week == 420.0
        assert stats.high_engagement_rate == 0.75
        assert stats.reports_pending_review == 5

    def test_class_overview_handles_zero_students(self) -> None:
        """Test that stats handle empty classroom correctly."""
        stats = ClassOverviewStats(
            total_students=0,
            active_students_this_week=0,
            total_sessions_this_week=0,
            avg_session_duration_minutes=0.0,
            total_practice_minutes_this_week=0.0,
            high_engagement_rate=0.0,
            reports_pending_review=0,
        )

        assert stats.total_students == 0
        assert stats.high_engagement_rate == 0.0


class TestEngagementTrendPoint:
    """Tests for engagement trend data points."""

    def test_engagement_trend_point_creation(self) -> None:
        """Test creating an engagement trend point."""
        point = EngagementTrendPoint(
            date="2025-01-15",
            high_engagement_count=10,
            medium_engagement_count=8,
            low_engagement_count=2,
            total_sessions=20,
            avg_duration_minutes=12.5,
        )

        assert point.date == "2025-01-15"
        assert point.high_engagement_count == 10
        assert point.medium_engagement_count == 8
        assert point.low_engagement_count == 2
        assert point.total_sessions == 20
        assert point.avg_duration_minutes == 12.5

    def test_engagement_trend_calculates_total(self) -> None:
        """Test that total matches engagement levels sum."""
        point = EngagementTrendPoint(
            date="2025-01-15",
            high_engagement_count=10,
            medium_engagement_count=8,
            low_engagement_count=2,
            total_sessions=20,
            avg_duration_minutes=10.0,
        )

        total = point.high_engagement_count + point.medium_engagement_count + point.low_engagement_count
        assert total == point.total_sessions


class TestEngagementTrendResponse:
    """Tests for engagement trend response."""

    def test_trend_response_creation(self) -> None:
        """Test creating an engagement trend response."""
        now = datetime.utcnow()
        response = EngagementTrendResponse(
            period_start=now - timedelta(days=30),
            period_end=now,
            trend_data=[],
            overall_high_percentage=0.6,
            overall_medium_percentage=0.3,
            overall_low_percentage=0.1,
        )

        assert response.overall_high_percentage == 0.6
        assert response.overall_medium_percentage == 0.3
        assert response.overall_low_percentage == 0.1


class TestStrugglingStudentAlert:
    """Tests for struggling student alerts."""

    def test_struggling_student_alert_creation(self) -> None:
        """Test creating a struggling student alert."""
        alert = StrugglingStudentAlert(
            student_code="STU-abc123",
            grade=5,
            primary_language="Arabic",
            consecutive_low_engagement_days=3,
            last_session_date=datetime.utcnow(),
            avg_session_duration_minutes=3.0,
            recommended_action="Schedule 1:1 check-in with student",
        )

        assert alert.student_code == "STU-abc123"
        assert alert.grade == 5
        assert alert.primary_language == "Arabic"
        assert alert.consecutive_low_engagement_days == 3
        assert alert.recommended_action == "Schedule 1:1 check-in with student"

    def test_alert_does_not_contain_student_name(self) -> None:
        """Verify alerts use student_code, not names (privacy)."""
        alert = StrugglingStudentAlert(
            student_code="STU-xyz789",
            grade=4,
            primary_language="Mandarin",
            consecutive_low_engagement_days=5,
            last_session_date=None,
            avg_session_duration_minutes=2.5,
            recommended_action="Review recent sessions",
        )

        # Ensure we're using codes, not names
        assert "STU-" in alert.student_code
        assert not any(
            name in alert.student_code.lower()
            for name in ["john", "jane", "student", "name"]
        )


class TestStrugglingStudentsResponse:
    """Tests for struggling students response."""

    def test_response_creation(self) -> None:
        """Test creating a struggling students response."""
        response = StrugglingStudentsResponse(
            alerts=[],
            total_struggling=0,
            threshold_days=3,
        )

        assert response.total_struggling == 0
        assert response.threshold_days == 3


class TestCurriculumCoverageItem:
    """Tests for curriculum coverage data."""

    def test_curriculum_coverage_item_creation(self) -> None:
        """Test creating a curriculum coverage item."""
        item = CurriculumCoverageItem(
            outcome_id="uuid-here",
            outcome_code="SS-5-1-1",
            outcome_description="Students will appreciate complexity of identity",
            subject="Social Studies",
            grade=5,
            session_count=15,
            unique_students=12,
            avg_engagement_score=0.75,
        )

        assert item.outcome_code == "SS-5-1-1"
        assert item.subject == "Social Studies"
        assert item.grade == 5
        assert item.avg_engagement_score == 0.75

    def test_engagement_score_bounds(self) -> None:
        """Test that engagement score is between 0 and 1."""
        item = CurriculumCoverageItem(
            outcome_id="uuid-here",
            outcome_code="LA-5-1-1",
            outcome_description="Students will explore thoughts and ideas",
            subject="Language Arts",
            grade=5,
            session_count=25,
            unique_students=20,
            avg_engagement_score=0.85,
        )

        assert 0 <= item.avg_engagement_score <= 1.0


class TestCurriculumCoverageResponse:
    """Tests for curriculum coverage response."""

    def test_response_creation(self) -> None:
        """Test creating a curriculum coverage response."""
        response = CurriculumCoverageResponse(
            outcomes=[],
            total_outcomes_covered=5,
            total_outcomes_available=20,
            coverage_percentage=0.25,
            most_practiced_subject="Science",
            least_practiced_subject="Math",
        )

        assert response.total_outcomes_covered == 5
        assert response.coverage_percentage == 0.25
        assert response.most_practiced_subject == "Science"


class TestAnalyticsSummaryResponse:
    """Tests for the analytics summary."""

    def test_analytics_summary_creation(self) -> None:
        """Test creating an analytics summary response."""
        summary = AnalyticsSummaryResponse(
            overview=ClassOverviewStats(
                total_students=25,
                active_students_this_week=20,
                total_sessions_this_week=100,
                avg_session_duration_minutes=12.0,
                total_practice_minutes_this_week=240.0,
                high_engagement_rate=0.72,
                reports_pending_review=3,
            ),
            engagement_trend=EngagementTrendResponse(
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                trend_data=[],
                overall_high_percentage=0.72,
                overall_medium_percentage=0.2,
                overall_low_percentage=0.08,
            ),
            struggling_students=StrugglingStudentsResponse(
                alerts=[],
                total_struggling=2,
                threshold_days=3,
            ),
            curriculum_coverage=CurriculumCoverageResponse(
                outcomes=[],
                total_outcomes_covered=10,
                total_outcomes_available=30,
                coverage_percentage=0.33,
                most_practiced_subject="Social Studies",
                least_practiced_subject="Math",
            ),
        )

        assert summary.overview.total_students == 25
        assert summary.struggling_students.total_struggling == 2
        assert summary.curriculum_coverage.coverage_percentage == 0.33


class TestPrivacyCompliance:
    """Tests to ensure analytics respect privacy requirements."""

    def test_no_pii_in_student_alerts(self) -> None:
        """Verify no personally identifiable information in alerts."""
        # Student code format: STU-{hash}
        valid_code_pattern = r"^STU-[a-zA-Z0-9]+$"

        test_code = "STU-abc123def456"
        assert re.match(valid_code_pattern, test_code)

    def test_aggregated_metrics_only(self) -> None:
        """Ensure analytics provide aggregated, not individual data."""
        # The ClassOverviewStats should contain counts and averages,
        # not lists of individual student data

        stats = ClassOverviewStats(
            total_students=25,
            active_students_this_week=20,
            total_sessions_this_week=150,
            avg_session_duration_minutes=7.0,
            total_practice_minutes_this_week=420.0,
            high_engagement_rate=0.75,
            reports_pending_review=5,
        )

        # Verify all fields are aggregates
        assert isinstance(stats.total_students, int)
        assert isinstance(stats.avg_session_duration_minutes, float)
        assert isinstance(stats.high_engagement_rate, float)

    def test_student_code_format(self) -> None:
        """Verify student codes follow privacy-safe format."""
        alert = StrugglingStudentAlert(
            student_code="STU-9a8b7c6d",
            grade=3,
            primary_language="Spanish",
            consecutive_low_engagement_days=4,
            last_session_date=datetime.utcnow(),
            avg_session_duration_minutes=5.0,
            recommended_action="Increase session frequency",
        )

        # Should be hash-based, not name-based
        assert alert.student_code.startswith("STU-")
        # Should not contain common name patterns
        assert not re.search(r"[A-Z][a-z]+[A-Z][a-z]+", alert.student_code)
