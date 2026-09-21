from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GameType(Base):
    """The central game-type registry. Seeded with the 8 built-in
    codes; admin can add custom types (digit_length + classification_rule drive
    generic validation for anything beyond the built-ins) without a deploy."""

    __tablename__ = "game_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(500), default="")
    digit_length: Mapped[int] = mapped_column(Integer, default=1)
    # NONE | PANNA_SINGLE | PANNA_DOUBLE | PANNA_TRIPLE
    classification_rule: Mapped[str] = mapped_column(String(20), default="NONE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class GameTypeConfig(Base):
    """The one junction table that drives 'is this game type available here' plus
    all bulk-mode config, for every market/slot x game-type combination (spec
    sec.2/3/6/7/11/33/34 collapse into this single generic row)."""

    __tablename__ = "game_type_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), index=True)
    # null = market-level default; set = slot-level override (Starline)
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("starline_slots.id"), nullable=True, index=True)
    game_type_id: Mapped[int] = mapped_column(ForeignKey("game_types.id"), index=True)
    # null (not stage-scoped) | OPEN | CLOSE | BOTH -- Matka Single/Panna care about this
    stage: Mapped[str | None] = mapped_column(String(10), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    min_credits: Mapped[int] = mapped_column(Integer, default=10)
    max_credits: Mapped[int] = mapped_column(Integer, default=10000)
    bulk_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_bulk_selections: Mapped[int] = mapped_column(Integer, default=50)
    same_amount_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    individual_amount_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    duplicate_selection_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
