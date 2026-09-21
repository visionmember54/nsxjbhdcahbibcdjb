"""add audit subject user for user activity timelines

Revision ID: d4e7f8a9b306
Revises: c3f6a7b8d205
Create Date: 2026-09-15 23:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e7f8a9b306"
down_revision: Union[str, None] = "c3f6a7b8d205"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject_user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_audit_logs_subject_user_id", ["subject_user_id"], unique=False)
        batch_op.create_foreign_key("fk_audit_logs_subject_user_id", "users", ["subject_user_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.drop_constraint("fk_audit_logs_subject_user_id", type_="foreignkey")
        batch_op.drop_index("ix_audit_logs_subject_user_id")
        batch_op.drop_column("subject_user_id")
