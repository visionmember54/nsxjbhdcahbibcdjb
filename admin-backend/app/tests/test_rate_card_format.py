from __future__ import annotations


def test_config_game_rates_uses_dash_not_ka(client):
    resp = client.get("/api/v1/config/game-rates")
    assert resp.status_code == 200, resp.text
    rows = resp.json()["data"]["rates"]
    assert rows
    for row in rows:
        assert "KA" not in row["payout"]
        assert row["payout"].startswith("10-")


def test_config_bootstrap_rates_summary_uses_dash_not_ka(client):
    resp = client.get("/api/v1/config/bootstrap")
    assert resp.status_code == 200, resp.text
    rows = resp.json()["data"]["overviewRules"]["ratesSummary"]
    assert rows
    for row in rows:
        assert "KA" not in row["rate"]
        assert row["rate"].startswith("10-")
