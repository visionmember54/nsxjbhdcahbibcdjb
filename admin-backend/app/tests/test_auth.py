from __future__ import annotations


def test_admin_login_success(client):
    resp = client.post("/admin/auth/login", json={"email": "admin@kalyan.com", "password": "admin123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["role"] == "super_admin"
    assert body["token"]


def test_admin_login_wrong_password(client):
    resp = client.post("/admin/auth/login", json={"email": "admin@kalyan.com", "password": "wrong"})
    assert resp.status_code == 401


def test_admin_me_requires_token(client):
    resp = client.get("/admin/auth/me")
    assert resp.status_code == 401


def test_admin_me_with_token(client, auth_headers):
    resp = client.get("/admin/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@kalyan.com"


def test_login_and_me_include_own_permissions(client, auth_headers):
    login = client.post("/admin/auth/login", json={"email": "admin@kalyan.com", "password": "admin123"})
    assert "admins.manage" in login.json()["user"]["permissions"]

    me = client.get("/admin/auth/me", headers=auth_headers)
    assert "admins.manage" in me.json()["permissions"]
    assert "results.correct" in me.json()["permissions"]


def test_admin_login_rate_limited_after_five_attempts(client):
    for _ in range(5):
        resp = client.post("/admin/auth/login", json={"email": "nope@kalyan.com", "password": "wrong"})
        assert resp.status_code == 401
    resp = client.post("/admin/auth/login", json={"email": "nope@kalyan.com", "password": "wrong"})
    assert resp.status_code == 429


def test_user_register_and_login(client):
    resp = client.post("/auth/register", json={"name": "New User", "phone": "9111111111", "password": "pass123"})
    assert resp.status_code == 201
    assert resp.json()["user"]["balance"] == 0

    resp = client.post("/auth/login", json={"phone": "9111111111", "password": "pass123"})
    assert resp.status_code == 200
    assert resp.json()["token"]


def test_user_token_rejected_on_admin_endpoints(client, user_headers):
    resp = client.get("/admin/users", headers=user_headers)
    assert resp.status_code == 401


def test_admin_token_rejected_on_user_endpoints(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 401


def test_logout_revokes_token(client, auth_headers):
    assert client.get("/admin/auth/me", headers=auth_headers).status_code == 200
    assert client.post("/admin/auth/logout", headers=auth_headers).status_code == 200
    assert client.get("/admin/auth/me", headers=auth_headers).status_code == 401


def test_successful_login_clears_failures(client):
    for _ in range(4):
        client.post("/admin/auth/login", json={"email": "admin@kalyan.com", "password": "wrong"})
    ok = client.post("/admin/auth/login", json={"email": "admin@kalyan.com", "password": "admin123"})
    assert ok.status_code == 200


def test_reports_and_dashboard_require_permission(client, db_session_factory=None):
    from app.tests.conftest import TestingSessionLocal
    from app.core.security import hash_password
    from app.models.admin import Admin
    from app.models.role import Role

    db = TestingSessionLocal()
    db.add(Role(slug="nobody", name="Nobody"))
    db.add(Admin(name="N", email="n@kalyan.com", password_hash=hash_password("password123"), role="nobody", status="active"))
    db.commit()
    db.close()
    token = client.post("/admin/auth/login", json={"email": "n@kalyan.com", "password": "password123"}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/admin/reports/simulation-statistics", headers=h).status_code == 403
    assert client.get("/admin/dashboard", headers=h).status_code == 403


def test_user_reset_password_returns_temporary_and_no_pin(client, auth_headers):
    users = client.get("/admin/users", headers=auth_headers).json()["items"]
    assert "security_pin" not in users[0]
    uid = users[0]["id"]
    resp = client.post(f"/admin/users/{uid}/reset-password", headers=auth_headers)
    temp = resp.json()["temporary_password"]
    assert len(temp) >= 8 and temp != "user12345"


def test_cors_rejects_unlisted_origin(client):
    resp = client.options(
        "/admin/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in resp.headers
