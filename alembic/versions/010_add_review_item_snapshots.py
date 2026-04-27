"""add review item snapshots

Revision ID: 010
Revises: 009
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "review_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("source_checklist_item_id", sa.Integer(), nullable=True),
        sa.Column("item_code", sa.String(), nullable=True),
        sa.Column("area", sa.String(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True, default=1.0),
        sa.Column("is_review_mandatory", sa.Boolean(), nullable=True, default=True),
        sa.Column("expected_evidence", sa.Text(), nullable=True),
        sa.Column("team_category", sa.String(), nullable=True),
        sa.Column("guidance", sa.Text(), nullable=True),
        sa.Column("applicability_tags", sa.JSON(), nullable=True),
        sa.Column("suggested_for_domains", sa.JSON(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=True, default=0),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_checklist_item_id"], ["checklist_items.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_review_items_id", "review_items", ["id"])
    op.create_index("ix_review_items_review_id", "review_items", ["review_id"])
    op.create_index("ix_review_items_source_checklist_item_id", "review_items", ["source_checklist_item_id"])
    op.add_column("review_responses", sa.Column("review_item_id", sa.Integer(), nullable=True))
    op.create_index("ix_review_responses_review_item_id", "review_responses", ["review_item_id"])
    op.create_foreign_key(
        "review_responses_review_item_id_fkey",
        "review_responses",
        "review_items",
        ["review_item_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("review_responses_review_item_id_fkey", "review_responses", type_="foreignkey")
    op.drop_index("ix_review_responses_review_item_id", table_name="review_responses")
    op.drop_column("review_responses", "review_item_id")
    op.drop_index("ix_review_items_source_checklist_item_id", table_name="review_items")
    op.drop_index("ix_review_items_review_id", table_name="review_items")
    op.drop_index("ix_review_items_id", table_name="review_items")
    op.drop_table("review_items")
