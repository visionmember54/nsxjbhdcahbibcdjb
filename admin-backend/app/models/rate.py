from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Rate(Base):
    """Simulated payout rate scoped to (market|slot) x game_type, time-versioned
    via effective_from. 'Current rate' = latest Active row for a combo."""

    __tablename__ = "rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), index=True)
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("starline_slots.id"), nullable=True, index=True)
    game_type_id: Mapped[int] = mapped_column(ForeignKey("game_types.id"), index=True)
    rate: Mapped[int] = mapped_column(Integer)
    effective_from: Mapped[date_type] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="Active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
