"""admin token_version + dashboard.view / reports.view permissions

Revision ID: f6a9b0c1d508
Revises: 873759b1e2e9
Create Date: 2026-09-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a9b0c1d508'
down_revision: Union[str, None] = '873759b1e2e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Self-contained snapshot (migrations must not depend on the live catalog).
NEW_PERMISSIONS = {
    'dashboard.view': 'View the dashboard overview',
    'reports.view': 'View simulation/game statistics reports',
}
GRANTS = {
    'dashboard.view': ['super_admin', 'admin', 'manager', 'support'],
    'reports.view': ['super_admin', 'admin', 'manager'],
}


def upgrade() -> None:
    with op.batch_alter_table('admins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))

    permissions = sa.table('permissions', sa.column('id', sa.Integer), sa.column('code', sa.String), sa.column('description', sa.String))
    roles = sa.table('roles', sa.column('id', sa.Integer), sa.column('slug', sa.String))
    role_permissions = sa.table('role_permissions', sa.column('role_id', sa.Integer), sa.column('permission_id', sa.Integer))
    conn = op.get_bind()

    conn.execute(permissions.insert(), [{'code': c, 'description': d} for c, d in NEW_PERMISSIONS.items()])
    perm_id = {r.code: r.id for r in conn.execute(sa.select(permissions.c.id, permissions.c.code))}
    role_id = {r.slug: r.id for r in conn.execute(sa.select(roles.c.id, roles.c.slug))}
    rows = [
        {'role_id': role_id[slug], 'permission_id': perm_id[code]}
        for code, slugs in GRANTS.items()
        for slug in slugs
        if slug in role_id
    ]
    if rows:
        conn.execute(role_permissions.insert(), rows)


def downgrade() -> None:
    permissions = sa.table('permissions', sa.column('id', sa.Integer), sa.column('code', sa.String))
    role_permissions = sa.table('role_permissions', sa.column('permission_id', sa.Integer))
    conn = op.get_bind()
    ids = [r.id for r in conn.execute(sa.select(permissions.c.id).where(permissions.c.code.in_(list(NEW_PERMISSIONS))))]
    if ids:
        conn.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(ids)))
        conn.execute(permissions.delete().where(permissions.c.id.in_(ids)))
    with op.batch_alter_table('admins', schema=None) as batch_op:
        batch_op.drop_column('token_version')
