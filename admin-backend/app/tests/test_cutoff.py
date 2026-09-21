from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _market_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def _future_time_same_day(zone: str, minutes_ahead: int = 60) -> str:
    """cutoff_time is a bare time-of-day (no date), so a naive now+1h can
    wrap past midnight and alias to an earlier clock time than 'now'. Clamp to
    end-of-day so the derived cutoff is always unambiguously later today."""
    now = datetime.now(ZoneInfo(zone))
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return min(now + timedelta(minutes=minutes_ahead), end_of_day).time().isoformat()


def test_cutoff_passed_blocks_submission(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    past_cutoff = (datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=1)).time().isoformat()
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"cutoff_time": past_cutoff})

    resp = client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "value": "16", "credits": 10})
    assert resp.status_code == 400
    assert resp.json()["error"] == "CUTOFF_PASSED"


def test_cutoff_not_yet_passed_allows_submission(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    future_cutoff = _future_time_same_day("Asia/Kolkata")
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"cutoff_time": future_cutoff})

    resp = client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "value": "16", "credits": 10})
    assert resp.status_code == 201


def test_no_cutoff_configured_does_not_block(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    resp = client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "value": "16", "credits": 10})
    assert resp.status_code == 201
