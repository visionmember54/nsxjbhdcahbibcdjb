"""Merge result-selection and UPI migration branches.

Revision ID: c0d9e8f7a615
Revises: 9ac2d4e6f810, b7c8d9e0f112
"""
from typing import Sequence, Union


revision: str = "c0d9e8f7a615"
down_revision: Union[str, Sequence[str], None] = (
    "9ac2d4e6f810",
    "b7c8d9e0f112",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Both parent revisions already apply their schema changes.
    pass


def downgrade() -> None:
    # Merge revisions only join history; downgrade the parent revisions separately.
    pass
