"""online screening sessions

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-07 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'screening_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('company_slug', sa.String(length=80), nullable=True),
        sa.Column('role_slug', sa.String(length=80), nullable=False),
        sa.Column('level', sa.String(length=8), nullable=False),
        sa.Column('question_slugs', sa.JSON(), nullable=False),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=12), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_submitted', sa.Boolean(), nullable=False),
        sa.Column('correct', sa.Integer(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status in ('in_progress','submitted')", name='ck_screening_sessions_status_valid'),
    )
    op.create_index('ix_screening_sessions_user_id', 'screening_sessions', ['user_id'])
    op.create_index('ix_screening_sessions_status', 'screening_sessions', ['status'])


def downgrade() -> None:
    op.drop_table('screening_sessions')
