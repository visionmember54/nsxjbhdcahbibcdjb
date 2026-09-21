from __future__ import annotations

from datetime import time as time_type

from pydantic import BaseModel, Field


class StarlineSlotCreate(BaseModel):
    market_id: int
    slot_name: str = Field(min_length=1, max_length=60)
    start_time: time_type
    cutoff_time: time_type
    display_order: int = 0


class StarlineSlotUpdate(BaseModel):
    slot_name: str | None = None
    start_time: time_type | None = None
    cutoff_time: time_type | None = None
    enabled: bool | None = None
    display_order: int | None = None


class StarlineSlotOut(BaseModel):
    id: int
    market_id: int
    slot_name: str
    start_time: time_type
    cutoff_time: time_type
    enabled: bool
    display_order: int

    model_config = {"from_attributes": True}
