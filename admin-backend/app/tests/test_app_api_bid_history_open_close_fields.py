from __future__ import annotations

from datetime import date

from app.models.game_type import GameType, GameTypeConfig
from app.models.rate import Rate
from app.tests.conftest import TestingSessionLocal


def _market_id(client, auth_headers):
    return client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"][0]["id"]


def _enable_sangam(market_id: int) -> None:
    db = TestingSessionLocal()
    try:
        half = GameType(code="HALF_SANGAM", name="Half Sangam", digit_length=5, classification_rule="SANGAM_HALF")
        full = GameType(code="FULL_SANGAM", name="Full Sangam", digit_length=7, classification_rule="SANGAM_FULL")
        db.add_all([half, full])
        db.flush()
        for game_type in [half, full]:
            db.add(GameTypeConfig(market_id=market_id, game_type_id=game_type.id, stage="BOTH"))
            db.add(Rate(market_id=market_id, game_type_id=game_type.id, rate=95, effective_from=date(2020, 1, 1), status="Active"))
        db.commit()
    finally:
        db.close()


def _bid_for(client, user_headers, selection):
    bids = client.get("/api/v1/history/bids", headers=user_headers, params={"limit": 50}).json()["data"]["bids"]
    return next(b for b in bids if b["selection"] == selection)


def test_jodi_bid_history_includes_open_and_close_digit(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    resp = client.post("/simulations", headers=user_headers, json={"market_id": market_id, "game_type": "JODI", "value": "16", "credits": 10})
    assert resp.status_code == 201, resp.text

    bid = _bid_for(client, user_headers, "16")
    assert bid["openDigit"] == "1"
    assert bid["closeDigit"] == "6"
    assert bid["openPana"] is None
    assert bid["closePana"] is None


def test_half_sangam_bid_history_includes_open_panna_and_close_digit(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    _enable_sangam(market_id)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": market_id, "game_type": "HALF_SANGAM", "value": "128-1", "game_variant": "OPEN_PANNA_CLOSE_ANK", "credits": 10},
    )
    assert resp.status_code == 201, resp.text

    bid = _bid_for(client, user_headers, "128-1")
    assert bid["openPana"] == "128"
    assert bid["closeDigit"] == "1"
    assert bid["openDigit"] is None
    assert bid["closePana"] is None
    assert bid["stage"] == "CLOSE"  # open panna + close digit is the "Close" half sangam bet


def test_half_sangam_other_variant_includes_open_digit_and_close_panna(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    _enable_sangam(market_id)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": market_id, "game_type": "HALF_SANGAM", "value": "470-1", "game_variant": "OPEN_ANK_CLOSE_PANNA", "credits": 10},
    )
    assert resp.status_code == 201, resp.text

    bid = _bid_for(client, user_headers, "470-1")
    assert bid["openDigit"] == "1"
    assert bid["closePana"] == "470"
    assert bid["stage"] == "OPEN"  # open digit + close panna is the "Open" half sangam bet


def test_full_sangam_bid_history_includes_open_and_close_panna(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    _enable_sangam(market_id)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": market_id, "game_type": "FULL_SANGAM", "value": "128-470", "credits": 10},
    )
    assert resp.status_code == 201, resp.text

    bid = _bid_for(client, user_headers, "128-470")
    assert bid["openPana"] == "128"
    assert bid["closePana"] == "470"
    assert bid["openDigit"] is None
    assert bid["closeDigit"] is None


def test_single_panna_bid_history_splits_by_stage(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": market_id, "game_type": "SINGLE_PANNA", "stage": "OPEN", "value": "128", "credits": 10},
    )
    assert resp.status_code == 201, resp.text

    bid = _bid_for(client, user_headers, "128")
    assert bid["openPana"] == "128"
    assert bid["closePana"] is None


def test_plain_single_bid_history_splits_by_stage(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    resp = client.post(
        "/simulations", headers=user_headers,
        json={"market_id": market_id, "game_type": "SINGLE", "stage": "OPEN", "value": "7", "credits": 10},
    )
    assert resp.status_code == 201, resp.text

    bid = _bid_for(client, user_headers, "7")
    assert bid["openDigit"] == "7"
    assert bid["closeDigit"] is None
