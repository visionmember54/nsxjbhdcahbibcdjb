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
