"""company-wise question bank

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-06 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'bank_questions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('kind', sa.String(length=12), nullable=False),
        sa.Column('category', sa.String(length=40), nullable=False),
        sa.Column('difficulty', sa.String(length=8), nullable=False),
        sa.Column('roles', sa.JSON(), nullable=False),
        sa.Column('companies', sa.JSON(), nullable=False),
        sa.Column('topics', sa.JSON(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('ideal_answer', sa.Text(), nullable=False),
        sa.Column('key_points', sa.JSON(), nullable=False),
        sa.Column('follow_ups', sa.JSON(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('answer_index', sa.Integer(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('source_label', sa.String(length=32), nullable=False),
        sa.Column('source_note', sa.String(length=300), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("kind in ('technical','scenario','mcq','output')", name='ck_bank_questions_kind_valid'),
        sa.CheckConstraint("difficulty in ('easy','medium','hard')", name='ck_bank_questions_difficulty_valid'),
        sa.CheckConstraint("source_label in ('verified','reported','company_focused_practice')", name='ck_bank_questions_source_valid'),
    )
    for col in ('slug', 'kind', 'category', 'source_label', 'enabled'):
        op.create_index(f'ix_bank_questions_{col}', 'bank_questions', [col], unique=(col == 'slug'))


def downgrade() -> None:
    op.drop_table('bank_questions')
