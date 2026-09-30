"""add display_order to game_type_configs

Revision ID: c8d9e0f1a209
Revises: b3c4d5e6f708
Create Date: 2026-09-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a209'
down_revision: Union[str, None] = 'b3c4d5e6f708'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('game_type_configs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    with op.batch_alter_table('game_type_configs', schema=None) as batch_op:
        batch_op.drop_column('display_order')
