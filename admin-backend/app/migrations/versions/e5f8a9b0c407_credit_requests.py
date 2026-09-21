"""add credit_requests table for user credit top-up requests

Revision ID: e5f8a9b0c407
Revises: d4e7f8a9b306
Create Date: 2026-09-17 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f8a9b0c407"
down_revision: Union[str, None] = "d4e7f8a9b306"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credit_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("requested_amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Pending"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.Integer(), sa.ForeignKey("admins.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_credit_requests_user_id", "credit_requests", ["user_id"])
    op.create_index("ix_credit_requests_status", "credit_requests", ["status"])
    op.create_index("ix_credit_requests_created_at", "credit_requests", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_credit_requests_created_at", table_name="credit_requests")
    op.drop_index("ix_credit_requests_status", table_name="credit_requests")
    op.drop_index("ix_credit_requests_user_id", table_name="credit_requests")
    op.drop_table("credit_requests")
