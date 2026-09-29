from __future__ import annotations

from app.models.simulation import SimulationEntry
from app.tests.conftest import TestingSessionLocal


def _testgame_id(client, auth_headers) -> int:
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def _place(client, user_headers, mid, bet_type, **extra):
    return client.post(
        "/api/v1/bets/place", headers=user_headers,
        json={"marketId": str(mid), "betType": bet_type, "items": [{"number": extra.pop("number", "5"), "points": extra.pop("points", 10)}], **extra},
    )


def _latest_entry(client, auth_headers):
    return client.get("/admin/simulations?limit=1", headers=auth_headers).json()["items"][0]


def test_bid_history_shows_user_and_market_name(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "SINGLE DIGIT", session="OPEN")
    entry = _latest_entry(client, auth_headers)
    assert entry["userName"] == "Test User"
    assert entry["marketName"] == "TESTGAME"


def test_single_digit_open_and_close_land_in_correct_columns(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "SINGLE DIGIT", session="OPEN", number="5")
    entry = _latest_entry(client, auth_headers)
    assert (entry["openDigit"], entry["closeDigit"], entry["openPaana"], entry["closePaana"]) == ("5", None, None, None)

    _place(client, user_headers, mid, "SINGLE DIGIT", session="CLOSE", number="7")
    entry = _latest_entry(client, auth_headers)
    assert (entry["openDigit"], entry["closeDigit"]) == (None, "7")


def test_jodi_splits_into_open_and_close_digit(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "JODI DIGIT", number="45")
    entry = _latest_entry(client, auth_headers)
    assert (entry["openDigit"], entry["closeDigit"]) == ("4", "5")


def test_panna_lands_in_paana_columns_by_session(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "SINGLE PANA", session="OPEN", number="128")
    entry = _latest_entry(client, auth_headers)
    assert entry["openPaana"] == "128" and entry["closePaana"] is None


def test_edit_pending_bid_corrects_selection_credits_and_balance(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "SINGLE DIGIT", session="OPEN", number="5", points=10)
    entry = _latest_entry(client, auth_headers)
    balance_before = client.get("/admin/users/" + str(entry["userId"]), headers=auth_headers).json()["balance"]

    resp = client.patch(f"/admin/simulations/{entry['id']}", headers=auth_headers, json={"selection": "9", "credits": 20})
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["selection"] == "9"
    assert updated["simulatedCredits"] == 20
    assert updated["simulatedReturn"] == updated["simulatedRate"] * 20 // 10

    balance_after = client.get("/admin/users/" + str(entry["userId"]), headers=auth_headers).json()["balance"]
    assert balance_after == balance_before - 10  # charged 10 more credits


def test_edit_rejects_invalid_selection_shape(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "SINGLE DIGIT", session="OPEN", number="5")
    entry = _latest_entry(client, auth_headers)
    resp = client.patch(f"/admin/simulations/{entry['id']}", headers=auth_headers, json={"selection": "55", "credits": 10})
    assert resp.status_code == 400


def test_edit_rejects_once_resolved(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "SINGLE DIGIT", session="OPEN", number="5")
    entry = _latest_entry(client, auth_headers)

    db = TestingSessionLocal()
    db.query(SimulationEntry).filter(SimulationEntry.id == entry["id"]).update({"status": "Won"})
    db.commit()
    db.close()

    resp = client.patch(f"/admin/simulations/{entry['id']}", headers=auth_headers, json={"selection": "9", "credits": 10})
    assert resp.status_code == 400


def test_simulations_date_filter(client, auth_headers, user_headers):
    mid = _testgame_id(client, auth_headers)
    _place(client, user_headers, mid, "SINGLE DIGIT", session="OPEN", number="5")
    today = client.get("/admin/dashboard", headers=auth_headers).json()["today"]["date"]
    todays = client.get("/admin/simulations", headers=auth_headers, params={"date": today}).json()["items"]
    assert todays

    other_day = client.get("/admin/simulations", headers=auth_headers, params={"date": "2020-01-01"}).json()["items"]
    assert other_day == []
