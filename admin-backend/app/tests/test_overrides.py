from __future__ import annotations


def _market_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def _lost_entry(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "1", "credits": 100})
    client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-02-01", "open_panna": "222", "publish": True})  # ank=6, so "1" loses
    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    entry = next(e for e in entries if e["selection"] == "1")
    assert entry["status"] == "Lost"
    return entry


def test_override_flips_outcome_and_pays_out_without_touching_market_result(client, auth_headers, user_headers):
    entry = _lost_entry(client, auth_headers, user_headers)
    result_before = client.get("/admin/results?limit=50", headers=auth_headers).json()["items"][0]
    balance_before = client.get("/auth/me", headers=user_headers).json()["balance"]

    resp = client.post(
        f"/admin/simulations/{entry['id']}/override", headers=auth_headers,
        json={"outcome": "Won", "reason": "Educational demonstration"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "Won"
    assert body["originalStatus"] == "Lost"
    assert body["overrideStatus"] == "OVERRIDDEN"
    assert body["overrideReason"] == "Educational demonstration"

    balance_after = client.get("/auth/me", headers=user_headers).json()["balance"]
    assert balance_after == balance_before + entry["simulatedReturn"]

    result_after = client.get("/admin/results?limit=50", headers=auth_headers).json()["items"][0]
    assert result_after == result_before  # underlying market result is untouched


def test_override_without_reason_rejected(client, auth_headers, user_headers):
    entry = _lost_entry(client, auth_headers, user_headers)
    resp = client.post(f"/admin/simulations/{entry['id']}/override", headers=auth_headers, json={"outcome": "Won"})
    assert resp.status_code == 422


def test_override_requires_admin_permission(client, auth_headers, user_headers):
    entry = _lost_entry(client, auth_headers, user_headers)
    client.post(
        "/admin/admins", headers=auth_headers,
        json={"name": "Manager", "email": "override-manager@kalyan.com", "password": "manager123", "role": "manager"},
    )
    login = client.post("/admin/auth/login", json={"email": "override-manager@kalyan.com", "password": "manager123"})
    manager_headers = {"Authorization": f"Bearer {login.json()['token']}"}

    resp = client.post(
        f"/admin/simulations/{entry['id']}/override", headers=manager_headers,
        json={"outcome": "Won", "reason": "Educational demonstration"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "UNAUTHORIZED_OVERRIDE"


def test_override_of_pending_simulation_rejected(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "CLOSE", "value": "1", "credits": 10})
    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    entry = next(e for e in entries if e["stage"] == "CLOSE")
    assert entry["status"] == "Pending"

    resp = client.post(
        f"/admin/simulations/{entry['id']}/override", headers=auth_headers,
        json={"outcome": "Won", "reason": "Educational demonstration"},
    )
    assert resp.status_code == 400
