"""reports

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-24 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('reports',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('role_slug', sa.String(length=80), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=True),
    sa.Column('mode', sa.String(length=8), nullable=False),
    sa.Column('resume_id', sa.Uuid(), nullable=True),
    sa.Column('assessment_id', sa.Uuid(), nullable=True),
    sa.Column('coding_session_id', sa.Uuid(), nullable=True),
    sa.Column('interview_id', sa.Uuid(), nullable=True),
    sa.Column('horizon', sa.Integer(), nullable=False),
    sa.Column('rubric_version', sa.String(length=20), nullable=False),
    sa.Column('rubric', sa.JSON(), nullable=False),
    sa.Column('components', sa.JSON(), nullable=False),
    sa.Column('overall', sa.JSON(), nullable=False),
    sa.Column('gaps', sa.JSON(), nullable=False),
    sa.Column('strengths', sa.JSON(), nullable=False),
    sa.Column('practice_questions', sa.JSON(), nullable=False),
    sa.Column('sources', sa.JSON(), nullable=False),
    sa.Column('roadmap', sa.JSON(), nullable=False),
    sa.Column('notes', sa.JSON(), nullable=False),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('model', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('horizon in (7,30)', name=op.f('ck_reports_horizon_valid')),
    sa.CheckConstraint("mode in ('general','company')", name=op.f('ck_reports_mode_valid')),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], name=op.f('fk_reports_assessment_id_assessments'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['coding_session_id'], ['coding_sessions.id'], name=op.f('fk_reports_coding_session_id_coding_sessions'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_reports_company_id_companies'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['interview_id'], ['interview_sessions.id'], name=op.f('fk_reports_interview_id_interview_sessions'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], name=op.f('fk_reports_resume_id_resumes'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reports_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reports'))
    )
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reports_role_slug'), ['role_slug'], unique=False)
        batch_op.create_index(batch_op.f('ix_reports_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reports_user_id'))
        batch_op.drop_index(batch_op.f('ix_reports_role_slug'))

    op.drop_table('reports')
