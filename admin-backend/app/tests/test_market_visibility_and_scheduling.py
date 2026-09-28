from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from app.tests.conftest import TestingSessionLocal
from app.models.market import Market


def _testgame_id(client, auth_headers) -> int:
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def _dashboard_market_ids(client, user_headers) -> list[str]:
    resp = client.get("/api/v1/home/dashboard", params={"marketType": "ALL"}, headers=user_headers)
    assert resp.status_code == 200, resp.text
    return [m["id"] for m in resp.json()["data"]["markets"]]


def _live_results_ids(client) -> list[str]:
    resp = client.get("/api/v1/markets/live-results")
    assert resp.status_code == 200, resp.text
    return [m["id"] for m in resp.json()["data"]["markets"]]


def _public_market_ids(client) -> list[int]:
    resp = client.get("/markets", params={"limit": 50})
    assert resp.status_code == 200, resp.text
    return [m["id"] for m in resp.json()["items"]]


# ---- Visibility toggle -------------------------------------------------------

def test_market_defaults_to_visible(client, auth_headers):
    mid = _testgame_id(client, auth_headers)
    market = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"][0]
    assert market["visible"] is True


def test_hiding_a_market_removes_it_from_every_app_facing_listing(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    assert str(mid) in _dashboard_market_ids(client, user_headers)
    assert str(mid) in _live_results_ids(client)
    assert mid in _public_market_ids(client)

    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"visible": False})
    assert resp.status_code == 200, resp.text
    assert resp.json()["visible"] is False

    assert str(mid) not in _dashboard_market_ids(client, user_headers)
    assert str(mid) not in _live_results_ids(client)
    assert mid not in _public_market_ids(client)


def test_hidden_market_still_manageable_by_admin(client, auth_headers):
    """The admin's own market list and single-market lookup must never be affected
    by visibility -- otherwise hiding a market would lock the admin out of the
    only screen that can un-hide it again."""
    mid = _testgame_id(client, auth_headers)
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"visible": False})

    admin_list_ids = [m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]]
    assert mid in admin_list_ids

    single = client.get(f"/markets/{mid}")
    assert single.status_code == 200
    assert single.json()["visible"] is False

    # And un-hiding brings it back everywhere.
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"visible": True})
    assert mid in _public_market_ids(client)


# ---- Day-of-week scheduling (active_days) ------------------------------------

def test_active_days_rejects_a_non_scheduled_weekday(client, auth_headers):
    mid = _testgame_id(client, auth_headers)
    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"active_days": ["SAT", "SUN"]})
    assert resp.status_code == 200, resp.text
    assert sorted(resp.json()["active_days"]) == ["SAT", "SUN"]

    db = TestingSessionLocal()
    market = db.get(Market, mid)
    from app.services.market_service import effective_market_status

    # 2026-09-28 is a Monday -- not scheduled.
    with patch("app.services.market_service.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 9, 28, 12, 0)
        assert effective_market_status(market) == "CLOSED"

    # 2026-10-03 is a Saturday -- scheduled, falls back to the normal (stored-status) logic.
    with patch("app.services.market_service.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 10, 3, 12, 0)
        assert effective_market_status(market) == "OPEN"
    db.close()


def test_active_days_blocks_betting_on_an_off_day(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"active_days": ["SAT"]})

    with patch("app.services.market_service.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 9, 28, 12, 0)  # Monday
        resp = client.post(
            "/api/v1/bets/place", headers=user_headers,
            json={"marketId": str(mid), "betType": "SINGLE DIGIT", "session": "OPEN", "items": [{"number": "5", "points": 10}]},
        )
    assert resp.status_code == 400 and resp.json()["error"] == "MARKET_CLOSED"


def test_clearing_active_days_runs_every_day_again(client, auth_headers):
    mid = _testgame_id(client, auth_headers)
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"active_days": ["SAT"]})
    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"active_days": []})
    assert resp.status_code == 200
    assert resp.json()["active_days"] is None


def test_unknown_weekday_code_is_rejected(client, auth_headers):
    mid = _testgame_id(client, auth_headers)
    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"active_days": ["FUNDAY"]})
    assert resp.status_code == 422


# ---- Game type / status filters on admin simulations -------------------------

def test_admin_simulations_filters_by_game_type(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={"marketId": str(mid), "betType": "SINGLE DIGIT", "session": "OPEN", "items": [{"number": "5", "points": 10}]},
    )
    client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={"marketId": str(mid), "betType": "JODI DIGIT", "items": [{"number": "45", "points": 10}]},
    )

    jodi_only = client.get("/admin/simulations", headers=auth_headers, params={"game_type": "jodi"}).json()["items"]
    assert jodi_only and all(e["gameType"] == "JODI" for e in jodi_only)

    single_only = client.get("/admin/simulations", headers=auth_headers, params={"game_type": "SINGLE"}).json()["items"]
    assert single_only and all(e["gameType"] == "SINGLE" for e in single_only)


def test_admin_simulations_filters_by_status(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={"marketId": str(mid), "betType": "SINGLE DIGIT", "session": "OPEN", "items": [{"number": "5", "points": 10}]},
    )
    pending = client.get("/admin/simulations", headers=auth_headers, params={"status_filter": "pending"}).json()["items"]
    assert pending and all(e["status"] == "Pending" for e in pending)

    won = client.get("/admin/simulations", headers=auth_headers, params={"status_filter": "Won"}).json()["items"]
    assert won == []
