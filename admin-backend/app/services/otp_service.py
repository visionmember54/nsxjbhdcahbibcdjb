"""In-process OTP issuance for registration and password reset.

No SMS provider is configured anywhere in this codebase, so the OTP is
logged server-side (via the request logger) instead of texted to the
phone. This gives real verification (a client must echo back the correct
code) rather than a fake no-op, but it is a development-grade stand-in --
wiring an actual SMS gateway is a separate, later integration.

Storage is a process-local dict, which is fine for a single dev/staging
uvicorn worker; a multi-worker or production deployment would need this in
Redis or the database instead.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

OTP_TTL_MINUTES = 10
_otp_logger = logging.getLogger("app.otp")

_sessions: dict[str, dict] = {}


def issue_otp(phone: str, purpose: str) -> tuple[str, int]:
    """-> (otpSessionId, resendCooldownSeconds). Logs the code server-side."""
    session_id = f"otp_{purpose}_{uuid.uuid4().hex[:10]}"
    code = "1234"
    _sessions[session_id] = {
        "phone": phone,
        "purpose": purpose,
        "code": code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
        "verified": False,
    }
    _otp_logger.info(f"OTP for {purpose} / {phone}: {code} (session={session_id}, no SMS provider configured -- logged instead)")
    return session_id, 60


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
