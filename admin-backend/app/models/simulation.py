from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SimulationBatch(Base):
    """Groups one or more SimulationEntry rows submitted together. A single
    (non-bulk) placement transparently creates a 1-entry batch so the result
    engine's evaluation code path is always uniform."""

    __tablename__ = "simulation_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), index=True)
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("starline_slots.id"), nullable=True)
    game_type_id: Mapped[int] = mapped_column(ForeignKey("game_types.id"))
    stage: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_via: Mapped[str] = mapped_column(String(20), default="admin_manual")  # admin_manual|api_bulk
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class SimulationEntry(Base):
    __tablename__ = "simulation_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("simulation_batches.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), index=True)
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("starline_slots.id"), nullable=True)
    game_type_id: Mapped[int] = mapped_column(ForeignKey("game_types.id"))
    stage: Mapped[str | None] = mapped_column(String(10), nullable=True)
    selection: Mapped[str] = mapped_column(String(10))
    # Required for HALF_SANGAM so its two payout directions remain explicit.
    game_variant: Mapped[str | None] = mapped_column(String(30), nullable=True)
    simulated_credits: Mapped[int] = mapped_column(Integer)
    simulated_rate: Mapped[int] = mapped_column(Integer)
    simulated_return: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="Pending")  # Pending|Won|Lost|Cancelled
    result_id: Mapped[int | None] = mapped_column(ForeignKey("market_results.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Individual outcome override -- distinct from a market result
    # correction. `status` above is overwritten with the new outcome;
    # `original_status` preserves what the Result Engine originally decided.
    original_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    override_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # null | OVERRIDDEN
    override_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    overridden_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"), nullable=True)
    overridden_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
