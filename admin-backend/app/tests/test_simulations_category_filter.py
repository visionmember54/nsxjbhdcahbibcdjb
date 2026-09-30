from __future__ import annotations

from datetime import date


def _testgame_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def _single_game_type_id(client, auth_headers):
    types = client.get("/admin/game-types", headers=auth_headers).json()
    return next(g["id"] for g in types if g["code"] == "SINGLE")


def _setup_starline_market(client, auth_headers):
    cat = client.post("/admin/market-categories", headers=auth_headers, json={"slug": "STARLINE", "name": "Starline", "display_order": 2})
    assert cat.status_code == 201, cat.text
    category_id = cat.json()["id"]

    market = client.post(
        "/admin/markets", headers=auth_headers,
        json={"category_id": category_id, "name": "STARLINE-TEST", "slug": "starline-test"},
    )
    assert market.status_code == 201, market.text
    market_id = market.json()["id"]

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


def test_category_filter_separates_main_market_from_starline(client, auth_headers, user_headers):
    matka_id = _testgame_id(client, auth_headers)
    starline_id = _setup_starline_market(client, auth_headers)

    resp = client.post("/simulations", headers=user_headers, json={"market_id": matka_id, "game_type": "JODI", "value": "16", "credits": 10})
    assert resp.status_code == 201, resp.text
    resp = client.post("/simulations", headers=user_headers, json={"market_id": starline_id, "game_type": "SINGLE", "value": "5", "credits": 10})
    assert resp.status_code == 201, resp.text

    matka_only = client.get("/admin/simulations?category=MATKA", headers=auth_headers).json()
    assert matka_only["total"] == 1
    assert matka_only["items"][0]["marketId"] == matka_id
    assert matka_only["items"][0]["marketCategory"] == "MATKA"

    starline_only = client.get("/admin/simulations?category=STARLINE", headers=auth_headers).json()
    assert starline_only["total"] == 1
    assert starline_only["items"][0]["marketId"] == starline_id
    assert starline_only["items"][0]["marketCategory"] == "STARLINE"

    everything = client.get("/admin/simulations", headers=auth_headers).json()
    assert everything["total"] == 2
