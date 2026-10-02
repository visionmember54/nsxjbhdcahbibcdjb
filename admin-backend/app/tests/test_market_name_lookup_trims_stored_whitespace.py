from __future__ import annotations

from datetime import date


def _matka_category_id(client, auth_headers):
    categories = client.get("/admin/market-categories", headers=auth_headers).json()
    return next(c["id"] for c in categories if c["slug"] == "MATKA")


def _single_game_type_id(client, auth_headers):
    types = client.get("/admin/game-types", headers=auth_headers).json()
    return next(g["id"] for g in types if g["code"] == "SINGLE")


def _setup_trailing_space_market(client, auth_headers):
    """The real production bug: a market stored with a trailing space in its
    name (e.g. "SUPERME DAY "), looked up by a client that already trims its
    own input -- the exact scenario from the 404 report."""
    category_id = _matka_category_id(client, auth_headers)
    market = client.post(
        "/admin/markets", headers=auth_headers,
        json={"category_id": category_id, "name": "TRAILING SPACE TEST ", "slug": "trailing-space-test"},
    )
    assert market.status_code == 201, market.text
    market_id = market.json()["id"]
    assert market.json()["name"] == "TRAILING SPACE TEST "

    activate = client.post(f"/admin/markets/{market_id}/status", headers=auth_headers, json={"status": "OPEN"})
    assert activate.status_code == 200, activate.text

    game_type_id = _single_game_type_id(client, auth_headers)
    config = client.post(
        f"/admin/markets/{market_id}/game-type-configs", headers=auth_headers,
        json={"game_type_id": game_type_id, "stage": None},
    )
    assert config.status_code == 201, config.text

    rate = client.post(
        "/admin/rates", headers=auth_headers,
        json={"market_id": market_id, "game_type_id": game_type_id, "rate": 95, "effective_from": date(2020, 1, 1).isoformat()},
    )
    assert rate.status_code == 201, rate.text
    return market_id


def test_bet_by_market_name_resolves_despite_stored_trailing_space(client, auth_headers, user_headers):
    _setup_trailing_space_market(client, auth_headers)

    # The app already trims its own input before sending -- this is the exact
    # payload shape from the bug report.
    resp = client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={
            "marketName": "TRAILING SPACE TEST",
            "betType": "SINGLE DIGIT",
            "items": [{"number": "5", "points": 10}],
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True


def test_bet_by_market_name_also_resolves_if_client_sends_the_exact_trailing_space(client, auth_headers, user_headers):
    _setup_trailing_space_market(client, auth_headers)

    resp = client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={
            "marketName": "TRAILING SPACE TEST ",
            "betType": "SINGLE DIGIT",
            "items": [{"number": "6", "points": 10}],
        },
    )
    assert resp.status_code == 200, resp.text


def test_unknown_market_name_still_404s(client, user_headers):
    resp = client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={
            "marketName": "A MARKET THAT DOES NOT EXIST",
            "betType": "SINGLE DIGIT",
            "items": [{"number": "5", "points": 10}],
        },
    )
    assert resp.status_code == 404
