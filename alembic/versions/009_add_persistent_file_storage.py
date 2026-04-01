"""add persistent file storage (codebase_snapshots + snapshot_files)

Revision ID: 009
Revises: 008
Create Date: 2026-03-31

"""
from alembic import op
import sqlalchemy as sa


revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # ── codebase_snapshots ────────────────────────────────────────────────────
    op.create_table(
        'codebase_snapshots',
        sa.Column('id',             sa.Integer(),    primary_key=True),
        sa.Column('project_id',     sa.Integer(),    sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('source_path',    sa.String(),     nullable=False),
        sa.Column('total_size_mb',  sa.Float(),      nullable=True, default=0.0),
        sa.Column('language_stats', sa.JSON(),       nullable=True),
        sa.Column('agent_metadata', sa.JSON(),       nullable=True),
        sa.Column('created_by',     sa.Integer(),    sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at',     sa.DateTime(),   nullable=True),
    )
    op.create_index('idx_snapshots_project_id', 'codebase_snapshots', ['project_id'])

    # ── snapshot_files ────────────────────────────────────────────────────────
    op.create_table(
        'snapshot_files',
        sa.Column('id',          sa.Integer(), primary_key=True),
        sa.Column('snapshot_id', sa.Integer(), sa.ForeignKey('codebase_snapshots.id'), nullable=False),
        sa.Column('path',        sa.String(),  nullable=False),
        sa.Column('size_bytes',  sa.Integer(), nullable=True, default=0),
        sa.Column('language',    sa.String(),  nullable=True),
        sa.Column('hash',        sa.String(),  nullable=True),
        sa.Column('line_count',  sa.Integer(), nullable=True, default=0),
        sa.Column('content',     sa.Text(),    nullable=True),
    )
    op.create_index('idx_snapshot_files_snapshot_id', 'snapshot_files', ['snapshot_id'])
    op.create_index('idx_snapshot_files_path',        'snapshot_files', ['snapshot_id', 'path'])

    # ── snapshot_id FK on autonomous_review_jobs ──────────────────────────────
    op.add_column(
        'autonomous_review_jobs',
        sa.Column('snapshot_id', sa.Integer(),
                  sa.ForeignKey('codebase_snapshots.id', ondelete='SET NULL'),
                  nullable=True),
    )
    op.create_index('idx_arj_snapshot_id', 'autonomous_review_jobs', ['snapshot_id'])


def downgrade():
    op.drop_index('idx_arj_snapshot_id',             table_name='autonomous_review_jobs')
    op.drop_column('autonomous_review_jobs', 'snapshot_id')

    op.drop_index('idx_snapshot_files_path',          table_name='snapshot_files')
    op.drop_index('idx_snapshot_files_snapshot_id',   table_name='snapshot_files')
    op.drop_table('snapshot_files')

    op.drop_index('idx_snapshots_project_id',         table_name='codebase_snapshots')
    op.drop_table('codebase_snapshots')
