from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


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


class GameTypeConfigUpdate(BaseModel):
    enabled: bool | None = None
    min_credits: int | None = None
    max_credits: int | None = None
    bulk_enabled: bool | None = None
    max_bulk_selections: int | None = None
    same_amount_allowed: bool | None = None
    individual_amount_allowed: bool | None = None
    duplicate_selection_allowed: bool | None = None


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
