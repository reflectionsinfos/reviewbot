"""rename is_required to is_review_mandatory

Revision ID: 008
Revises: 007
Create Date: 2026-03-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('checklist_items') as batch_op:
        batch_op.add_column(
            sa.Column('is_review_mandatory', sa.Boolean(), nullable=False, server_default=sa.true())
        )

    op.execute(
        sa.text(
            "UPDATE checklist_items "
            "SET is_review_mandatory = COALESCE(is_required, TRUE)"
        )
    )

    with op.batch_alter_table('checklist_items') as batch_op:
        batch_op.drop_column('is_required')


def downgrade():
    with op.batch_alter_table('checklist_items') as batch_op:
        batch_op.add_column(
            sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.true())
        )

    op.execute(
        sa.text(
            "UPDATE checklist_items "
            "SET is_required = COALESCE(is_review_mandatory, TRUE)"
        )
    )

    with op.batch_alter_table('checklist_items') as batch_op:
        batch_op.drop_column('is_review_mandatory')
