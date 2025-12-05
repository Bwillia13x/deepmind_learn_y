"""Initial migration - Create core tables

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create students table
    op.create_table(
        'students',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('student_code', sa.String(50), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('primary_language', sa.String(50), nullable=True, server_default='English'),
        sa.Column('school_code', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_code'),
    )
    op.create_index('ix_students_student_code', 'students', ['student_code'])
    op.create_index('ix_students_grade', 'students', ['grade'])

    # Create oracy_sessions table
    op.create_table(
        'oracy_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('turn_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('transcript_summary', sa.Text(), nullable=True),
        sa.Column('curriculum_outcome_ids', sa.Text(), nullable=True),
        sa.Column('avg_response_latency_ms', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_oracy_sessions_student_id', 'oracy_sessions', ['student_id'])
    op.create_index('ix_oracy_sessions_status', 'oracy_sessions', ['status'])
    op.create_index('ix_oracy_sessions_started_at', 'oracy_sessions', ['started_at'])

    # Create scout_reports table
    op.create_table(
        'scout_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('oracy_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('engagement_level', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('insight_text', sa.Text(), nullable=False),
        sa.Column('linguistic_observations', sa.Text(), nullable=True),
        sa.Column('curriculum_connections', sa.Text(), nullable=True),
        sa.Column('recommended_next_steps', sa.Text(), nullable=True),
        sa.Column('is_reviewed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('teacher_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['oracy_session_id'], ['oracy_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scout_reports_oracy_session_id', 'scout_reports', ['oracy_session_id'])
    op.create_index('ix_scout_reports_is_reviewed', 'scout_reports', ['is_reviewed'])

    # Create curriculum_outcomes table
    op.create_table(
        'curriculum_outcomes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('outcome_code', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(100), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('strand', sa.String(100), nullable=True),
        sa.Column('outcome_text', sa.Text(), nullable=False),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('cultural_bridge_hints', sa.Text(), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('outcome_code'),
    )
    op.create_index('ix_curriculum_outcomes_grade', 'curriculum_outcomes', ['grade'])
    op.create_index('ix_curriculum_outcomes_subject', 'curriculum_outcomes', ['subject'])

    # Create outcome_links table (junction table)
    op.create_table(
        'outcome_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('oracy_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('curriculum_outcome_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['oracy_session_id'], ['oracy_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['curriculum_outcome_id'], ['curriculum_outcomes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_links_session', 'outcome_links', ['oracy_session_id'])
    op.create_index('ix_outcome_links_outcome', 'outcome_links', ['curriculum_outcome_id'])


def downgrade() -> None:
    op.drop_table('outcome_links')
    op.drop_table('curriculum_outcomes')
    op.drop_table('scout_reports')
    op.drop_table('oracy_sessions')
    op.drop_table('students')
