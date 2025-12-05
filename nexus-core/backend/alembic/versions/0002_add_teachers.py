"""Add teachers table and auth fields

Revision ID: 0002_add_teachers
Revises: 0001_initial
Create Date: 2024-12-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002_add_teachers'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create teachers table
    op.create_table(
        'teachers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('teacher_code', sa.String(64), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('school_code', sa.String(32), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='teacher'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('teacher_code'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_teachers_teacher_code', 'teachers', ['teacher_code'])
    op.create_index('ix_teachers_email', 'teachers', ['email'])
    op.create_index('ix_teachers_school_code', 'teachers', ['school_code'])

    # Add foreign key from scout_reports to teachers
    op.create_foreign_key(
        'fk_scout_reports_teacher_id',
        'scout_reports',
        'teachers',
        ['teacher_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    # Remove foreign key first
    op.drop_constraint('fk_scout_reports_teacher_id', 'scout_reports', type_='foreignkey')
    
    # Drop teachers table
    op.drop_table('teachers')
