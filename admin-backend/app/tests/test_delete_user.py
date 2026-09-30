from __future__ import annotations


def _testgame_id(client, auth_headers) -> int:
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def _user_id(client, auth_headers, phone: str) -> int:
    return next(u["id"] for u in client.get("/admin/users?limit=50", headers=auth_headers).json()["items"] if u["phone"] == phone)


def test_delete_user_removes_account_and_frees_phone_for_resignup(client, auth_headers, user_headers):
    uid = _user_id(client, auth_headers, "9000000000")

    resp = client.delete(f"/admin/users/{uid}", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    assert client.get(f"/admin/users/{uid}", headers=auth_headers).status_code == 404

    # Same phone number can register fresh again.
    register = client.post(
        "/api/v1/auth/register",
        json={"name": "Fresh Satish", "phone": "9000000000", "password": "brandnew123", "otpSessionId": "otp_reg_direct", "otp": "1234"},
    )
    assert register.status_code == 201, register.text


def test_delete_user_cascades_bids_and_wallet_history(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={"marketId": str(mid), "betType": "SINGLE DIGIT", "session": "OPEN", "items": [{"number": "5", "points": 10}]},
    )
    uid = _user_id(client, auth_headers, "9000000000")

    resp = client.delete(f"/admin/users/{uid}", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    remaining = client.get("/admin/simulations", headers=auth_headers, params={"user_id": uid}).json()["items"]
    assert remaining == []


def test_delete_user_404_for_unknown_id(client, auth_headers):
    resp = client.delete("/admin/users/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_user_preserves_audit_log_but_clears_subject_link(client, auth_headers, user_headers):
    uid = _user_id(client, auth_headers, "9000000000")
    client.post(f"/admin/users/{uid}/reset-password", headers=auth_headers)

    resp = client.delete(f"/admin/users/{uid}", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    logs = client.get("/admin/audit-logs?limit=50", headers=auth_headers).json()["items"]
    reset_entry = next(l for l in logs if l["action"] == "user_password_reset")
    assert reset_entry["subjectUserId"] is None
    delete_entry = next(l for l in logs if l["action"] == "user_deleted")
    assert "9000000000" in delete_entry["details"]
