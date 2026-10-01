"""support chat attachments + nullable message text

Revision ID: d1e2f3a4b5c6
Revises: c8d9e0f1a209
Create Date: 2026-10-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c8d9e0f1a209'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('support_messages', schema=None) as batch_op:
        batch_op.alter_column('text', existing_type=sa.Text(), nullable=True)
        batch_op.add_column(sa.Column('attachment_url', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('attachment_type', sa.String(length=10), nullable=True))

    op.create_table(
        'support_attachments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('data', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('support_attachments')
    with op.batch_alter_table('support_messages', schema=None) as batch_op:
        batch_op.drop_column('attachment_type')
        batch_op.drop_column('attachment_url')
        batch_op.alter_column('text', existing_type=sa.Text(), nullable=False)
