from __future__ import annotations


def _user_id(client, auth_headers):
    users = client.get("/admin/users?limit=10", headers=auth_headers).json()["items"]
    return users[0]["id"]


def test_grant_updates_balance_and_ledger(client, auth_headers):
    sid = _user_id(client, auth_headers)
    resp = client.post(f"/admin/users/{sid}/credits/grant", headers=auth_headers, json={"amount": 500, "note": "bonus"})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 1500  # 1000 seeded + 500

    history = client.get(f"/admin/users/{sid}/credits/history", headers=auth_headers).json()
    assert history["items"][0]["amount"] == 500
    assert history["items"][0]["type"] == "grant"


def test_adjustment_below_zero_rejected(client, auth_headers):
    sid = _user_id(client, auth_headers)
    resp = client.post(f"/admin/users/{sid}/credits/adjust", headers=auth_headers, json={"amount": -99999, "note": "test overdraw"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "INSUFFICIENT_LEARNING_CREDITS"

    users = client.get("/admin/users?limit=10", headers=auth_headers).json()["items"]
    assert next(s for s in users if s["id"] == sid)["balance"] == 1000  # unchanged


def test_reset_computes_correct_delta(client, auth_headers):
    sid = _user_id(client, auth_headers)
    resp = client.post(f"/admin/users/{sid}/credits/reset", headers=auth_headers, json={"new_balance": 250, "note": "reset for testing"})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 250

    history = client.get(f"/admin/users/{sid}/credits/history", headers=auth_headers).json()
    assert history["items"][0]["amount"] == -750  # 250 - 1000
    assert history["items"][0]["balanceAfter"] == 250


def test_grant_without_note_rejected(client, auth_headers):
    sid = _user_id(client, auth_headers)
    resp = client.post(f"/admin/users/{sid}/credits/grant", headers=auth_headers, json={"amount": 500})
    assert resp.status_code == 422
