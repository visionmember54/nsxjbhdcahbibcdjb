"""The permission catalog: every distinct (resource, action) surface currently
gated by an admin router, enumerated by grepping every require_roles(...) call
site. Used by app/seed.py (dev reset) to seed Role/Permission/RolePermission
rows -- the Alembic migration that ships this to a real database inlines its
own copy, since migrations must stay self-contained and reproducible."""
from __future__ import annotations

ROLE_NAMES: dict[str, str] = {
    "super_admin": "Super Admin",
    "admin": "Admin",
    "manager": "Manager",
    "support": "Support",
}

PERMISSIONS: list[tuple[str, str]] = [
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
    ("dashboard.view", "View the dashboard overview"),
    ("reports.view", "View simulation/game statistics reports"),
]

_ALL_CODES = [code for code, _ in PERMISSIONS]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": _ALL_CODES,
    "admin": [code for code in _ALL_CODES if code != "admins.manage"],
    "manager": [
        "markets.manage", "game_type_configs.manage", "starline.manage", "rates.manage",
        "simulations.create", "credits.manage", "users.manage", "content.manage",
        "dashboard.view", "reports.view",
    ],
    "support": ["support.manage", "dashboard.view"],
}
