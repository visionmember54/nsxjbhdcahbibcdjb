from __future__ import annotations


def _testgame_id(client, auth_headers):
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def _second_market_id(client, auth_headers):
    categories = client.get("/admin/market-categories", headers=auth_headers).json()
    matka_id = next(c["id"] for c in categories if c["slug"] == "MATKA")
    resp = client.post(
        "/admin/markets", headers=auth_headers,
        json={"category_id": matka_id, "name": "TESTGAME TWO", "slug": "testgame-two"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _single_game_type_id(client, auth_headers):
    gts = client.get("/admin/game-types", headers=auth_headers).json()
    return next(g["id"] for g in gts if g["code"] == "SINGLE")


def test_bulk_rate_creates_one_rate_per_market(client, auth_headers):
    mid1 = _testgame_id(client, auth_headers)
    mid2 = _second_market_id(client, auth_headers)
    gt_id = _single_game_type_id(client, auth_headers)

    resp = client.post(
        "/admin/rates/bulk", headers=auth_headers,
        json={"market_ids": [mid1, mid2], "game_type_id": gt_id, "rate": 1000, "effective_from": "2020-01-01"},
    )
    assert resp.status_code == 201, resp.text
    rows = resp.json()
    assert {r["market_id"] for r in rows} == {mid1, mid2}
    assert all(r["rate"] == 1000 for r in rows)
    assert all(r["status"] == "Active" for r in rows)

    rates_mid1 = client.get(f"/admin/rates?market_id={mid1}", headers=auth_headers).json()
    assert any(r["rate"] == 1000 for r in rates_mid1)


def test_bulk_rate_rejects_unknown_market(client, auth_headers):
    mid1 = _testgame_id(client, auth_headers)
    gt_id = _single_game_type_id(client, auth_headers)
    resp = client.post(
        "/admin/rates/bulk", headers=auth_headers,
        json={"market_ids": [mid1, 999999], "game_type_id": gt_id, "rate": 95, "effective_from": "2020-01-01"},
    )
    assert resp.status_code == 404


def test_bulk_game_type_config_creates_where_missing(client, auth_headers):
    mid1 = _testgame_id(client, auth_headers)
    mid2 = _second_market_id(client, auth_headers)
    gt_id = _single_game_type_id(client, auth_headers)

    resp = client.post(
        "/admin/game-type-configs/bulk", headers=auth_headers,
        json={"market_ids": [mid1, mid2], "game_type_id": gt_id, "stage": "CLOSE", "min_credits": 20, "max_credits": 5000},
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert {r["market_id"] for r in rows} == {mid1, mid2}
    assert all(r["min_credits"] == 20 and r["max_credits"] == 5000 for r in rows)

    configs_mid2 = client.get(f"/admin/markets/{mid2}/game-type-configs", headers=auth_headers).json()
    assert any(c["game_type_code"] == "SINGLE" and c["stage"] == "CLOSE" and c["min_credits"] == 20 for c in configs_mid2)


def test_bulk_game_type_config_updates_existing_in_place_not_duplicated(client, auth_headers):
    mid1 = _testgame_id(client, auth_headers)
    gt_id = _single_game_type_id(client, auth_headers)

    # TESTGAME already has a SINGLE/OPEN config from the base seed -- bulk-applying
    # the same (game_type, stage) must update it, not create a second row.
    before = client.get(f"/admin/markets/{mid1}/game-type-configs", headers=auth_headers).json()
    before_count = len([c for c in before if c["game_type_code"] == "SINGLE" and c["stage"] == "OPEN"])
    assert before_count == 1

    resp = client.post(
        "/admin/game-type-configs/bulk", headers=auth_headers,
        json={"market_ids": [mid1], "game_type_id": gt_id, "stage": "OPEN", "min_credits": 50, "max_credits": 2000},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()[0]["min_credits"] == 50

    after = client.get(f"/admin/markets/{mid1}/game-type-configs", headers=auth_headers).json()
    matching = [c for c in after if c["game_type_code"] == "SINGLE" and c["stage"] == "OPEN"]
    assert len(matching) == 1
    assert matching[0]["min_credits"] == 50


def test_bulk_game_type_config_rejects_unknown_market(client, auth_headers):
    gt_id = _single_game_type_id(client, auth_headers)
    resp = client.post(
        "/admin/game-type-configs/bulk", headers=auth_headers,
        json={"market_ids": [999999], "game_type_id": gt_id, "stage": "OPEN"},
    )
    assert resp.status_code == 404
