from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketResult(Base):
    """Matka populates open/close/jodi fields; Starline/Gali-Disawar populate
    single_result instead. ank is derived server-side from panna's digit sum,
    jodi from open_ank+close_ank -- never trusted from the client."""

    __tablename__ = "market_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), index=True)
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("starline_slots.id"), nullable=True, index=True)
    result_date: Mapped[str] = mapped_column("date", String(20), index=True)

    open_panna: Mapped[str | None] = mapped_column(String(3), nullable=True)
    open_ank: Mapped[str | None] = mapped_column(String(1), nullable=True)
    close_panna: Mapped[str | None] = mapped_column(String(3), nullable=True)
    close_ank: Mapped[str | None] = mapped_column(String(1), nullable=True)
    jodi: Mapped[str | None] = mapped_column(String(2), nullable=True)
    single_result: Mapped[str | None] = mapped_column(String(10), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="Draft")  # Draft|Published|Corrected
    published_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    corrected_from_id: Mapped[int | None] = mapped_column(ForeignKey("market_results.id"), nullable=True)
    correction_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
