from __future__ import annotations


def _testgame_id(client, auth_headers):
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def test_search_finds_user_by_name_phone_or_email(client, auth_headers):
    for q in ("Test User", "9000000000", "test@example.com", "test us"):
        resp = client.get("/admin/search", headers=auth_headers, params={"q": q})
        assert resp.status_code == 200, resp.text
        users = resp.json()["users"]
        assert any(u["name"] == "Test User" for u in users), f"query {q!r} found {users}"


def test_search_finds_market_by_partial_name(client, auth_headers):
    resp = client.get("/admin/search", headers=auth_headers, params={"q": "TESTGA"})
    assert resp.status_code == 200, resp.text
    markets = resp.json()["markets"]
    assert any(m["name"] == "TESTGAME" for m in markets)


def test_search_finds_bid_by_exact_numeric_id(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 10})
    entry_id = client.get("/admin/simulations?limit=1", headers=auth_headers).json()["items"][0]["id"]

    resp = client.get("/admin/search", headers=auth_headers, params={"q": str(entry_id)})
    assert resp.status_code == 200, resp.text
    bid = resp.json()["bid"]
    assert bid is not None
    assert bid["id"] == entry_id
    assert bid["marketName"] == "TESTGAME"
    assert bid["selection"] == "5"


def test_search_with_no_matches_returns_empty_lists(client, auth_headers):
    resp = client.get("/admin/search", headers=auth_headers, params={"q": "nonexistent-xyz"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["users"] == []
    assert data["markets"] == []
    assert data["bid"] is None


def test_search_requires_login(client):
    resp = client.get("/admin/search", params={"q": "test"})
    assert resp.status_code == 401
