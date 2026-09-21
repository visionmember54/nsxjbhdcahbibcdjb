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


def reset() -> None:
    _failures.clear()
