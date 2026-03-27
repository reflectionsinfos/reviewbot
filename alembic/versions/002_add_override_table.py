"""Add autonomous review override table

Revision ID: 002
Revises: 001
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create autonomous_review_overrides table
    op.create_table('autonomous_review_overrides',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('result_id', sa.Integer(), nullable=False),
    sa.Column('new_rag_status', sa.String(), nullable=False),
    sa.Column('comments', sa.Text(), nullable=False),
    sa.Column('reason', sa.String(), nullable=True),
    sa.Column('overridden_by', sa.Integer(), nullable=False),
    sa.Column('overridden_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['result_id'], ['autonomous_review_results.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['overridden_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for faster lookups
    op.create_index('idx_override_result', 'autonomous_review_overrides', ['result_id'])
    op.create_index('idx_override_user', 'autonomous_review_overrides', ['overridden_by'])


def downgrade() -> None:
    op.drop_index('idx_override_user', table_name='autonomous_review_overrides')
    op.drop_index('idx_override_result', table_name='autonomous_review_overrides')
    op.drop_table('autonomous_review_overrides')
