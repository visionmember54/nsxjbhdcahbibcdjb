from __future__ import annotations


def _matka_id(client, auth_headers):
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def _dashboard_result(client, user_headers):
    items = client.get("/api/v1/home/dashboard", headers=user_headers).json()["data"]["markets"]
    return next(m for m in items if m["name"] == "TESTGAME")["result"]


def test_dashboard_shows_placeholder_when_no_result_published_yet(client, auth_headers, user_headers):
    assert _dashboard_result(client, user_headers) == "***-**-***"


def test_dashboard_shows_an_old_result_as_placeholder_not_stale_data(client, auth_headers, user_headers):
    """A result from a prior day must not keep showing in the home screen's
    'live' result badge once a new day starts -- it should read as 'no result
    yet today', not silently display yesterday's (or older) numbers."""
    mid = _matka_id(client, auth_headers)
    client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2020-01-01", "open_panna": "128", "close_panna": "600", "publish": True})

    assert _dashboard_result(client, user_headers) == "***-**-***"


def test_dashboard_shows_todays_result_once_published(client, auth_headers, user_headers):
    from app.services.app_api_service import today_ist

    mid = _matka_id(client, auth_headers)
    client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": today_ist().isoformat(), "open_panna": "128", "close_panna": "600", "publish": True})

    assert _dashboard_result(client, user_headers) == "128-16-600"
