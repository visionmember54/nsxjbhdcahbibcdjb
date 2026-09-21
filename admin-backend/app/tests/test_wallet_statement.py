from __future__ import annotations

import pytest

from app.models.market import Market, MarketCategory
from app.tests.conftest import TestingSessionLocal


@pytest.fixture(autouse=True)
def _gali_category():
    db = TestingSessionLocal()
    db.add(MarketCategory(slug="GALI_DISAWAR", name="Gali – Disawar", display_order=3))
    db.add(MarketCategory(slug="STARLINE", name="Starline", display_order=2))
    db.commit()
    db.close()


def _statement(client, headers, **params):
    resp = client.get("/api/v1/wallet/statement", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["transactions"]


def _play_and_win(client, auth_headers, user_headers):
    mid = next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")
    uid = client.get("/auth/me", headers=user_headers).json()["id"]
    client.post(f"/admin/users/{uid}/credits/grant", headers=auth_headers, json={"amount": 50, "note": "bonus"})
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 100})
    client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-02", "open_panna": "500", "publish": True})


def test_payout_lands_in_wallet_after_publish(client, auth_headers, user_headers):
    _play_and_win(client, auth_headers, user_headers)
    kinds = {t["title"] for t in _statement(client, user_headers)}
    assert {"Bet Placed", "Bet Won"} <= kinds


def test_market_type_filters_statement(client, auth_headers, user_headers):
    _play_and_win(client, auth_headers, user_headers)
    everything = _statement(client, user_headers, marketType="ALL")
    regular = _statement(client, user_headers, marketType="regular")
    assert {t["title"] for t in regular} == {"Bet Placed", "Bet Won"}  # grant has no market, so it is excluded
    assert len(everything) > len(regular)
    assert _statement(client, user_headers, marketType="GALI_DISAWAR") == []
    assert _statement(client, user_headers, marketType="STARLINE") == []


def test_market_type_combines_with_transaction_type(client, auth_headers, user_headers):
    _play_and_win(client, auth_headers, user_headers)
    debits = _statement(client, user_headers, marketType="REGULAR", transaction_type="DEBIT")
    assert [t["title"] for t in debits] == ["Bet Placed"]


def test_invalid_market_type_rejected(client, user_headers):
    resp = client.get("/api/v1/wallet/statement", params={"marketType": "nope"}, headers=user_headers)
    assert resp.status_code == 400


def test_market_chart_with_published_results(client, auth_headers):
    mid = next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")
    client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-05", "open_panna": "500", "publish": True})
    resp = client.get(f"/api/v1/markets/{mid}/chart", params={"year": 2026})
    assert resp.status_code == 200, resp.text
    week = resp.json()["data"]["records"][0]
    assert week["weekStartDate"] == "2026-01-05" and week["days"]["MON"]["openPana"] == "500"


def _market_id(client, auth_headers):
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def test_bet_appears_instantly_with_details(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 100})
    rows = _statement(client, user_headers)  # no result published yet
    assert len(rows) == 1
    row = rows[0]
    assert (row["kind"], row["title"], row["type"], row["amount"]) == ("BET_PLACED", "Bet Placed", "DEBIT", 100)
    assert row["transactionId"].startswith("SIM-") and row["gameType"] == "SINGLE"
    assert row["market"]["name"] == "TESTGAME" and row["market"]["marketType"] == "MATKA"
    assert row["bets"] == [{"number": "5", "points": 100, "status": "PENDING"}]
    assert "5 (100)" in row["description"] and "TESTGAME" in row["description"]


def test_each_number_gets_its_own_wallet_row(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    selections = [{"value": f"{i:02d}", "credits": 50} for i in range(3)]
    client.post("/simulations/bulk", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "selections": selections})
    rows = _statement(client, user_headers)
    assert [r["kind"] for r in rows] == ["BET_PLACED"] * 3
    assert sorted(r["bets"][0]["number"] for r in rows) == ["00", "01", "02"]
    assert {r["amount"] for r in rows} == {50} and len({r["transactionId"] for r in rows}) == 1
    assert sorted(r["balanceAfter"] for r in rows) == [850, 900, 950]  # running balance after each bid


def test_batch_over_balance_writes_no_rows(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    selections = [{"value": f"{i:02d}", "credits": 400} for i in range(3)]  # 1200 > 1000
    resp = client.post("/simulations/bulk", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "selections": selections})
    assert resp.status_code == 400
    assert _statement(client, user_headers) == []
    assert client.get("/api/v1/wallet/balance", headers=user_headers).json()["data"]["balance"] == 1000


def test_win_row_links_the_bet(client, auth_headers, user_headers):
    _play_and_win(client, auth_headers, user_headers)
    won = next(t for t in _statement(client, user_headers) if t["kind"] == "BET_WON")
    assert won["bets"][0]["status"] == "WON" and won["market"]["name"] == "TESTGAME" and won["transactionId"]


def test_pending_deposit_shows_then_becomes_approved(client, auth_headers, user_headers):
    req = client.post("/api/v1/wallet/deposit/initiate", headers=user_headers, json={"amount": 500, "utrNumber": "123"}).json()["data"]
    rows = _statement(client, user_headers)
    assert [(r["kind"], r["status"], r["balanceAfter"]) for r in rows] == [("DEPOSIT_PENDING", "PENDING", None)]
    assert _statement(client, user_headers, transaction_type="DEBIT") == []
    assert _statement(client, user_headers, marketType="REGULAR") == []

    rid = req["id"].split("_")[1]
    assert client.post(f"/admin/credit-requests/{rid}/approve", headers=auth_headers, json={"admin_note": "ok"}).status_code == 200
    rows = _statement(client, user_headers)
    assert [r["kind"] for r in rows] == ["DEPOSIT_APPROVED"]  # the pending row is replaced, not duplicated


def test_rejected_deposit_is_listed(client, auth_headers, user_headers):
    req = client.post("/api/v1/wallet/deposit/initiate", headers=user_headers, json={"amount": 500}).json()["data"]
    client.post(f"/admin/credit-requests/{req['id'].split('_')[1]}/reject", headers=auth_headers, json={"admin_note": "bad utr"})
    row = _statement(client, user_headers)[0]
    assert (row["kind"], row["status"], row["description"]) == ("DEPOSIT_REJECTED", "REJECTED", "bad utr")


def test_withdrawal_hold_status_follows_request(client, auth_headers, user_headers):
    req = client.post("/api/v1/wallet/withdraw/request", headers=user_headers, json={"amount": 1000}).json()["data"]
    rid = req["id"].split("_")[1]
    hold = _statement(client, user_headers)[0]
    assert (hold["kind"], hold["status"], hold["type"]) == ("WITHDRAWAL_HOLD", "PENDING", "DEBIT")

    client.post(f"/admin/credit-requests/{rid}/approve", headers=auth_headers, json={"admin_note": ""})
    rows = _statement(client, user_headers)
    assert [(r["kind"], r["status"]) for r in rows] == [("WITHDRAWAL_HOLD", "SUCCESS")]
    from app.models.credit import CreditLedger
    from app.tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    assert db.query(CreditLedger).filter(CreditLedger.type == "withdraw").count() == 0  # no zero-amount marker row is written
    db.close()


def test_rejected_withdrawal_is_refunded(client, auth_headers, user_headers):
    req = client.post("/api/v1/wallet/withdraw/request", headers=user_headers, json={"amount": 1000}).json()["data"]
    client.post(f"/admin/credit-requests/{req['id'].split('_')[1]}/reject", headers=auth_headers, json={"admin_note": "no"})
    rows = _statement(client, user_headers)
    assert [(r["kind"], r["status"]) for r in rows] == [("WITHDRAWAL_REFUND", "SUCCESS"), ("WITHDRAWAL_HOLD", "REFUNDED")]


def test_result_correction_row_and_market_filter(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "1", "credits": 100})
    result = client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-03", "open_panna": "128", "publish": True}).json()
    client.post(f"/admin/results/{result['id']}/correct", headers=auth_headers, json={"reason": "typo", "open_panna": "230"})
    correction = [t for t in _statement(client, user_headers) if t["kind"] == "RESULT_CORRECTION"]
    assert len(correction) == 1 and correction[0]["market"]["name"] == "TESTGAME" and correction[0]["type"] == "DEBIT"
    assert "SINGLE 1" in correction[0]["description"] and "typo" in correction[0]["description"]
    assert any(t["kind"] == "RESULT_CORRECTION" for t in _statement(client, user_headers, marketType="REGULAR"))
    assert not any(t["kind"] == "RESULT_CORRECTION" for t in _statement(client, user_headers, marketType="STARLINE"))


def test_pagination_merges_requests_and_ledger(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    for _ in range(12):
        client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 10})
    for _ in range(12):
        client.post("/api/v1/wallet/deposit/initiate", headers=user_headers, json={"amount": 500})
    p1 = _statement(client, user_headers, page=1)
    p2 = _statement(client, user_headers, page=2)
    assert len(p1) == 20 and len(p2) == 4
    assert len({r["id"] for r in p1 + p2}) == 24  # no duplicates or gaps across pages
