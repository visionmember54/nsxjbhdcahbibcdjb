from __future__ import annotations


def _market_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def test_jodi_resolves_only_after_both_stages_published(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)

    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "JODI", "value": "16", "credits": 100})
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "1", "credits": 10})

    # Publish OPEN only: open_panna=128 -> open_ank=1
    client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-01", "open_panna": "128", "publish": True})

    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    jodi_entry = next(e for e in entries if e["gameType"] == "JODI")
    single_entry = next(e for e in entries if e["gameType"] == "SINGLE")
    assert jodi_entry["status"] == "Pending"  # awaiting close
    assert single_entry["status"] == "Won"  # open_ank matches "1"

    # Publish CLOSE: close_panna=600 -> close_ank=6 -> jodi="16"
    client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-01", "close_panna": "600", "publish": True})

    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    jodi_entry = next(e for e in entries if e["gameType"] == "JODI")
    assert jodi_entry["status"] == "Won"
    assert jodi_entry["simulatedReturn"] == 100 * 95 // 10  # rate seeded as 95 "per 10 credits"

    user = client.get("/auth/me", headers=user_headers).json()
    assert user["balance"] > 1000  # net positive after payouts


def test_payout_uses_configured_rate(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "5", "credits": 100})
    resp = client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-02", "open_panna": "500", "publish": True})
    assert resp.json()["openAnk"] == "5"

    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    entry = next(e for e in entries if e["selection"] == "5")
    assert entry["status"] == "Won"
    assert entry["simulatedReturn"] == 100 * 95 // 10  # rate seeded as 95 "per 10 credits"


def test_correction_reverses_payout_and_reevaluates(client, auth_headers, user_headers):
    mid = _market_id(client, auth_headers)
    client.post("/simulations", headers=user_headers, json={"market_id": mid, "game_type": "SINGLE", "stage": "OPEN", "value": "1", "credits": 100})

    result = client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-03", "open_panna": "128", "publish": True}).json()
    balance_after_win = client.get("/auth/me", headers=user_headers).json()["balance"]

    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    entry = next(e for e in entries if e["selection"] == "1")
    assert entry["status"] == "Won"

    # Correct to a panna whose ank != 1, flipping the entry to Lost and reversing the payout
    corrected = client.post(
        f"/admin/results/{result['id']}/correct", headers=auth_headers,
        json={"open_panna": "222", "reason": "Data entry error"},
    ).json()
    assert corrected["openAnk"] == "6"
    assert corrected["correctedFromId"] == result["id"]
    assert corrected["correctionReason"] == "Data entry error"

    entries = client.get("/simulations/my?limit=10", headers=user_headers).json()["items"]
    entry = next(e for e in entries if e["selection"] == "1")
    assert entry["status"] == "Lost"

    balance_after_correction = client.get("/auth/me", headers=user_headers).json()["balance"]
    assert balance_after_correction < balance_after_win


def test_correction_without_reason_rejected(client, auth_headers):
    mid = _market_id(client, auth_headers)
    result = client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-05", "open_panna": "128", "publish": True}).json()
    resp = client.post(f"/admin/results/{result['id']}/correct", headers=auth_headers, json={"open_panna": "222"})
    assert resp.status_code == 422


def test_result_delete_is_single_record_only(client, auth_headers):
    mid = _market_id(client, auth_headers)
    result = client.post("/admin/results", headers=auth_headers, json={"market_id": mid, "date": "2026-01-04", "open_panna": "128", "publish": True}).json()
    resp = client.delete(f"/admin/results/{result['id']}", headers=auth_headers)
    assert resp.status_code == 204

    remaining = client.get("/admin/results?limit=50", headers=auth_headers).json()
    assert result["id"] not in [r["id"] for r in remaining["items"]]
