"""Add report history support - link reports to autonomous jobs

Revision ID: 003
Revises: 002
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add autonomous_review_job_id to reports table
    op.add_column('reports', 
                  sa.Column('autonomous_review_job_id', sa.Integer(), 
                           sa.ForeignKey('autonomous_review_jobs.id', ondelete='SET NULL'), 
                           nullable=True))
    
    # Add index for faster lookups
    op.create_index('idx_report_autonomous_job', 'reports', ['autonomous_review_job_id'])


def downgrade() -> None:
    op.drop_index('idx_report_autonomous_job', table_name='reports')
    op.drop_column('reports', 'autonomous_review_job_id')
