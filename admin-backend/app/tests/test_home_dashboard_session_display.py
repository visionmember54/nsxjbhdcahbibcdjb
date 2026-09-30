from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _market_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def _market_item(client, user_headers, name="TESTGAME"):
    resp = client.get("/api/v1/home/dashboard", params={"marketType": "ALL"}, headers=user_headers)
    assert resp.status_code == 200, resp.text
    return next(m for m in resp.json()["data"]["markets"] if m["name"] == name)


def test_close_only_window_still_reports_as_the_green_opening_flag(client, auth_headers, user_headers):
    """Open time has passed but Close hasn't -- only the Close leg is biddable.
    The app has one visual "Play" (green) state driven off isOpeningLive, and a
    separate gold "closing" look driven off isClosingLive that reads as closed
    to users -- so this must surface as isOpeningLive=True, not isClosingLive."""
    mid = _market_id(client, auth_headers)
    past = (datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=1)).time().isoformat()
    future = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(hours=1)).time().isoformat()
    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"opening_time": past, "closing_time": future})
    assert resp.status_code == 200, resp.text

    item = _market_item(client, user_headers)
    assert item["isOpeningLive"] is True
    assert item["isClosingLive"] is False
    assert item["isBiddingAllowed"] is True
    assert item["sessionStatus"] == "OPENING"


def test_both_legs_live_still_reports_as_opening(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    past = (datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=1)).time().isoformat()
    future = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(hours=2)).time().isoformat()
    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"opening_time": future, "closing_time": future})
    assert resp.status_code == 200, resp.text
    # opening_time in the future -> not live yet; flip opening_time to the past instead.
    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"opening_time": past})
    assert resp.status_code == 200, resp.text

    item = _market_item(client, user_headers)
    assert item["isOpeningLive"] is True
    assert item["isClosingLive"] is False
    assert item["isBiddingAllowed"] is True


def test_fully_closed_market_is_unaffected(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    past = (datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=2)).time().isoformat()
    just_past = (datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=1)).time().isoformat()
    resp = client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"opening_time": past, "closing_time": just_past})
    assert resp.status_code == 200, resp.text

    item = _market_item(client, user_headers)
    assert item["isOpeningLive"] is False
    assert item["isClosingLive"] is False
    assert item["isBiddingAllowed"] is False
    assert item["sessionStatus"] == "CLOSED_TODAY"


def test_actual_bet_cutoff_enforcement_is_unaffected_by_the_display_remap(client, auth_headers, user_headers):
    """The display remap must not loosen real bet validation -- an Open-stage bet
    must still be rejected once Open time has passed, even though the dashboard
    now reports isOpeningLive=True for the still-live Close leg."""
    mid = _market_id(client, auth_headers)
    past = (datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=1)).time().isoformat()
    future = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(hours=1)).time().isoformat()
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"opening_time": past, "closing_time": future})

    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 10},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "CUTOFF_PASSED"

    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE", "stage": "CLOSE", "value": "5", "credits": 10},
    )
    assert resp.status_code == 201
