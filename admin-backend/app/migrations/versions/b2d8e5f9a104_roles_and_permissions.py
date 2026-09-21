"""roles and permissions (data-driven RBAC)

Revision ID: b2d8e5f9a104
Revises: a1c9d4e7f203
Create Date: 2026-09-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d8e5f9a104'
down_revision: Union[str, None] = 'a1c9d4e7f203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Inlined snapshot of app/core/rbac_catalog.py as of this migration -- migrations
# must stay self-contained and reproducible even if the catalog changes later.
ROLE_NAMES = {
    "super_admin": "Super Admin",
    "admin": "Admin",
    "manager": "Manager",
    "support": "Support",
}

PERMISSIONS = [
    ("markets.manage", "Create and update markets, change market status"),
    ("market_categories.manage", "Create market categories"),
    ("game_types.manage", "Create and update game types"),
    ("game_type_configs.manage", "Enable/configure game types per market or slot"),
    ("starline.manage", "Create and update Starline slots"),
    ("rates.manage", "Create and update simulated rates"),
    ("results.manage", "Enter and publish market results"),
    ("results.correct", "Correct a published market result"),
    ("results.delete", "Delete a result record"),
    ("simulations.create", "Submit simulations/bulk batches on behalf of a user"),
    ("simulations.override", "Override an individual simulation's outcome"),
    ("credits.manage", "Grant, adjust, and reset user Learning Credit balances"),
    ("users.manage", "Create users, change user account status"),
    ("admins.manage", "Manage admin accounts and roles & permissions"),
    ("audit_logs.view", "View the audit log"),
    ("content.manage", "Create and update homepage banners, scrolling messages, educational content, FAQs"),
    ("content.delete", "Delete homepage banners, scrolling messages, FAQs"),
    ("content.settings", "Update site settings (support contact info, hero image, ...)"),
    ("support.manage", "Reply to support queries"),
]

_ALL_CODES = [code for code, _ in PERMISSIONS]

ROLE_PERMISSIONS = {
    "super_admin": _ALL_CODES,
    "admin": [code for code in _ALL_CODES if code != "admins.manage"],
    "manager": [
        "markets.manage", "game_type_configs.manage", "starline.manage", "rates.manage",
        "simulations.create", "credits.manage", "users.manage", "content.manage",
    ],
    "support": ["support.manage"],
}


def upgrade() -> None:
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roles_slug'), ['slug'], unique=True)

    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=60), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_permissions_code'), ['code'], unique=True)

    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    with op.batch_alter_table('role_permissions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_role_permissions_role_id'), ['role_id'])
        batch_op.create_index(batch_op.f('ix_role_permissions_permission_id'), ['permission_id'])

    roles_table = sa.table('roles', sa.column('id', sa.Integer), sa.column('slug', sa.String), sa.column('name', sa.String))
    permissions_table = sa.table('permissions', sa.column('id', sa.Integer), sa.column('code', sa.String), sa.column('description', sa.String))
    role_permissions_table = sa.table('role_permissions', sa.column('role_id', sa.Integer), sa.column('permission_id', sa.Integer))

    connection = op.get_bind()

    connection.execute(
        roles_table.insert(),
        [{'slug': slug, 'name': name} for slug, name in ROLE_NAMES.items()],
    )
    connection.execute(
        permissions_table.insert(),
        [{'code': code, 'description': desc} for code, desc in PERMISSIONS],
    )

    role_id_by_slug = {row.slug: row.id for row in connection.execute(sa.select(roles_table.c.id, roles_table.c.slug))}
    permission_id_by_code = {row.code: row.id for row in connection.execute(sa.select(permissions_table.c.id, permissions_table.c.code))}

    role_permission_rows = [
        {'role_id': role_id_by_slug[slug], 'permission_id': permission_id_by_code[code]}
        for slug, codes in ROLE_PERMISSIONS.items()
        for code in codes
    ]
    connection.execute(role_permissions_table.insert(), role_permission_rows)


def downgrade() -> None:
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
