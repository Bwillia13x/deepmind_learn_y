"""
NEXUS Database Models.

Domain models based on .context/01_domain_glossary.md terminology.
Uses SQLAlchemy 2.0 declarative style with proper type annotations.

CRITICAL: We NEVER store student names. Only student_code (hashed identifier).
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    pass


class EngagementLevel(enum.Enum):
    """Engagement level observed during an oracy session."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SessionStatus(enum.Enum):
    """Status of an oracy session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class UserRole(enum.Enum):
    """User roles in the NEXUS system."""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class Student(Base):
    """
    Student record for NEXUS.

    PRIVACY NOTICE: NO name field exists by design (see .context/02_privacy_charter.md).
    The student_code is a hashed, non-identifying code. Mapping to real identity
    is maintained ONLY in the school's existing Student Information System (SIS).
    """

    __tablename__ = "students"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    student_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="Hashed student identifier (e.g., STU-abc123). NO real names.",
    )
    grade: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Grade level (K=0, 1-12)",
    )
    primary_language: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="English",
        comment="Student's primary/home language for cultural bridging",
    )
    school_code: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="School identifier for multi-tenant isolation",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    oracy_sessions: Mapped[list["OracySession"]] = relationship(
        "OracySession",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Student(code={self.student_code}, grade={self.grade})>"


class Teacher(Base):
    """
    Teacher record for NEXUS.

    Teachers have access to Scout Reports and can view student progress.
    """

    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    teacher_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="Teacher identifier code",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Teacher email for authentication",
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Bcrypt password hash for authentication",
    )
    school_code: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="School identifier for multi-tenant isolation",
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.TEACHER,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    scout_reports: Mapped[list["ScoutReport"]] = relationship(
        "ScoutReport",
        back_populates="teacher",
    )

    def __repr__(self) -> str:
        return f"<Teacher(code={self.teacher_code})>"


class OracySession(Base):
    """
    Record of a voice-interactive tutoring session.

    An Oracy Session is the core interaction unit between NEXUS and a student.
    Audio is NEVER stored (per .context/02_privacy_charter.md) - only the
    anonymized transcript summary is retained.
    """

    __tablename__ = "oracy_sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session metadata
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        nullable=False,
        default=SessionStatus.ACTIVE,
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total session duration in seconds",
    )
    turn_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of conversation turns",
    )

    # Content (PII-scrubbed before storage)
    transcript_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Summarized, PII-scrubbed transcript of the session",
    )
    curriculum_outcome_ids: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated curriculum outcome IDs covered in session",
    )

    # Quality metrics
    avg_response_latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Average AI response latency in milliseconds",
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="oracy_sessions",
    )
    scout_report: Mapped["ScoutReport | None"] = relationship(
        "ScoutReport",
        back_populates="oracy_session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<OracySession(id={self.id[:8]}..., status={self.status.value})>"


class ScoutReport(Base):
    """
    Qualitative insight summary generated for teachers after an Oracy Session.

    This is NOT a grade - it is a draft observation to reduce teacher admin burden.
    The teacher retains 100% authority over final assessments.
    """

    __tablename__ = "scout_reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    oracy_session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("oracy_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    teacher_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Teacher who reviewed/owns this report",
    )

    # Core insight fields
    engagement_level: Mapped[EngagementLevel] = mapped_column(
        Enum(EngagementLevel),
        nullable=False,
        default=EngagementLevel.MEDIUM,
    )
    insight_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The generated insight summary for the teacher",
    )
    linguistic_observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Specific language patterns observed (pronunciation, grammar)",
    )
    curriculum_connections: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Which curriculum outcomes were demonstrated",
    )
    recommended_next_steps: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Suggested follow-up activities or focus areas",
    )

    # Status
    is_reviewed: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether teacher has reviewed this report",
    )
    teacher_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes added by teacher",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    oracy_session: Mapped["OracySession"] = relationship(
        "OracySession",
        back_populates="scout_report",
    )
    teacher: Mapped["Teacher | None"] = relationship(
        "Teacher",
        back_populates="scout_reports",
    )

    def __repr__(self) -> str:
        return f"<ScoutReport(id={self.id[:8]}..., engagement={self.engagement_level.value})>"


class CurriculumOutcome(Base):
    """
    Alberta Program of Studies curriculum outcome.

    Used for RAG-based cultural bridging and tracking which outcomes
    are covered in oracy sessions.
    """

    __tablename__ = "curriculum_outcomes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    outcome_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique outcome identifier (e.g., SS-5-1-2)",
    )
    subject: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    grade: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    strand: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    outcome_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full text of the curriculum outcome",
    )
    keywords: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated keywords for search",
    )
    cultural_bridge_hints: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Hints for creating cultural analogies",
    )

    # Vector embedding (stored as JSON string for simplicity; use pgvector in production)
    embedding: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-serialized embedding vector",
    )

    def __repr__(self) -> str:
        return f"<CurriculumOutcome(code={self.outcome_code})>"
