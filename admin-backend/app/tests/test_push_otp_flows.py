from __future__ import annotations

from unittest.mock import patch


def _relay_configured(configured: bool = True):
    """Patches the module-level check app_api.py calls before attempting delivery."""
    return patch("app.routers.public.app_api.firebase_service.otp_relay_configured", return_value=configured)


def _mocked_relay():
    return patch("app.routers.public.app_api.firebase_service.send_otp_to_relay", return_value="projects/x/messages/1")


def _sent_code(mock_send_relay) -> str:
    args, _ = mock_send_relay.call_args
    return args[1]  # send_otp_to_relay(phone_number, otp)


def test_register_send_otp_relays_when_configured(client):
    with _relay_configured(True), _mocked_relay() as mock_send:
        resp = client.post("/api/v1/auth/register/send-otp", json={"phone": "9222233334"})
    assert resp.status_code == 200, resp.text
    assert mock_send.called
    assert resp.json()["message"] == "OTP sent"


def test_register_send_otp_without_relay_configured_logs_only(client):
    with _relay_configured(False), _mocked_relay() as mock_send:
        resp = client.post("/api/v1/auth/register/send-otp", json={"phone": "9222233335"})
    assert resp.status_code == 200, resp.text
    assert not mock_send.called
    assert "console" in resp.json()["message"]


def test_full_register_flow_with_relay_delivered_otp(client):
    with _relay_configured(True), _mocked_relay() as mock_send:
        send_resp = client.post("/api/v1/auth/register/send-otp", json={"phone": "9222233336"})
    session_id = send_resp.json()["data"]["otpSessionId"]
    code = _sent_code(mock_send)
    mock_send.assert_called_once_with("9222233336", code)

    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "Relay Signup", "phone": "9222233336", "password": "pass1234", "otpSessionId": session_id, "otp": code},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["user"]["phone"] == "9222233336"


def test_send_login_otp_unknown_phone_404(client):
    with _relay_configured(True), _mocked_relay():
        resp = client.post("/api/v1/auth/login/send-otp", json={"phoneNumber": "9222299999"})
    assert resp.status_code == 404


def test_login_via_otp_full_flow(client, user_headers):
    with _relay_configured(True), _mocked_relay() as mock_send:
        send_resp = client.post("/api/v1/auth/login/send-otp", json={"phoneNumber": "9000000000"})
    assert send_resp.status_code == 200, send_resp.text
    session_id = send_resp.json()["data"]["otpSessionId"]
    code = _sent_code(mock_send)

    resp = client.post("/api/v1/auth/login/verify-otp", json={"otpSessionId": session_id, "otp": code, "fcmToken": "device-4"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["user"]["phone"] == "9000000000"
    assert resp.json()["data"]["token"]


def test_login_via_otp_wrong_code_rejected(client, user_headers):
    with _relay_configured(True), _mocked_relay():
        send_resp = client.post("/api/v1/auth/login/send-otp", json={"phoneNumber": "9000000000"})
    session_id = send_resp.json()["data"]["otpSessionId"]

    resp = client.post("/api/v1/auth/login/verify-otp", json={"otpSessionId": session_id, "otp": "000000"})
    assert resp.status_code == 400


def test_forgot_password_via_relay_otp(client, user_headers):
    with _relay_configured(True), _mocked_relay() as mock_send:
        req_resp = client.post("/api/v1/auth/forgot-password/request-otp", json={"phone": "9000000000"})
    assert req_resp.status_code == 200, req_resp.text
    session_id = req_resp.json()["data"]["otpSessionId"]
    code = _sent_code(mock_send)

    resp = client.post(
        "/api/v1/auth/forgot-password/confirm",
        json={"otpSessionId": session_id, "otp": code, "newPassword": "brandnewpass1"},
    )
    assert resp.status_code == 200, resp.text

    login = client.post("/api/v1/auth/login", json={"phone": "9000000000", "password": "brandnewpass1"})
    assert login.status_code == 200


def test_send_otp_to_relay_fails_loudly_when_not_configured():
    from app.core.errors import AppError
    from app.services import firebase_service

    with patch("app.services.firebase_service.get_settings") as mock_settings:
        mock_settings.return_value.OTP_RELAY_DEVICE_FCM_TOKEN = None
        try:
            firebase_service.send_otp_to_relay("9876543210", "123456")
            assert False, "expected AppError"
        except AppError as exc:
            assert exc.code == "OTP_RELAY_NOT_CONFIGURED"
