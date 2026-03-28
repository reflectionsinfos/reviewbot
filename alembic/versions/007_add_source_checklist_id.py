"""add source_checklist_id

Revision ID: 007
Revises: 006
Create Date: 2026-03-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('checklists', sa.Column('source_checklist_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_checklists_source_checklist_id_checklists',
        'checklists',
        'checklists',
        ['source_checklist_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_checklists_source_checklist_id_checklists', 'checklists', type_='foreignkey')
    op.drop_column('checklists', 'source_checklist_id')
