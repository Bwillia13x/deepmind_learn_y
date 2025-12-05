"""
Test configuration and fixtures.

Provides shared test fixtures for database mocking, async sessions,
and sample data generation.
"""

from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    EngagementLevel,
    OracySession,
    ScoutReport,
    SessionStatus,
    Student,
    Teacher,
)


# === Sample Data Fixtures ===


@pytest.fixture
def sample_student_code() -> str:
    """Sample student code for testing."""
    return "STU-abc123def456"


@pytest.fixture
def sample_pii_text() -> str:
    """Sample text containing PII for testing."""
    return "John Smith called at 555-123-4567 from john@email.com"


@pytest.fixture
def sample_student() -> Student:
    """Create a sample Student model instance."""
    return Student(
        id=str(uuid4()),
        student_code="STU-test123abc",
        grade=5,
        primary_language="Arabic",
        school_code="SCHOOL-001",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_teacher() -> Teacher:
    """Create a sample Teacher model instance."""
    return Teacher(
        id=str(uuid4()),
        email="teacher@school.ab.ca",
        school_code="SCHOOL-001",
        is_active=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_oracy_session(sample_student: Student) -> OracySession:
    """Create a sample OracySession model instance."""
    return OracySession(
        id=str(uuid4()),
        student_id=sample_student.id,
        started_at=datetime.utcnow() - timedelta(minutes=15),
        ended_at=datetime.utcnow(),
        status=SessionStatus.COMPLETED,
        duration_seconds=900,
        turn_count=20,
        avg_latency_ms=150.0,
        transcript="Student: Hello\nNEXUS: Hi there! How are you today?",
        curriculum_outcome="SCI-5-1: Wetland ecosystems",
    )


@pytest.fixture
def sample_scout_report(sample_oracy_session: OracySession) -> ScoutReport:
    """Create a sample ScoutReport model instance."""
    return ScoutReport(
        id=str(uuid4()),
        oracy_session_id=sample_oracy_session.id,
        engagement_level=EngagementLevel.HIGH,
        insight_text="Student showed excellent engagement discussing wetlands.",
        linguistic_observations="Good use of descriptive vocabulary.",
        cultural_bridge_notes="Connected Alberta ecosystems to home country rivers.",
        recommended_followup="Explore more environmental science topics.",
        is_reviewed=False,
        reviewed_at=None,
        created_at=datetime.utcnow(),
    )


# === Mock Database Fixtures ===


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


@pytest.fixture
def mock_db_result() -> MagicMock:
    """Create a mock database result."""
    result = MagicMock()
    result.scalars = MagicMock(return_value=MagicMock())
    result.scalar = MagicMock(return_value=None)
    result.first = MagicMock(return_value=None)
    result.all = MagicMock(return_value=[])
    return result


# === Session Context Fixtures ===


@pytest.fixture
def sample_session_context() -> dict:
    """Sample session context for voice engine testing."""
    return {
        "student_code": "STU-test123abc",
        "grade": 5,
        "primary_language": "Ukrainian",
        "curriculum_outcome": "SS-5-1: Canadian Identity",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How are you today?"},
        ],
    }


@pytest.fixture
def sample_conversation_transcript() -> str:
    """Sample conversation transcript for testing."""
    return """Student: Hello, I want to practice English today.
NEXUS: That's wonderful! I'm happy to help you practice. What would you like to talk about?
Student: I learned about wetlands in class today.
NEXUS: Wetlands are fascinating! What did you learn about them?
Student: They have lots of animals and plants. And water.
NEXUS: Yes! Wetlands are like nature's water parks. They're home to frogs, birds, and many plants. Did you know Alberta has many wetlands?
Student: No, I didn't know that.
NEXUS: It's true! The prairies have many small wetlands called sloughs. Have you ever seen one near your school?"""


# === EAL Language Fixtures ===


@pytest.fixture
def eal_languages() -> list[str]:
    """List of supported EAL languages."""
    return [
        "Arabic",
        "Mandarin",
        "Punjabi",
        "Tagalog",
        "Spanish",
        "Ukrainian",
        "Vietnamese",
        "Somali",
    ]


@pytest.fixture
def grade_levels() -> list[int]:
    """List of valid grade levels (K=0, 1-12)."""
    return list(range(0, 13))


# === Curriculum Fixtures ===


@pytest.fixture
def sample_curriculum_outcomes() -> list[dict]:
    """Sample Alberta curriculum outcomes for testing."""
    return [
        {
            "code": "SCI-5-1",
            "subject": "Science",
            "grade": 5,
            "outcome_text": "Students will describe the properties of wetland ecosystems",
        },
        {
            "code": "SS-5-1-2",
            "subject": "Social Studies",
            "grade": 5,
            "outcome_text": "Students will examine historical events in the Canadian context",
        },
        {
            "code": "MATH-5-N-3",
            "subject": "Math",
            "grade": 5,
            "outcome_text": "Students will demonstrate understanding of fractions",
        },
        {
            "code": "ELA-5-1",
            "subject": "English Language Arts",
            "grade": 5,
            "outcome_text": "Students will use oral language to express ideas",
        },
    ]


# === Analytics Fixtures ===


@pytest.fixture
def sample_analytics_data() -> dict:
    """Sample analytics data for dashboard testing."""
    return {
        "total_students": 25,
        "active_students": 18,
        "total_sessions": 45,
        "avg_duration_minutes": 12.5,
        "high_engagement_rate": 0.72,
        "reports_pending": 5,
    }


@pytest.fixture
def sample_engagement_trend() -> list[dict]:
    """Sample engagement trend data points."""
    base_date = datetime.utcnow()
    return [
        {
            "date": (base_date - timedelta(days=i)).strftime("%Y-%m-%d"),
            "high_engagement_count": 8 + i % 3,
            "medium_engagement_count": 5 + i % 2,
            "low_engagement_count": 2,
            "total_sessions": 15 + i % 4,
        }
        for i in range(7)
    ]
