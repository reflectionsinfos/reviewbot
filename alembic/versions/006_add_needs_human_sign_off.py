"""Add needs_human_sign_off to autonomous_review_results

Revision ID: 006
Revises: 005
Create Date: 2026-03-28

Supports the new "AI + Human" routing mode where the bot runs its analysis
but a human must confirm the final RAG status.
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'autonomous_review_results',
        sa.Column('needs_human_sign_off', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade():
    op.drop_column('autonomous_review_results', 'needs_human_sign_off')
