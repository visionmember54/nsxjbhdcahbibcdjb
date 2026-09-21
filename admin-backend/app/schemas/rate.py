from __future__ import annotations

from datetime import date as date_type

from pydantic import BaseModel, Field


class RateCreate(BaseModel):
    market_id: int
    slot_id: int | None = None
    game_type_id: int
    rate: int = Field(gt=0, le=1_000_000, description="Win per 10 credits staked")
    effective_from: date_type


class RateOut(BaseModel):
    id: int
    market_id: int
    slot_id: int | None
    game_type_id: int
    game_type_code: str
    rate: int
    effective_from: date_type
    status: str

    model_config = {"from_attributes": True}
