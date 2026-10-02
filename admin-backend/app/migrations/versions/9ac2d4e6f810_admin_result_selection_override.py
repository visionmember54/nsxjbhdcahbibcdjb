"""Store admin-only result selection overrides separately from user bets.

Revision ID: 9ac2d4e6f810
Revises: f6a9b0c1d508
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9ac2d4e6f810"
down_revision: Union[str, None] = "f6a9b0c1d508"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("simulation_entries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("result_selection_override", sa.String(length=10), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("simulation_entries", schema=None) as batch_op:
        batch_op.drop_column("result_selection_override")
