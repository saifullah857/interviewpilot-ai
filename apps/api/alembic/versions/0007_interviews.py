"""interviews

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-23 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('interview_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('resume_id', sa.Uuid(), nullable=True),
    sa.Column('resume_version_id', sa.Uuid(), nullable=True),
    sa.Column('company_id', sa.Uuid(), nullable=True),
    sa.Column('role_slug', sa.String(length=80), nullable=False),
    sa.Column('mode', sa.String(length=8), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('input_mode', sa.String(length=8), nullable=False),
    sa.Column('question_target', sa.Integer(), nullable=False),
    sa.Column('plan', sa.JSON(), nullable=False),
    sa.Column('evidence', sa.JSON(), nullable=False),
    sa.Column('consent_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('save_transcript', sa.Boolean(), nullable=False),
    sa.Column('transcript_purged_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('events', sa.JSON(), nullable=False),
    sa.Column('evaluation', sa.JSON(), nullable=True),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('model', sa.String(length=80), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("input_mode in ('voice','text')", name=op.f('ck_interview_sessions_input_mode_valid')),
    sa.CheckConstraint("mode in ('general','company')", name=op.f('ck_interview_sessions_mode_valid')),
    sa.CheckConstraint("status in ('active','completed','interrupted')", name=op.f('ck_interview_sessions_status_valid')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_interview_sessions_company_id_companies'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], name=op.f('fk_interview_sessions_resume_id_resumes'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['resume_version_id'], ['resume_versions.id'], name=op.f('fk_interview_sessions_resume_version_id_resume_versions'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_interview_sessions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_sessions'))
    )
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_sessions_user_id'), ['user_id'], unique=False)

    op.create_table('interview_turns',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('speaker', sa.String(length=12), nullable=False),
    sa.Column('kind', sa.String(length=10), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('topic', sa.String(length=60), nullable=True),
    sa.Column('slot', sa.Integer(), nullable=True),
    sa.Column('source', sa.String(length=10), nullable=False),
    sa.Column('informed_by', sa.JSON(), nullable=False),
    sa.Column('flags', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("kind in ('opening','question','follow_up','answer','skipped','closing')", name=op.f('ck_interview_turns_kind_valid')),
    sa.CheckConstraint("speaker in ('interviewer','candidate')", name=op.f('ck_interview_turns_speaker_valid')),
    sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], name=op.f('fk_interview_turns_session_id_interview_sessions'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_interview_turns_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_turns')),
    sa.UniqueConstraint('session_id', 'position', name=op.f('uq_interview_turns_session_id'))
    )
    with op.batch_alter_table('interview_turns', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_turns_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_turns_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('interview_turns', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_turns_user_id'))
        batch_op.drop_index(batch_op.f('ix_interview_turns_session_id'))

    op.drop_table('interview_turns')
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_sessions_user_id'))

    op.drop_table('interview_sessions')
