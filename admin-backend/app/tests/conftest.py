from __future__ import annotations

import os
from datetime import date, time

os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_db
from app.core.rbac_catalog import PERMISSIONS, ROLE_NAMES, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models.admin import Admin
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, MarketCategory
from app.models.rate import Rate
from app.models.role import Permission, Role, RolePermission
from app.models.user import User

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _reset_state():
    from app.core import ratelimit
    ratelimit.reset()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    db.add(Admin(name="Super Admin", email="admin@kalyan.com", password_hash=hash_password("admin123"), role="super_admin", status="active"))
    db.add(User(name="Test User", phone="9000000000", email="test@example.com", password_hash=hash_password("user12345"), status="active", balance=1000))

    permissions = [Permission(code=code, description=desc) for code, desc in PERMISSIONS]
    db.add_all(permissions)
    db.commit()
    perm_by_code = {p.code: p for p in permissions}

    roles = [Role(slug=slug, name=ROLE_NAMES[slug]) for slug in ROLE_PERMISSIONS]
    db.add_all(roles)
    db.commit()
    for role in roles:
        db.add_all(
            RolePermission(role_id=role.id, permission_id=perm_by_code[code].id)
            for code in ROLE_PERMISSIONS[role.slug]
        )
    db.commit()
    category = MarketCategory(slug="MATKA", name="Matka Markets", display_order=1)
    db.add(category)
    db.commit()

    game_types = [
        GameType(code="SINGLE", name="Single", digit_length=1, classification_rule="NONE", display_order=1),
        GameType(code="JODI", name="Jodi", digit_length=2, classification_rule="NONE", display_order=2),
        GameType(code="SINGLE_PANNA", name="Single Panna", digit_length=3, classification_rule="PANNA_SINGLE", display_order=3),
        GameType(code="DOUBLE_PANNA", name="Double Panna", digit_length=3, classification_rule="PANNA_DOUBLE", display_order=4),
        GameType(code="TRIPLE_PANNA", name="Triple Panna", digit_length=3, classification_rule="PANNA_TRIPLE", display_order=5),
    ]
    db.add_all(game_types)
    db.commit()

    market = Market(category_id=category.id, name="TESTGAME", slug="testgame", status="OPEN", display_order=1)
    db.add(market)
    db.commit()

    gt_by_code = {g.code: g for g in game_types}
    configs = [
        GameTypeConfig(market_id=market.id, game_type_id=gt_by_code["SINGLE"].id, stage="OPEN"),
        GameTypeConfig(market_id=market.id, game_type_id=gt_by_code["SINGLE"].id, stage="CLOSE"),
        GameTypeConfig(market_id=market.id, game_type_id=gt_by_code["JODI"].id, stage="BOTH"),
        GameTypeConfig(market_id=market.id, game_type_id=gt_by_code["SINGLE_PANNA"].id, stage="OPEN"),
        GameTypeConfig(market_id=market.id, game_type_id=gt_by_code["DOUBLE_PANNA"].id, stage="OPEN"),
        GameTypeConfig(market_id=market.id, game_type_id=gt_by_code["TRIPLE_PANNA"].id, stage="OPEN"),
    ]
    db.add_all(configs)
    db.commit()

    for code in ["SINGLE", "JODI", "SINGLE_PANNA", "DOUBLE_PANNA", "TRIPLE_PANNA"]:
        db.add(Rate(market_id=market.id, game_type_id=gt_by_code[code].id, rate=95, effective_from=date(2020, 1, 1), status="Active"))
    db.commit()
    db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    resp = client.post("/admin/auth/login", json={"email": "admin@kalyan.com", "password": "admin123"})
    return resp.json()["token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_token(client):
    resp = client.post("/auth/login", json={"phone": "9000000000", "password": "user12345"})
    return resp.json()["token"]


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
