"""add game variant for Half Sangam selections

Revision ID: c3f6a7b8d205
Revises: b2d8e5f9a104
Create Date: 2026-09-15 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3f6a7b8d205"
down_revision: Union[str, None] = "b2d8e5f9a104"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("simulation_entries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("game_variant", sa.String(length=30), nullable=True))
    game_types = sa.table(
        "game_types",
        sa.column("code", sa.String), sa.column("name", sa.String), sa.column("description", sa.String),
        sa.column("digit_length", sa.Integer), sa.column("classification_rule", sa.String),
        sa.column("is_active", sa.Boolean), sa.column("display_order", sa.Integer),
    )
    op.bulk_insert(game_types, [
        {"code": "HALF_SANGAM", "name": "Half Sangam", "description": "Panna and ank across open/close results.", "digit_length": 5, "classification_rule": "SANGAM_HALF", "is_active": True, "display_order": 9},
        {"code": "FULL_SANGAM", "name": "Full Sangam", "description": "Open and close panna across one result.", "digit_length": 7, "classification_rule": "SANGAM_FULL", "is_active": True, "display_order": 10},
    ])


def downgrade() -> None:
    op.execute("DELETE FROM game_types WHERE code IN ('HALF_SANGAM', 'FULL_SANGAM')")
    with op.batch_alter_table("simulation_entries", schema=None) as batch_op:
        batch_op.drop_column("game_variant")
