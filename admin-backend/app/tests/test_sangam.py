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


def test_sangam_validators_require_canonical_shape_and_half_variant(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    _enable_sangam(market_id)

    no_variant = client.post("/simulations", headers=user_headers, json={"market_id": market_id, "game_type": "HALF_SANGAM", "value": "128-1", "credits": 10})
    assert no_variant.status_code == 400
    malformed = client.post("/simulations", headers=user_headers, json={"market_id": market_id, "game_type": "FULL_SANGAM", "value": "128-1", "credits": 10})
    assert malformed.status_code == 400


def test_sangam_resolves_only_when_open_and_close_are_published(client, auth_headers, user_headers):
    market_id = _market_id(client, auth_headers)
    _enable_sangam(market_id)
    selections = [
        {"game_type": "HALF_SANGAM", "value": "128-1", "game_variant": "OPEN_PANNA_CLOSE_ANK"},
        {"game_type": "HALF_SANGAM", "value": "470-1", "game_variant": "OPEN_ANK_CLOSE_PANNA"},
        {"game_type": "FULL_SANGAM", "value": "128-470"},
    ]
    for selection in selections:
        response = client.post("/simulations", headers=user_headers, json={"market_id": market_id, "credits": 10, **selection})
        assert response.status_code == 201, response.text

    client.post("/admin/results", headers=auth_headers, json={"market_id": market_id, "date": "2026-02-01", "open_panna": "128", "publish": True})
    pending = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    assert all(entry["status"] == "Pending" for entry in pending)

    client.post("/admin/results", headers=auth_headers, json={"market_id": market_id, "date": "2026-02-01", "close_panna": "470", "publish": True})
    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    assert {entry["status"] for entry in entries} == {"Won"}
    assert {entry["gameVariant"] for entry in entries if entry["gameType"] == "HALF_SANGAM"} == {"OPEN_PANNA_CLOSE_ANK", "OPEN_ANK_CLOSE_PANNA"}
