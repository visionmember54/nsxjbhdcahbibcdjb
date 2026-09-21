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


def assert_market_open(market: Market, stage: str | None = None) -> None:
    if market.status != "OPEN":
        raise AppError(MARKET_CLOSED, f"Market '{market.name}' is not open")
    # Open-session bets (and jodi/sangam, which need the open result) stop at the cutoff; close-session
    # bets stay open until the market closes. This matches the app's OPENING -> CLOSING session states.
    deadline = market.closing_time if stage == "CLOSE" and market.closing_time else (market.cutoff_time or market.closing_time)
    if _cutoff_passed(deadline, market.timezone):
        raise AppError(CUTOFF_PASSED, f"Market '{market.name}' cutoff has passed")


def assert_slot_open(slot: StarlineSlot, market: Market) -> None:
    if not slot.enabled:
        raise AppError(SLOT_CLOSED, f"Slot '{slot.slot_name}' is not open")
    if _cutoff_passed(slot.cutoff_time, market.timezone):
        raise AppError(SLOT_CLOSED, f"Slot '{slot.slot_name}' cutoff has passed")
