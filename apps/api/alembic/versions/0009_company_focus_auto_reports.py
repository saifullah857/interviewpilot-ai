"""company focus coding, resume language, auto reports

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-04 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('coding_problems') as b:
        b.add_column(sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'))
        b.add_column(sa.Column('ds', sa.JSON(), nullable=False, server_default='[]'))
    with op.batch_alter_table('coding_sessions') as b:
        b.add_column(sa.Column('company_slug', sa.String(length=80), nullable=True))
        b.add_column(sa.Column('resume_id', sa.Uuid(), nullable=True))
        b.add_column(sa.Column('language', sa.String(length=12), nullable=False, server_default='python'))
        b.add_column(sa.Column('plan', sa.JSON(), nullable=False, server_default='{}'))
    with op.batch_alter_table('reports') as b:
        b.add_column(sa.Column('auto', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table('reports') as b:
        b.drop_column('auto')
    with op.batch_alter_table('coding_sessions') as b:
        b.drop_column('plan')
        b.drop_column('language')
        b.drop_column('resume_id')
        b.drop_column('company_slug')
    with op.batch_alter_table('coding_problems') as b:
        b.drop_column('ds')
        b.drop_column('tags')
