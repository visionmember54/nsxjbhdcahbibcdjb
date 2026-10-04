from __future__ import annotations


def _set(client, auth_headers, key, value):
    resp = client.put(f"/admin/content/settings/{key}", headers=auth_headers, json={"value": value})
    assert resp.status_code == 200, resp.text


def test_home_dashboard_includes_phone_and_email(client, auth_headers, user_headers):
    _set(client, auth_headers, "support_phone", "+91 7000000000")
    _set(client, auth_headers, "support_email", "support@example.com")
    _set(client, auth_headers, "support_whatsapp", "917000000000")
    _set(client, auth_headers, "support_telegram", "https://t.me/example")

    config = client.get("/api/v1/home/dashboard", headers=user_headers).json()["data"]["appConfig"]
    assert config["supportPhone"] == "+91 7000000000"
    assert config["supportEmail"] == "support@example.com"
    assert config["supportWhatsApp"] == "917000000000"
    assert config["supportTelegram"] == "https://t.me/example"


def test_config_bootstrap_includes_phone_and_email(client, auth_headers):
    _set(client, auth_headers, "support_phone", "+91 7000000000")
    _set(client, auth_headers, "support_email", "support@example.com")

    support = client.get("/api/v1/config/bootstrap").json()["data"]["support"]
    assert support["phone"] == "+91 7000000000"
    assert support["email"] == "support@example.com"


def test_support_fields_default_to_empty_string_when_unset(client):
    support = client.get("/api/v1/config/bootstrap").json()["data"]["support"]
    assert support["phone"] == ""
    assert support["email"] == ""
    assert support["whatsapp"] == ""
    assert support["telegram"] == ""
