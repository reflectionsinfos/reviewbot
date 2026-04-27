"""add offline review fields

Revision ID: 009
Revises: 008
Create Date: 2026-04-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('reviews') as batch_op:
        batch_op.add_column(sa.Column('review_type', sa.String(), nullable=True, server_default='online'))
        batch_op.add_column(sa.Column('assigned_reviewer_email', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('assigned_reviewer_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('upload_token', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('upload_token_expiry', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('excel_sent_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('first_accessed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('excel_downloaded_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('excel_uploaded_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('excel_response_path', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('offline_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('due_date', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_reviews_upload_token', ['upload_token'])


def downgrade():
    with op.batch_alter_table('reviews') as batch_op:
        batch_op.drop_index('ix_reviews_upload_token')
        batch_op.drop_column('due_date')
        batch_op.drop_column('offline_message')
        batch_op.drop_column('excel_response_path')
        batch_op.drop_column('excel_uploaded_at')
        batch_op.drop_column('excel_downloaded_at')
        batch_op.drop_column('first_accessed_at')
        batch_op.drop_column('excel_sent_at')
        batch_op.drop_column('upload_token_expiry')
        batch_op.drop_column('upload_token')
        batch_op.drop_column('assigned_reviewer_name')
        batch_op.drop_column('assigned_reviewer_email')
        batch_op.drop_column('review_type')
