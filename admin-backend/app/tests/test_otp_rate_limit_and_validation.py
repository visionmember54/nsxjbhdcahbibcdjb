from __future__ import annotations

from unittest.mock import patch


def _mocked_relay():
    return patch("app.routers.public.app_api.firebase_service.otp_relay_configured", return_value=False)


def test_second_send_within_cooldown_is_rejected(client):
    with _mocked_relay():
        first = client.post("/api/v1/auth/register/send-otp", json={"phone": "9333344445"})
        assert first.status_code == 200, first.text

        second = client.post("/api/v1/auth/register/send-otp", json={"phone": "9333344445"})
    assert second.status_code == 429
    assert "Retry-After" in second.headers


def test_different_phone_numbers_are_not_blocked_by_each_others_cooldown(client):
    with _mocked_relay():
        first = client.post("/api/v1/auth/register/send-otp", json={"phone": "9333344446"})
        second = client.post("/api/v1/auth/register/send-otp", json={"phone": "9333344447"})
    assert first.status_code == 200
    assert second.status_code == 200


def test_per_number_cap_kicks_in_after_repeated_sends(client):
    from app.core import ratelimit

    with _mocked_relay():
        for _ in range(5):
            resp = client.post("/api/v1/auth/register/send-otp", json={"phone": "9333344448"})
            assert resp.status_code == 200, resp.text
            # Bypass the cooldown between iterations without touching the cap counter itself.
            key = "otp_phone:9333344448"
            if ratelimit._failures.get(key):
                ratelimit._failures[key][-1] -= ratelimit.OTP_RESEND_COOLDOWN_SECONDS + 1

        blocked = client.post("/api/v1/auth/register/send-otp", json={"phone": "9333344448"})
    assert blocked.status_code == 429


def test_rejects_phone_with_letters(client):
    resp = client.post("/api/v1/auth/register/send-otp", json={"phone": "98ABCD5352"})
    assert resp.status_code == 422


def test_rejects_phone_with_too_few_digits(client):
    resp = client.post("/api/v1/auth/register/send-otp", json={"phone": "123456"})
    assert resp.status_code == 422


def test_accepts_phone_with_country_code_and_formatting(client):
    with _mocked_relay():
        resp = client.post("/api/v1/auth/register/send-otp", json={"phone": "+91 89470-35352"})
    assert resp.status_code == 200, resp.text
