"""In-process OTP issuance for registration, login, and password reset.

Delivery is via Firebase Cloud Messaging push (to a device token the caller
already has, from the app's own Firebase SDK init -- independent of whether
a User row exists yet, so this works for brand-new signups too). If no
fcm_token is supplied, the code is only logged server-side -- a dev-mode
fallback for testing without a real device.

Note on what this proves: a push-delivered OTP confirms the caller has that
specific device, not that they own the phone number itself (unlike a real
SMS). This tradeoff was chosen deliberately to avoid a paid third-party SMS
gateway; revisit if phone-number ownership verification becomes a real
requirement (e.g. via Firebase Phone Auth's client-side SMS flow instead).

Storage is a process-local dict, which is fine for a single dev/staging
uvicorn worker; a multi-worker or production deployment would need this in
Redis or the database instead.
"""
from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

OTP_TTL_MINUTES = 10
_otp_logger = logging.getLogger("app.otp")

_sessions: dict[str, dict] = {}


def issue_otp(phone: str, purpose: str) -> tuple[str, int, str]:
    """-> (otpSessionId, resendCooldownSeconds, code). Always logs the code
    server-side too, so it stays testable without a device in dev/staging."""
    session_id = f"otp_{purpose}_{uuid.uuid4().hex[:10]}"
    code = f"{random.randint(0, 999999):06d}"
    _sessions[session_id] = {
        "phone": phone,
        "purpose": purpose,
        "code": code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
        "verified": False,
    }
    _otp_logger.info(f"OTP for {purpose} / {phone}: {code} (session={session_id})")
    return session_id, 60, code


def verify_otp(session_id: str, code: str, purpose: str) -> str | None:
    """Returns the phone the session was issued for on success, else None.
    The caller decides whether that phone matches what it expected."""
    entry = _sessions.get(session_id)
    if not entry or entry["purpose"] != purpose:
        return None
    if datetime.now(timezone.utc) > entry["expires_at"]:
        del _sessions[session_id]
        return None
    if entry["code"] != code.strip():
        return None
    return entry["phone"]


def consume_otp(session_id: str) -> None:
    _sessions.pop(session_id, None)
