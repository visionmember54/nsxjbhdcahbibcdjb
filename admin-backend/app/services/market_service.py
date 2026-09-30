from __future__ import annotations

from datetime import datetime, time as time_
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import CUTOFF_PASSED, MARKET_CLOSED, SLOT_CLOSED, AppError
from app.models.market import Market, StarlineSlot
from app.models.market_result import MarketResult

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

_WEEKDAY_CODES = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


def active_days_to_list(value: str | None) -> list[str] | None:
    """DB storage (comma-separated "SAT,SUN") -> API shape (["SAT", "SUN"]), or None for every day."""
    if not value:
        return None
    days = [d.strip().upper() for d in value.split(",") if d.strip()]
    return days or None


def active_days_to_str(value: list[str] | None) -> str | None:
    """API shape -> DB storage. Empty list is treated the same as None (every day)."""
    if not value:
        return None
    return ",".join(d.strip().upper() for d in value)


def _runs_today(market: Market, now_date) -> bool:
    if not market.active_days:
        return True
    scheduled = {d.strip().upper() for d in market.active_days.split(",") if d.strip()}
    return _WEEKDAY_CODES[now_date.weekday()] in scheduled


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
    of leaving yesterday's result/closed state on screen indefinitely.

    active_days restricts which weekdays a market runs on at all (e.g. a
    weekend-only CUSTOM market) -- on a day it's not scheduled, it's simply
    CLOSED for that day, no matter what the stored status says."""
    if market.status == "SUSPENDED":
        return "SUSPENDED"

    now_dt = datetime.now(ZoneInfo(market.timezone or "Asia/Kolkata"))
    now = now_dt.time()

    if not _runs_today(market, now_dt.date()):
        return "CLOSED"

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


def declared_result_today(db: Session, market: Market) -> MarketResult | None:
    """Today's Published/Corrected result row for this market (Matka-shaped, no
    slot), if one exists yet. Used to auto-close a session the instant its
    number is declared, with no per-market schedule config required."""
    today = datetime.now(ZoneInfo(market.timezone or "Asia/Kolkata")).date().isoformat()
    return (
        db.query(MarketResult)
        .filter(
            MarketResult.market_id == market.id,
            MarketResult.slot_id.is_(None),
            MarketResult.result_date == today,
            MarketResult.status.in_(("Published", "Corrected")),
        )
        .order_by(MarketResult.id.desc())
        .first()
    )


def assert_market_open(db: Session, market: Market, stage: str | None = None) -> None:
    if effective_market_status(market) != "OPEN":
        raise AppError(MARKET_CLOSED, f"Market '{market.name}' is not open")

    result = declared_result_today(db, market)

    if stage == "CLOSE":
        # Close-session bets stop the instant today's Close number is declared, or at
        # closing_time, whichever comes first.
        if result and result.close_panna:
            raise AppError(CUTOFF_PASSED, f"Market '{market.name}' Close result has already been declared for today")
        if _cutoff_passed(market.closing_time, market.timezone):
            raise AppError(CUTOFF_PASSED, f"Market '{market.name}' cutoff has passed")
        return

    # Open-session bets (and jodi/sangam, which need the open result): stop the instant
    # today's Open number is declared -- automatic, independent of any admin-entered
    # cutoff_time -- or at cutoff_time/closing_time if one is set, whichever is first.
    if result and result.open_panna:
        raise AppError(CUTOFF_PASSED, f"Market '{market.name}' Open result has already been declared for today")
    if _cutoff_passed(market.cutoff_time or market.closing_time, market.timezone):
        raise AppError(CUTOFF_PASSED, f"Market '{market.name}' cutoff has passed")


def assert_slot_open(slot: StarlineSlot, market: Market) -> None:
    if not slot.enabled:
        raise AppError(SLOT_CLOSED, f"Slot '{slot.slot_name}' is not open")
    if _cutoff_passed(slot.cutoff_time, market.timezone):
        raise AppError(SLOT_CLOSED, f"Slot '{slot.slot_name}' cutoff has passed")
