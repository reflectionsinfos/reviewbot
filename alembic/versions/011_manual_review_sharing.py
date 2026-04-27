"""manual review sharing and portal response tracking

Revision ID: 011
Revises: 010
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    # Track whether a response was last written via web portal, Excel, or AI
    op.add_column(
        "review_responses",
        sa.Column("last_updated_via", sa.String(), nullable=True),
    )

    # Manual review share table — supports internal user and external magic-link sharing
    op.create_table(
        "manual_review_shares",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("shared_with_user_id", sa.Integer(), nullable=True),
        sa.Column("shared_with_email", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True, default="contributor"),
        sa.Column("token", sa.String(), nullable=True, unique=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_with_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_manual_review_shares_id", "manual_review_shares", ["id"])
    op.create_index("ix_manual_review_shares_review_id", "manual_review_shares", ["review_id"])
    op.create_index(
        "ix_manual_review_shares_token",
        "manual_review_shares",
        ["token"],
        unique=True,
        postgresql_where=sa.text("token IS NOT NULL"),
    )


def downgrade():
    op.drop_index("ix_manual_review_shares_token", table_name="manual_review_shares")
    op.drop_index("ix_manual_review_shares_review_id", table_name="manual_review_shares")
    op.drop_index("ix_manual_review_shares_id", table_name="manual_review_shares")
    op.drop_table("manual_review_shares")
    op.drop_column("review_responses", "last_updated_via")
