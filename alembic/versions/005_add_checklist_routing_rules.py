"""Add checklist_routing_rules table

Revision ID: 005
Revises: 004
Create Date: 2026-03-28

Allows admins/PMs/leads to override the strategy router on a per-item basis
without touching Python code or requiring a deployment.
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'checklist_routing_rules',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('checklist_item_id', sa.Integer(),
                  sa.ForeignKey('checklist_items.id', ondelete='CASCADE'),
                  nullable=True, index=True),
        sa.Column('checklist_id', sa.Integer(),
                  sa.ForeignKey('checklists.id', ondelete='CASCADE'),
                  nullable=True, index=True),
        sa.Column('strategy', sa.String(50), nullable=False, server_default='human_required'),
        sa.Column('skip_reason', sa.Text(), nullable=True),
        sa.Column('evidence_hint', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(),
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade():
    op.drop_table('checklist_routing_rules')
