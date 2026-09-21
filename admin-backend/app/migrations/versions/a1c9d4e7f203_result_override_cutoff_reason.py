"""result override, cutoff enforcement, mandatory correction reason

Revision ID: a1c9d4e7f203
Revises: 8bdcf2fe512b
Create Date: 2026-09-15 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c9d4e7f203'
down_revision: Union[str, None] = '8bdcf2fe512b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('markets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cutoff_time', sa.Time(), nullable=True))

    with op.batch_alter_table('market_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('correction_reason', sa.String(length=500), nullable=True))

    with op.batch_alter_table('simulation_entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('override_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('override_reason', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('overridden_by_admin_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('overridden_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            'fk_simulation_entries_overridden_by_admin_id', 'admins', ['overridden_by_admin_id'], ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('simulation_entries', schema=None) as batch_op:
        batch_op.drop_constraint('fk_simulation_entries_overridden_by_admin_id', type_='foreignkey')
        batch_op.drop_column('overridden_at')
        batch_op.drop_column('overridden_by_admin_id')
        batch_op.drop_column('override_reason')
        batch_op.drop_column('override_status')
        batch_op.drop_column('original_status')

    with op.batch_alter_table('market_results', schema=None) as batch_op:
        batch_op.drop_column('correction_reason')

    with op.batch_alter_table('markets', schema=None) as batch_op:
        batch_op.drop_column('cutoff_time')
