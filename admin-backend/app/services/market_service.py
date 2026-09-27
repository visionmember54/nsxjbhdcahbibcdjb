from __future__ import annotations

from datetime import datetime, time as time_
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import CUTOFF_PASSED, MARKET_CLOSED, SLOT_CLOSED, AppError
from app.models.market import Market, StarlineSlot

# Market status state machine
VALID_TRANSITIONS: dict[str, set[str]] = {
    "UPCOMING": {"OPEN", "SUSPENDED"},
    "OPEN": {"CLOSED", "SUSPENDED"},
    "CLOSED": {"RESULT_PENDING", "OPEN", "SUSPENDED"},
    "RESULT_PENDING": {"RESULT_PUBLISHED", "SUSPENDED"},
    "RESULT_PUBLISHED": {"UPCOMING", "SUSPENDED"},
    "SUSPENDED": {"UPCOMING"},
}

ALL_STATUSES = {"UPCOMING", "OPEN", "CLOSED", "RESULT_PENDING", "RESULT_PUBLISHED", "SUSPENDED"}


def transition_status(db: Session, market: Market, new_status: str) -> Market:
    if new_status not in ALL_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown status '{new_status}'")

    allowed = VALID_TRANSITIONS.get(market.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition market from {market.status} to {new_status}",
        )

    market.status = new_status
    db.flush()
    return market


def _cutoff_passed(cutoff: time_ | None, timezone_name: str) -> bool:
    if cutoff is None:
        return False
    return datetime.now(ZoneInfo(timezone_name)).time() >= cutoff


def effective_market_status(market: Market) -> str:
    """market.status is admin-set and never advances on its own -- a market left
    at UPCOMING past its scheduled opening_time would otherwise block bets
    forever (and one left at OPEN past closing_time would accept them forever)
    until someone manually clicks the status button. This derives the status
    actually in effect right now, without touching the stored column, so both
    bet validation and the app's displayed session status auto-advance on
    schedule. SUSPENDED is always an explicit admin override and is never
    touched here.

    CLOSED / RESULT_PENDING / RESULT_PUBLISHED are only meaningful for the day
    they were set on -- each market runs one open/close/result cycle per day.
    If we're still sitting in one of those from yesterday (i.e. it's now before
    today's opening_time), treat it as a fresh UPCOMING for the new day instead
    of leaving yesterday's result/closed state on screen indefinitely."""
    if market.status == "SUSPENDED":
        return "SUSPENDED"

    now = datetime.now(ZoneInfo(market.timezone or "Asia/Kolkata")).time()

    status_for_today = market.status
    if status_for_today in ("CLOSED", "RESULT_PENDING", "RESULT_PUBLISHED"):
        if market.opening_time is None or now < market.opening_time:
            status_for_today = "UPCOMING"
        else:
            return status_for_today  # still within/after today's window -- admin-driven, leave as-is

    if status_for_today == "UPCOMING":
        if market.opening_time and now >= market.opening_time:
            deadline = market.closing_time or market.cutoff_time
            if deadline is None or now < deadline:
                return "OPEN"
        return "UPCOMING"

    # status_for_today == "OPEN"
    if market.closing_time and now >= market.closing_time:
        return "CLOSED"
    return "OPEN"


def assert_market_open(market: Market, stage: str | None = None) -> None:
    if effective_market_status(market) != "OPEN":
        raise AppError(MARKET_CLOSED, f"Market '{market.name}' is not open")
    # Open-session bets (and jodi/sangam, which need the open result) stop at the cutoff; close-session
    # bets stay open until the market closes.
    deadline = market.closing_time if stage == "CLOSE" and market.closing_time else (market.cutoff_time or market.closing_time)
    if _cutoff_passed(deadline, market.timezone):
        raise AppError(CUTOFF_PASSED, f"Market '{market.name}' cutoff has passed")


def assert_slot_open(slot: StarlineSlot, market: Market) -> None:
    if not slot.enabled:
        raise AppError(SLOT_CLOSED, f"Slot '{slot.slot_name}' is not open")
    if _cutoff_passed(slot.cutoff_time, market.timezone):
        raise AppError(SLOT_CLOSED, f"Slot '{slot.slot_name}' cutoff has passed")
