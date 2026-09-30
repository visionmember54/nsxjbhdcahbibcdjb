from __future__ import annotations


def _market_id(client, auth_headers):
    markets = client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"]
    return next(m["id"] for m in markets if m["name"] == "TESTGAME")


def _configs_by_code(client, auth_headers, market_id):
    rows = client.get(f"/admin/markets/{market_id}/game-type-configs", headers=auth_headers).json()
    return {c["game_type_code"]: c for c in rows}


def test_new_config_defaults_to_display_order_zero(client, auth_headers):
    mid = _market_id(client, auth_headers)
    configs = _configs_by_code(client, auth_headers, mid)
    assert configs["SINGLE"]["display_order"] == 0


def test_admin_can_set_and_read_back_display_order(client, auth_headers):
    mid = _market_id(client, auth_headers)
    configs = _configs_by_code(client, auth_headers, mid)
    single_id = configs["SINGLE"]["id"]

    resp = client.patch(
        f"/admin/markets/{mid}/game-type-configs/{single_id}", headers=auth_headers, json={"display_order": 5}
    )
    assert resp.status_code == 200
    assert resp.json()["display_order"] == 5

    refreshed = _configs_by_code(client, auth_headers, mid)
    assert refreshed["SINGLE"]["display_order"] == 5


def test_admin_list_is_sorted_by_display_order(client, auth_headers):
    mid = _market_id(client, auth_headers)
    configs = _configs_by_code(client, auth_headers, mid)
    # Put DOUBLE_PANNA before TRIPLE_PANNA before SINGLE_PANNA, opposite of id order.
    client.patch(f"/admin/markets/{mid}/game-type-configs/{configs['DOUBLE_PANNA']['id']}", headers=auth_headers, json={"display_order": 1})
    client.patch(f"/admin/markets/{mid}/game-type-configs/{configs['TRIPLE_PANNA']['id']}", headers=auth_headers, json={"display_order": 2})
    client.patch(f"/admin/markets/{mid}/game-type-configs/{configs['SINGLE_PANNA']['id']}", headers=auth_headers, json={"display_order": 3})

    rows = client.get(f"/admin/markets/{mid}/game-type-configs", headers=auth_headers).json()
    codes = [r["game_type_code"] for r in rows if r["game_type_code"] in ("DOUBLE_PANNA", "TRIPLE_PANNA", "SINGLE_PANNA")]
    assert codes == ["DOUBLE_PANNA", "TRIPLE_PANNA", "SINGLE_PANNA"]


def test_public_market_games_endpoint_respects_display_order(client, auth_headers):
    """This is what the app actually reads to build its game list."""
    mid = _market_id(client, auth_headers)
    configs = _configs_by_code(client, auth_headers, mid)
    client.patch(f"/admin/markets/{mid}/game-type-configs/{configs['SINGLE_PANNA']['id']}", headers=auth_headers, json={"display_order": 10})
    client.patch(f"/admin/markets/{mid}/game-type-configs/{configs['DOUBLE_PANNA']['id']}", headers=auth_headers, json={"display_order": 1})
    client.patch(f"/admin/markets/{mid}/game-type-configs/{configs['TRIPLE_PANNA']['id']}", headers=auth_headers, json={"display_order": 5})

    rows = client.get(f"/markets/{mid}/games").json()
    codes = [r["game_type_code"] for r in rows if r["game_type_code"] in ("SINGLE_PANNA", "DOUBLE_PANNA", "TRIPLE_PANNA")]
    assert codes == ["DOUBLE_PANNA", "TRIPLE_PANNA", "SINGLE_PANNA"]
