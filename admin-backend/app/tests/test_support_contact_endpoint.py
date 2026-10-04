from __future__ import annotations


def _set(client, auth_headers, key, value):
    resp = client.put(f"/admin/content/settings/{key}", headers=auth_headers, json={"value": value})
    assert resp.status_code == 200, resp.text


def test_support_contact_returns_all_fields(client, auth_headers):
    _set(client, auth_headers, "support_phone", "+91 7000000000")
    _set(client, auth_headers, "support_whatsapp", "917000000000")
    _set(client, auth_headers, "support_telegram", "https://t.me/example")
    _set(client, auth_headers, "support_email", "support@example.com")
    _set(client, auth_headers, "app_share_url", "https://example.com/app")

    resp = client.get("/api/v1/support/contact")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["phone"] == "+91 7000000000"
    assert data["whatsapp"] == "917000000000"
    assert data["telegram"] == "https://t.me/example"
    assert data["email"] == "support@example.com"
    assert data["shareUrl"] == "https://example.com/app"


def test_support_contact_defaults_to_empty_strings_when_unset(client):
    resp = client.get("/api/v1/support/contact")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    for key in ("phone", "whatsapp", "telegram", "email", "shareUrl"):
        assert data[key] == ""
    assert data["faqs"] == []


def test_support_contact_includes_only_enabled_faqs_in_order(client, auth_headers):
    client.post("/admin/content/faqs", headers=auth_headers, json={"question": "Q2", "answer": "A2", "display_order": 2})
    client.post("/admin/content/faqs", headers=auth_headers, json={"question": "Q1", "answer": "A1", "display_order": 1})
    hidden = client.post("/admin/content/faqs", headers=auth_headers, json={"question": "Hidden", "answer": "A3", "display_order": 0}).json()
    client.patch(f"/admin/content/faqs/{hidden['id']}", headers=auth_headers, json={"enabled": False})

    resp = client.get("/api/v1/support/contact")
    assert resp.status_code == 200, resp.text
    faqs = resp.json()["data"]["faqs"]
    assert [f["question"] for f in faqs] == ["Q1", "Q2"]


def test_support_contact_requires_no_auth(client):
    resp = client.get("/api/v1/support/contact")
    assert resp.status_code == 200
