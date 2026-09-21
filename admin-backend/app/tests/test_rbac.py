from __future__ import annotations


def test_manager_cannot_list_admins(client, auth_headers):
    resp = client.post(
        "/admin/admins",
        headers=auth_headers,
        json={"name": "Manager One", "email": "manager1@kalyan.com", "password": "manager123", "role": "manager"},
    )
    assert resp.status_code == 201

    login = client.post("/admin/auth/login", json={"email": "manager1@kalyan.com", "password": "manager123"})
    manager_headers = {"Authorization": f"Bearer {login.json()['token']}"}

    resp = client.get("/admin/admins", headers=manager_headers)
    assert resp.status_code == 403


def test_manager_can_create_user(client, auth_headers):
    resp = client.post(
        "/admin/admins",
        headers=auth_headers,
        json={"name": "Manager Two", "email": "manager2@kalyan.com", "password": "manager123", "role": "manager"},
    )
    assert resp.status_code == 201

    login = client.post("/admin/auth/login", json={"email": "manager2@kalyan.com", "password": "manager123"})
    manager_headers = {"Authorization": f"Bearer {login.json()['token']}"}

    resp = client.post("/admin/users", headers=manager_headers, json={"name": "New User", "phone": "9111111111"})
    assert resp.status_code == 201


def test_admin_cannot_disable_own_account(client, auth_headers):
    me = client.get("/admin/auth/me", headers=auth_headers).json()
    resp = client.patch(f"/admin/admins/{me['id']}", headers=auth_headers, json={"status": "disabled"})
    assert resp.status_code == 400


def _manager_headers(client, auth_headers, email="manager-rbac@kalyan.com"):
    client.post(
        "/admin/admins", headers=auth_headers,
        json={"name": "Manager RBAC", "email": email, "password": "manager123", "role": "manager"},
    )
    login = client.post("/admin/auth/login", json={"email": email, "password": "manager123"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_manager_cannot_correct_results_or_manage_admins(client, auth_headers):
    manager_headers = _manager_headers(client, auth_headers)
    resp = client.get("/admin/admins", headers=manager_headers)
    assert resp.status_code == 403
    resp = client.get("/admin/roles", headers=manager_headers)
    assert resp.status_code == 403


def test_super_admin_can_list_roles_with_seeded_permissions(client, auth_headers):
    resp = client.get("/admin/roles", headers=auth_headers)
    assert resp.status_code == 200
    roles = {r["slug"]: r for r in resp.json()}
    assert "admins.manage" in roles["super_admin"]["permissions"]
    assert "admins.manage" not in roles["admin"]["permissions"]
    assert "results.correct" in roles["admin"]["permissions"]
    assert "results.correct" not in roles["manager"]["permissions"]
    assert roles["support"]["permissions"] == ["dashboard.view", "support.manage"]


def test_create_custom_role_and_grant_specific_permissions(client, auth_headers):
    resp = client.post("/admin/roles", headers=auth_headers, json={"slug": "auditor", "name": "Auditor"})
    assert resp.status_code == 201
    role_id = resp.json()["id"]
    assert resp.json()["permissions"] == []

    resp = client.put(f"/admin/roles/{role_id}/permissions", headers=auth_headers, json={"permission_codes": ["audit_logs.view"]})
    assert resp.status_code == 200
    assert resp.json()["permissions"] == ["audit_logs.view"]

    client.post(
        "/admin/admins", headers=auth_headers,
        json={"name": "Auditor One", "email": "auditor1@kalyan.com", "password": "auditor123", "role": "auditor"},
    )
    login = client.post("/admin/auth/login", json={"email": "auditor1@kalyan.com", "password": "auditor123"})
    auditor_headers = {"Authorization": f"Bearer {login.json()['token']}"}

    assert client.get("/admin/audit-logs", headers=auditor_headers).status_code == 200
    assert client.get("/admin/admins", headers=auditor_headers).status_code == 403


def test_set_permissions_rejects_unknown_code(client, auth_headers):
    resp = client.post("/admin/roles", headers=auth_headers, json={"slug": "temp", "name": "Temp"})
    role_id = resp.json()["id"]
    resp = client.put(f"/admin/roles/{role_id}/permissions", headers=auth_headers, json={"permission_codes": ["not.a.real.code"]})
    assert resp.status_code == 400


def test_disabled_admin_cannot_login(client, auth_headers):
    created = client.post(
        "/admin/admins",
        headers=auth_headers,
        json={"name": "Support One", "email": "support1@kalyan.com", "password": "support123", "role": "support"},
    ).json()
    client.patch(f"/admin/admins/{created['id']}", headers=auth_headers, json={"status": "disabled"})

    resp = client.post("/admin/auth/login", json={"email": "support1@kalyan.com", "password": "support123"})
    assert resp.status_code == 401
