from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def _market_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def _today() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()


def _declare_open(client, auth_headers, market_id, panna="123"):
    resp = client.post(
        "/admin/results",
        headers=auth_headers,
        json={"market_id": market_id, "date": _today(), "open_panna": panna, "publish": True},
    )
    assert resp.status_code == 201, resp.text


def _declare_close(client, auth_headers, market_id, panna="456"):
    resp = client.post(
        "/admin/results",
        headers=auth_headers,
        json={"market_id": market_id, "date": _today(), "close_panna": panna, "publish": True},
    )
    assert resp.status_code == 201, resp.text


def test_open_bet_blocked_once_open_result_declared_even_without_cutoff_time(client, auth_headers, user_headers):
    """No cutoff_time is configured on TESTGAME -- the Open leg should still stop
    itself automatically the instant today's Open result is published."""
    mid = _market_id(client, auth_headers)
    _declare_open(client, auth_headers, mid)

    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 10},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "CUTOFF_PASSED"


def test_close_bet_still_allowed_after_open_result_declared(client, auth_headers, user_headers):
    """Declaring the Open result must not block the still-pending Close leg."""
    mid = _market_id(client, auth_headers)
    _declare_open(client, auth_headers, mid)

    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE", "stage": "CLOSE", "value": "5", "credits": 10},
    )
    assert resp.status_code == 201


def test_close_bet_blocked_once_close_result_declared(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    _declare_open(client, auth_headers, mid)
    _declare_close(client, auth_headers, mid)

    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE", "stage": "CLOSE", "value": "5", "credits": 10},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "CUTOFF_PASSED"


def test_open_bet_allowed_before_any_result_declared(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 10},
    )
    assert resp.status_code == 201


def test_jodi_blocked_once_open_result_declared(client, auth_headers, user_headers):
    """Jodi always needs the Open number -- it must follow the Open leg's
    auto-cutoff regardless of what stage (if any) the client sends."""
    mid = _market_id(client, auth_headers)
    _declare_open(client, auth_headers, mid)

    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "JODI", "value": "16", "credits": 10},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "CUTOFF_PASSED"
