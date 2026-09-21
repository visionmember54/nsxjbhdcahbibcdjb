"""users.security_pin / users.last_seen and the user_payment_info table

These existed on the models but in no earlier migration, so a database built purely by
`alembic upgrade head` was missing them. Guarded, because databases that were once built with
create_all() already have them.

Revision ID: a7b8c9d0e109
Revises: f6a9b0c1d508
Create Date: 2026-09-22 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7b8c9d0e109'
down_revision: Union[str, None] = 'f6a9b0c1d508'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    have = {c['name'] for c in insp.get_columns('users')}
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'security_pin' not in have:
            batch_op.add_column(sa.Column('security_pin', sa.String(length=10), nullable=True))
        if 'last_seen' not in have:
            batch_op.add_column(sa.Column('last_seen', sa.DateTime(), nullable=True))

    if not insp.has_table('user_payment_info'):
        op.create_table(
            'user_payment_info',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('payment_method', sa.String(length=50), nullable=False),
            sa.Column('account_name', sa.String(length=100), nullable=True),
            sa.Column('account_number', sa.String(length=100), nullable=True),
            sa.Column('ifsc_code', sa.String(length=50), nullable=True),
            sa.Column('upi_id', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_user_payment_info_user_id'), 'user_payment_info', ['user_id'], unique=False)


def downgrade() -> None:
    # Not dropped: these may predate this migration on some databases, and dropping user data is unsafe.
    pass
