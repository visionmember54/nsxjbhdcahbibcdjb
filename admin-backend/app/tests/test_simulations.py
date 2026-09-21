from __future__ import annotations


def _market_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def test_single_simulation_deducts_balance(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    resp = client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "value": "16", "credits": 100})
    assert resp.status_code == 201
    assert resp.json()["remainingBalance"] == 900


def test_invalid_selection_shape_rejected(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    resp = client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "value": "5", "credits": 10})
    assert resp.status_code == 400


def test_panna_classification_mismatch_rejected(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE_PANNA", "stage": "OPEN", "value": "112", "credits": 10},
    )
    assert resp.status_code == 400


def test_bulk_batch_exceeding_balance_is_fully_rejected(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    selections = [{"value": f"{i:02d}", "credits": 400} for i in range(5)]  # 2000 > 1000 balance
    resp = client.post("/simulations/bulk", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "selections": selections})
    assert resp.status_code == 400

    mine = client.get("/simulations/my?limit=1", headers=user_headers).json()
    assert mine["total"] == 0


def test_bulk_batch_valid_creates_n_entries_and_one_ledger_row(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    selections = [{"value": f"{i:02d}", "credits": 50} for i in range(5)]
    resp = client.post("/simulations/bulk", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "selections": selections})
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["entries"]) == 5
    assert body["totalCredits"] == 250
    assert body["remainingBalance"] == 750

    mine = client.get("/simulations/my?limit=1", headers=user_headers).json()
    assert mine["total"] == 5


def test_bulk_rejects_batch_when_one_entry_invalid(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    selections = [{"value": "01", "credits": 10}, {"value": "999", "credits": 10}]
    resp = client.post("/simulations/bulk", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "selections": selections})
    assert resp.status_code == 400
    mine = client.get("/simulations/my?limit=1", headers=user_headers).json()
    assert mine["total"] == 0


def test_disabled_game_type_config_rejects_submission(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": mid, "game_type": "SINGLE_PANNA", "stage": "CLOSE", "value": "123", "credits": 10},
    )
    assert resp.status_code == 400  # only OPEN is configured for SINGLE_PANNA on this market
