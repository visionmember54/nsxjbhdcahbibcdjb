from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GameTypeConfigCreate(BaseModel):
    game_type_id: int
    slot_id: int | None = None
    stage: Literal["OPEN", "CLOSE", "BOTH"] | None = None
    enabled: bool = True
    min_credits: int = 10
    max_credits: int = 10000
    bulk_enabled: bool = True
    max_bulk_selections: int = 50
    same_amount_allowed: bool = True
    individual_amount_allowed: bool = True
    duplicate_selection_allowed: bool = False
    display_order: int = 0


class GameTypeConfigBulkApply(BaseModel):
    """Applies one game type's config to many markets in one call, for
    markets that are meant to all behave the same within a category (e.g.
    every Gali-Disawar market) -- creates the config where it's missing,
    updates it in place where it already exists, so the admin never has to
    open each market individually just to keep them in sync."""

    market_ids: list[int] = Field(min_length=1, max_length=500)
    game_type_id: int
    stage: Literal["OPEN", "CLOSE", "BOTH"] | None = None
    enabled: bool = True
    min_credits: int = 10
    max_credits: int = 10000
    bulk_enabled: bool = True
    max_bulk_selections: int = 50
    same_amount_allowed: bool = True
    individual_amount_allowed: bool = True
    duplicate_selection_allowed: bool = False
    display_order: int = 0


class GameTypeConfigUpdate(BaseModel):
    enabled: bool | None = None
    min_credits: int | None = None
    max_credits: int | None = None
    bulk_enabled: bool | None = None
    max_bulk_selections: int | None = None
    same_amount_allowed: bool | None = None
    individual_amount_allowed: bool | None = None
    duplicate_selection_allowed: bool | None = None
    display_order: int | None = None


class GameTypeConfigOut(BaseModel):
    id: int
    market_id: int
    slot_id: int | None
    game_type_id: int
    game_type_code: str
    stage: str | None
    enabled: bool
    min_credits: int
    max_credits: int
    bulk_enabled: bool
    max_bulk_selections: int
    same_amount_allowed: bool
    individual_amount_allowed: bool
    duplicate_selection_allowed: bool
    display_order: int
