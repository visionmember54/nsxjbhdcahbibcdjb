from __future__ import annotations


def test_dashboard_exposes_active_today_withdrawal_and_starline_breakdowns(client, auth_headers):
    resp = client.get("/admin/dashboard", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    stats = resp.json()["stats"]

    for key in (
        "activeUsersToday", "signupsToday",
        "withdrawalsPending", "withdrawalsApproved",
        "depositsPending", "depositsApproved",
        "starlineOpenSlots", "starlineClosedSlots", "starlineTotalSlots",
        "openMarkets", "activeStarlineSlots",
    ):
        assert key in stats, f"missing {key}"
        assert isinstance(stats[key], int)

    assert stats["starlineOpenSlots"] + stats["starlineClosedSlots"] == stats["starlineTotalSlots"]
    assert resp.json()["today"]["activeUsers"] == stats["activeUsersToday"]


def test_dashboard_counts_open_and_pending_support_tickets(client, auth_headers, user_headers):
    resp = client.post(
        "/admin/users", headers=auth_headers,
        json={"name": "Second User", "phone": "9111111112", "email": "second2@example.com", "password": "seconduser123"},
    )
    assert resp.status_code == 201, resp.text
    second_token = client.post("/auth/login", json={"phone": "9111111112", "password": "seconduser123"}).json()["token"]
    second_headers = {"Authorization": f"Bearer {second_token}"}

    client.post("/api/v1/support/chat", headers=user_headers, json={"message": "need help"})
    reply_query = client.post("/api/v1/support/chat", headers=second_headers, json={"message": "second question"})
    query_id = reply_query.json()["data"]["sessionId"]
    client.post(f"/admin/queries/{query_id}/reply", headers=auth_headers, json={"message": "on it"})

    stats = client.get("/admin/dashboard", headers=auth_headers).json()["stats"]
    assert stats["openSupportTickets"] == 1
    assert stats["pendingSupportTickets"] == 1


def test_game_type_name_is_editable_via_patch(client, auth_headers):
    game_type = next(g for g in client.get("/admin/game-types", headers=auth_headers).json() if g["code"] == "SINGLE")
    resp = client.patch(
        f"/admin/game-types/{game_type['id']}", json={"name": "Single Digit"}, headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Single Digit"


def test_users_list_supports_joined_today_and_active_today_filters(client, auth_headers):
    resp = client.get("/admin/users?joined_today=true", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    resp = client.get("/admin/users?active_today=true", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 0
