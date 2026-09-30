from __future__ import annotations

from unittest.mock import patch

from app.core.errors import AppError
from app.services import firebase_service


def test_normalize_phone_strips_country_code_and_symbols():
    assert firebase_service.normalize_phone("+91 98765 43210") == "9876543210"
    assert firebase_service.normalize_phone("919876543210") == "9876543210"
    assert firebase_service.normalize_phone("9876543210") == "9876543210"


def test_phones_match_across_formats():
    assert firebase_service.phones_match("+919876543210", "9876543210")
    assert not firebase_service.phones_match("+919876543210", "9876543211")


def test_verify_phone_token_fails_loudly_when_unconfigured():
    firebase_service.reset_for_tests()
    try:
        try:
            firebase_service.verify_phone_token("whatever")
            assert False, "expected AppError"
        except AppError as exc:
            assert exc.code == "FIREBASE_NOT_CONFIGURED"
            assert exc.status_code == 500
    finally:
        firebase_service.reset_for_tests()


def _mock_verified(phone: str):
    return patch("app.routers.public.app_api.firebase_service.verify_phone_token", return_value=phone)


def test_register_with_firebase_token_skips_legacy_otp(client):
    with _mock_verified("+919111122223"):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Firebase Signup",
                "phone": "9111122223",
                "password": "pass1234",
                "firebaseIdToken": "fake-but-mocked-valid",
            },
        )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["data"]["user"]["phone"] == "9111122223"
    assert body["data"]["token"]


def test_register_with_firebase_token_rejects_phone_mismatch(client):
    with _mock_verified("+919999999999"):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Mismatch",
                "phone": "9111122224",
                "password": "pass1234",
                "firebaseIdToken": "fake-but-mocked-valid",
            },
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "PHONE_MISMATCH"


def test_register_requires_a_verification_method(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "No Verification", "phone": "9111122225", "password": "pass1234"},
    )
    assert resp.status_code == 422


def test_forgot_password_with_firebase_token(client, user_headers):
    with _mock_verified("+919000000000"):
        resp = client.post(
            "/api/v1/auth/forgot-password/confirm",
            json={"firebaseIdToken": "fake-but-mocked-valid", "newPassword": "newpass123"},
        )
    assert resp.status_code == 200, resp.text

    # old password no longer works, new one does
    old = client.post("/api/v1/auth/login", json={"phone": "9000000000", "password": "user12345"})
    assert old.status_code == 401
    new = client.post("/api/v1/auth/login", json={"phone": "9000000000", "password": "newpass123"})
    assert new.status_code == 200


def test_login_with_phone_token_for_existing_user(client):
    with _mock_verified("+919000000000"):
        resp = client.post("/api/v1/auth/login-with-phone-token", json={"firebaseIdToken": "fake-but-mocked-valid"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["user"]["phone"] == "9000000000"


def test_login_with_phone_token_unknown_number(client):
    with _mock_verified("+919888877776"):
        resp = client.post("/api/v1/auth/login-with-phone-token", json={"firebaseIdToken": "fake-but-mocked-valid"})
    assert resp.status_code == 404
