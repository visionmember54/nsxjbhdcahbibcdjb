"""Brute-force protection for login endpoints.

Failures are counted per account key (email/phone) and per client IP; once either reaches
the limit inside the lock window, further attempts get 429 until it expires.

ponytail: in-memory and per-process -- resets on restart and isn't shared across workers.
Move to Redis or a DB table if the API ever runs with more than one worker.
"""
from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_failures: dict[str, list[float]] = {}


def _recent(key: str, window: float) -> list[float]:
    now = time.time()
    hits = [t for t in _failures.get(key, []) if now - t < window]
    if hits:
        _failures[key] = hits
    else:
        _failures.pop(key, None)
    return hits


def client_ip(request: Request) -> str:
    # uvicorn --proxy-headers already resolves X-Forwarded-For from the trusted proxy.
    return request.client.host if request.client else "unknown"


def check_login_allowed(request: Request, account: str) -> None:
    s = get_settings()
    window = s.LOGIN_LOCK_MINUTES * 60
    for key in (f"acct:{account.strip().lower()}", f"ip:{client_ip(request)}"):
        hits = _recent(key, window)
        if len(hits) >= s.LOGIN_MAX_FAILURES:
            retry = max(1, int(window - (time.time() - hits[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later.",
                headers={"Retry-After": str(retry)},
            )


def record_login_failure(request: Request, account: str) -> None:
    now = time.time()
    for key in (f"acct:{account.strip().lower()}", f"ip:{client_ip(request)}"):
        _failures.setdefault(key, []).append(now)


def clear_login_failures(account: str) -> None:
    _failures.pop(f"acct:{account.strip().lower()}", None)


# --- OTP send throttling -----------------------------------------------------
# A real SMS goes out through the relay device's SIM on every OTP send -- unlike
# a login attempt, there's a real cost (and carrier spam-flagging risk) to letting
# this run unbounded. Enforces the cooldown the response already advertises, plus
# a per-number and per-IP cap over a longer window.
OTP_RESEND_COOLDOWN_SECONDS = 20
OTP_MAX_PER_NUMBER_WINDOW = 10
OTP_MAX_PER_IP_WINDOW = 50
OTP_WINDOW_SECONDS = 30 * 60


def check_otp_send_allowed(request: Request, phone: str) -> None:
    phone_key = f"otp_phone:{phone.strip()}"
    ip_key = f"otp_ip:{client_ip(request)}"
    now = time.time()

    phone_hits = _recent(phone_key, OTP_WINDOW_SECONDS)
    if phone_hits:
        elapsed = now - phone_hits[-1]
        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            retry = max(1, int(OTP_RESEND_COOLDOWN_SECONDS - elapsed))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another OTP.",
                headers={"Retry-After": str(retry)},
            )
    if len(phone_hits) >= OTP_MAX_PER_NUMBER_WINDOW:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests for this number. Please try again later.",
        )

    ip_hits = _recent(ip_key, OTP_WINDOW_SECONDS)
    if len(ip_hits) >= OTP_MAX_PER_IP_WINDOW:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests from this network. Please try again later.",
        )


def record_otp_send(request: Request, phone: str) -> None:
    now = time.time()
    _failures.setdefault(f"otp_phone:{phone.strip()}", []).append(now)
    _failures.setdefault(f"otp_ip:{client_ip(request)}", []).append(now)


# --- Support chat send throttling -------------------------------------------
# Generous, not strict -- this only exists to stop a runaway client/script from
# flooding a single user's thread; normal chat use never gets near this cap.
SUPPORT_CHAT_MAX_PER_USER_WINDOW = 30
SUPPORT_CHAT_WINDOW_SECONDS = 5 * 60


def check_support_chat_send_allowed(user_id: int) -> None:
    key = f"support_chat_user:{user_id}"
    hits = _recent(key, SUPPORT_CHAT_WINDOW_SECONDS)
    if len(hits) >= SUPPORT_CHAT_MAX_PER_USER_WINDOW:
        retry = max(1, int(SUPPORT_CHAT_WINDOW_SECONDS - (time.time() - hits[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many messages sent. Please wait a moment before sending another.",
            headers={"Retry-After": str(retry)},
        )


def record_support_chat_send(user_id: int) -> None:
    _failures.setdefault(f"support_chat_user:{user_id}", []).append(time.time())


# --- Support chat upload throttling -----------------------------------------
# Tighter than the text-message cap -- uploads cost real storage, each one
# gets fully read into memory and written to the database.
SUPPORT_UPLOAD_MAX_PER_USER_WINDOW = 10
SUPPORT_UPLOAD_WINDOW_SECONDS = 5 * 60


def check_support_upload_allowed(user_id: int) -> None:
    key = f"support_upload_user:{user_id}"
    hits = _recent(key, SUPPORT_UPLOAD_WINDOW_SECONDS)
    if len(hits) >= SUPPORT_UPLOAD_MAX_PER_USER_WINDOW:
        retry = max(1, int(SUPPORT_UPLOAD_WINDOW_SECONDS - (time.time() - hits[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many uploads. Please wait a moment before sending another.",
            headers={"Retry-After": str(retry)},
        )


def record_support_upload(user_id: int) -> None:
    _failures.setdefault(f"support_upload_user:{user_id}", []).append(time.time())


def reset() -> None:
    _failures.clear()
