from __future__ import annotations

from datetime import datetime, time, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketCategory(Base):
    """Not a hardcoded enum: admin can add categories beyond the seeded
    MATKA/STARLINE/GALI_DISAWAR/CUSTOM without a backend deploy."""

    __tablename__ = "market_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class Market(Base):
    """Covers MATKA and GALI_DISAWAR-shaped markets (single opening/closing/result
    time). STARLINE-category markets use this row as the umbrella container; the
    actual per-time-window config lives on StarlineSlot."""

    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("market_categories.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(20), default="UPCOMING")
    timezone: Mapped[str] = mapped_column(String(60), default="Asia/Kolkata")
    opening_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    closing_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    cutoff_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    result_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class StarlineSlot(Base):
    """A daily time window under a STARLINE-category Market (spec: 10:00 AM,
    11:00 AM, 12:00 PM, ... each independently configurable)."""

    __tablename__ = "starline_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), index=True)
    slot_name: Mapped[str] = mapped_column(String(60))
    start_time: Mapped[time] = mapped_column(Time)
    cutoff_time: Mapped[time] = mapped_column(Time)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
