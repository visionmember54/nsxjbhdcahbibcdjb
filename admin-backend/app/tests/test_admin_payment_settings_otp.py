from __future__ import annotations

from unittest.mock import patch


def _relay_configured(configured: bool = True):
    return patch("app.routers.admin.content.firebase_service.otp_relay_configured", return_value=configured)


def _mocked_relay():
    return patch("app.routers.admin.content.firebase_service.send_otp_to_relay", return_value="projects/x/messages/1")


def _sent_code(mock_send_relay) -> str:
    args, _ = mock_send_relay.call_args
    return args[1]


def _set_own_phone(client, auth_headers, phone="9876543210"):
    admin_id = client.get("/admin/admins?limit=10", headers=auth_headers).json()["items"][0]["id"]
    resp = client.patch(f"/admin/admins/{admin_id}", headers=auth_headers, json={"phone": phone})
    assert resp.status_code == 200, resp.text
    return phone


def test_payment_setting_rejected_without_otp_on_plain_endpoint(client, auth_headers):
    resp = client.put("/admin/content/settings/payment_upi_id", headers=auth_headers, json={"value": "attacker@upi"})
    assert resp.status_code == 400
    assert "OTP" in resp.json()["message"]


def test_non_payment_setting_still_works_without_otp(client, auth_headers):
    resp = client.put("/admin/content/settings/support_phone", headers=auth_headers, json={"value": "+911234567890"})
    assert resp.status_code == 200, resp.text


def test_send_otp_requires_admin_to_have_a_phone_on_file(client, auth_headers):
    resp = client.post("/admin/content/settings/payment/send-otp", headers=auth_headers)
    assert resp.status_code == 400
    assert "phone" in resp.json()["message"].lower()


def test_full_payment_settings_otp_flow(client, auth_headers):
    _set_own_phone(client, auth_headers)

    with _relay_configured(True), _mocked_relay() as mock_send:
        send_resp = client.post("/admin/content/settings/payment/send-otp", headers=auth_headers)
    assert send_resp.status_code == 200, send_resp.text
    session_id = send_resp.json()["otpSessionId"]
    code = _sent_code(mock_send)

    resp = client.put(
        "/admin/content/settings/payment/bulk", headers=auth_headers,
        json={"values": {"payment_upi_id": "realmerchant@icici", "payment_merchant_name": "Kalyan Milan"}, "otp_session_id": session_id, "otp_code": code},
    )
    assert resp.status_code == 200, resp.text
    values = {s["key"]: s["value"] for s in resp.json()}
    assert values["payment_upi_id"] == "realmerchant@icici"

    settings = client.get("/admin/content/settings", headers=auth_headers).json()
    assert next(s["value"] for s in settings if s["key"] == "payment_upi_id") == "realmerchant@icici"


def test_bulk_update_rejects_wrong_otp_code(client, auth_headers):
    _set_own_phone(client, auth_headers)
    with _relay_configured(True), _mocked_relay():
        send_resp = client.post("/admin/content/settings/payment/send-otp", headers=auth_headers)
    session_id = send_resp.json()["otpSessionId"]

    resp = client.put(
        "/admin/content/settings/payment/bulk", headers=auth_headers,
        json={"values": {"payment_upi_id": "attacker@upi"}, "otp_session_id": session_id, "otp_code": "000000"},
    )
    assert resp.status_code == 400
    assert "OTP" in resp.json()["message"]


def test_bulk_update_rejects_non_payment_keys(client, auth_headers):
    _set_own_phone(client, auth_headers)
    with _relay_configured(True), _mocked_relay() as mock_send:
        send_resp = client.post("/admin/content/settings/payment/send-otp", headers=auth_headers)
    session_id = send_resp.json()["otpSessionId"]
    code = _sent_code(mock_send)

    resp = client.put(
        "/admin/content/settings/payment/bulk", headers=auth_headers,
        json={"values": {"maintenance_mode": "true"}, "otp_session_id": session_id, "otp_code": code},
    )
    assert resp.status_code == 400


def test_otp_cannot_be_reused_after_being_consumed(client, auth_headers):
    _set_own_phone(client, auth_headers)
    with _relay_configured(True), _mocked_relay() as mock_send:
        send_resp = client.post("/admin/content/settings/payment/send-otp", headers=auth_headers)
    session_id = send_resp.json()["otpSessionId"]
    code = _sent_code(mock_send)

    first = client.put(
        "/admin/content/settings/payment/bulk", headers=auth_headers,
        json={"values": {"payment_upi_id": "first@upi"}, "otp_session_id": session_id, "otp_code": code},
    )
    assert first.status_code == 200, first.text

    second = client.put(
        "/admin/content/settings/payment/bulk", headers=auth_headers,
        json={"values": {"payment_upi_id": "second@upi"}, "otp_session_id": session_id, "otp_code": code},
    )
    assert second.status_code == 400
