"""Firebase Admin SDK integration: verifies Phone Auth ID tokens and sends
Cloud Messaging (FCM) push notifications.

Firebase itself sends and checks the SMS code entirely on the client (via
the Flutter app's Firebase SDK) -- the backend is never involved in sending
an OTP. Once the user enters the correct code, Firebase hands the app a
signed ID token; the app forwards that token here, and this module checks
it's genuinely signed by Firebase and extracts the verified phone number.

Credentials come from either FIREBASE_SERVICE_ACCOUNT_JSON (the whole key
file's contents, as a single env var -- the only option on Render's free/
starter plans, which don't include Secret Files) or a local JSON file at
FIREBASE_SERVICE_ACCOUNT_PATH (for local development). If neither is
present, `is_configured()` is False and callers should fail clearly rather
than silently skipping verification.
"""
from __future__ import annotations

import json
import logging
import os
import threading

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin import messaging

from app.core import errors
from app.core.config import get_settings
from app.core.errors import AppError

_push_logger = logging.getLogger("app.push")
_firebase_logger = logging.getLogger("app.firebase")

_app: firebase_admin.App | None = None
_lock = threading.Lock()
_init_attempted = False


def _load_credentials() -> credentials.Certificate | None:
    settings = get_settings()
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        return credentials.Certificate(info)
    if os.path.isfile(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
        return credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    return None


def _get_app() -> firebase_admin.App | None:
    global _app, _init_attempted
    if _app is not None:
        return _app
    with _lock:
        if _app is not None or _init_attempted:
            return _app
        _init_attempted = True
        try:
            cred = _load_credentials()
            if cred is None:
                _firebase_logger.warning(
                    "Firebase not configured: neither FIREBASE_SERVICE_ACCOUNT_JSON nor "
                    "FIREBASE_SERVICE_ACCOUNT_PATH resolved to usable credentials."
                )
                return None
            _app = firebase_admin.initialize_app(cred, name="kalyan-otp")
            return _app
        except Exception:
            # Logged with a full traceback so a malformed/truncated env var value is
            # actually diagnosable in Render's logs, instead of surfacing as an opaque
            # "not configured" on every request for the rest of this process's life.
            _firebase_logger.exception("Firebase Admin SDK failed to initialize -- check FIREBASE_SERVICE_ACCOUNT_JSON")
            return None


def is_configured() -> bool:
    return _get_app() is not None


def otp_relay_configured() -> bool:
    return is_configured() and bool(get_settings().OTP_RELAY_DEVICE_FCM_TOKEN)


def reset_for_tests() -> None:
    """Test-only: clears the cached app so a later test can inject its own fake verifier."""
    global _app, _init_attempted
    _app = None
    _init_attempted = False


def verify_phone_token(id_token: str) -> str:
    """Verifies a Firebase ID token and returns the verified phone number
    (E.164, e.g. "+919876543210"). Raises AppError on any failure."""
    app = _get_app()
    if app is None:
        raise AppError(
            errors.FIREBASE_NOT_CONFIGURED,
            "Phone verification is not configured on this server",
            status_code=500,
        )
    try:
        decoded = firebase_auth.verify_id_token(id_token, app=app)
    except Exception as exc:  # firebase_admin raises several distinct exception types
        raise AppError(errors.INVALID_FIREBASE_TOKEN, f"Invalid or expired verification token: {exc}") from exc

    phone = decoded.get("phone_number")
    if not phone:
        raise AppError(errors.INVALID_FIREBASE_TOKEN, "Token was not issued for phone verification")
    return phone


def normalize_phone(phone: str) -> str:
    """Last 10 digits, so "+919876543210", "919876543210", and "9876543210"
    (Firebase's E.164 form vs. how phones are stored elsewhere in this app)
    all compare equal."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    return digits[-10:]


def phones_match(a: str, b: str) -> bool:
    return normalize_phone(a) == normalize_phone(b)


def send_push(fcm_token: str, title: str, body: str, data: dict[str, str] | None = None) -> str:
    """Sends one Firebase Cloud Messaging push notification. Returns Firebase's
    message id on success. Raises AppError if Firebase isn't configured or the
    send itself fails (a stale/unregistered token, malformed message, etc.)."""
    app = _get_app()
    if app is None:
        raise AppError(
            errors.FIREBASE_NOT_CONFIGURED,
            "Push notifications are not configured on this server",
            status_code=500,
        )
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=fcm_token,
    )
    try:
        return messaging.send(message, app=app)
    except Exception as exc:  # firebase_admin raises several distinct exception types
        _push_logger.warning(f"Push send failed for token ...{fcm_token[-8:]}: {exc}")
        raise AppError(errors.PUSH_SEND_FAILED, f"Failed to send push notification: {exc}") from exc


def send_otp_to_relay(phone_number: str, otp: str) -> str:
    """Sends {appName, phoneNumber, otp} as a data-only FCM message to the one
    fixed relay device (OTP_RELAY_DEVICE_FCM_TOKEN) -- a phone with a SIM,
    running a small app that receives this and sends the real SMS via its own
    SmsManager. Data-only (no `notification` block) so the relay app's own
    handler always runs, even if Android would otherwise auto-display a
    system notification while the app is backgrounded.

    Raises AppError if Firebase or the relay token isn't configured, or if
    the send itself fails."""
    settings = get_settings()
    if not settings.OTP_RELAY_DEVICE_FCM_TOKEN:
        raise AppError(
            errors.OTP_RELAY_NOT_CONFIGURED,
            "No OTP relay device is configured on this server (OTP_RELAY_DEVICE_FCM_TOKEN)",
            status_code=500,
        )
    app = _get_app()
    if app is None:
        raise AppError(
            errors.FIREBASE_NOT_CONFIGURED,
            "Push notifications are not configured on this server",
            status_code=500,
        )
    message = messaging.Message(
        data={"appName": settings.OTP_RELAY_APP_NAME, "phoneNumber": phone_number, "otp": otp},
        token=settings.OTP_RELAY_DEVICE_FCM_TOKEN,
    )
    try:
        return messaging.send(message, app=app)
    except Exception as exc:  # firebase_admin raises several distinct exception types
        _push_logger.warning(f"OTP relay push failed for {phone_number}: {exc}")
        raise AppError(errors.PUSH_SEND_FAILED, f"Failed to send OTP via relay device: {exc}") from exc
