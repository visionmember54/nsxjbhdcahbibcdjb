"""Add unique UPI order references to deposit requests.

Revision ID: b7c8d9e0f112
Revises: d1e2f3a4b5c6
Create Date: 2026-10-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f112"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("credit_requests"):
        return

    columns = {column["name"] for column in inspector.get_columns("credit_requests")}
    with op.batch_alter_table("credit_requests") as batch:
        if "order_id" not in columns:
            batch.add_column(sa.Column("order_id", sa.String(length=64), nullable=True))
        if "transaction_id" not in columns:
            batch.add_column(sa.Column("transaction_id", sa.String(length=100), nullable=True))
        if "upi_app" not in columns:
            batch.add_column(sa.Column("upi_app", sa.String(length=32), nullable=True))

    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("credit_requests")}
    if "ix_credit_requests_order_id" not in indexes:
        op.create_index("ix_credit_requests_order_id", "credit_requests", ["order_id"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("credit_requests"):
        return
    indexes = {index["name"] for index in inspector.get_indexes("credit_requests")}
    if "ix_credit_requests_order_id" in indexes:
        op.drop_index("ix_credit_requests_order_id", table_name="credit_requests")
    columns = {column["name"] for column in inspector.get_columns("credit_requests")}
    with op.batch_alter_table("credit_requests") as batch:
        for name in ("upi_app", "transaction_id", "order_id"):
            if name in columns:
                batch.drop_column(name)
