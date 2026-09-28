from __future__ import annotations

from datetime import time as time_type

from pydantic import BaseModel, Field, field_validator

WEEKDAY_CODES = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}


def _validate_active_days(value: list[str] | None) -> list[str] | None:
    if value is None:
        return None
    codes = [v.strip().upper() for v in value]
    unknown = [c for c in codes if c not in WEEKDAY_CODES]
    if unknown:
        raise ValueError(f"Unknown weekday code(s): {', '.join(unknown)}. Use MON..SUN.")
    return codes or None


class MarketCategoryCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=80)
    display_order: int = 0


class MarketCategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    display_order: int

    model_config = {"from_attributes": True}


class MarketCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=140)
    description: str = ""
    timezone: str = "Asia/Kolkata"
    opening_time: time_type | None = None
    closing_time: time_type | None = None
    cutoff_time: time_type | None = None
    result_time: time_type | None = None
    display_order: int = 0
    visible: bool = True
    active_days: list[str] | None = Field(default=None, description="Subset of MON..SUN this market runs on; omit for every day")

    _validate_active_days = field_validator("active_days")(_validate_active_days)


class MarketUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    opening_time: time_type | None = None
    closing_time: time_type | None = None
    cutoff_time: time_type | None = None
    result_time: time_type | None = None
    display_order: int | None = None
    visible: bool | None = None
    active_days: list[str] | None = None

    _validate_active_days = field_validator("active_days")(_validate_active_days)


class MarketStatusUpdate(BaseModel):
    status: str = Field(description="UPCOMING|OPEN|CLOSED|RESULT_PENDING|RESULT_PUBLISHED|SUSPENDED")


class MarketOut(BaseModel):
    id: int
    category_id: int
    category: str
    name: str
    slug: str
    description: str
    status: str
    timezone: str
    opening_time: time_type | None
    closing_time: time_type | None
    cutoff_time: time_type | None
    result_time: time_type | None
    display_order: int
    visible: bool
    active_days: list[str] | None
    effective_status: str

    model_config = {"from_attributes": True}
