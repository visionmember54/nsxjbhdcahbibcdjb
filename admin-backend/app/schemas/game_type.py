from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GameTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=80)
    description: str = ""
    digit_length: int = Field(ge=1, le=7, default=1)
    classification_rule: Literal["NONE", "PANNA_SINGLE", "PANNA_DOUBLE", "PANNA_TRIPLE", "SANGAM_HALF", "SANGAM_FULL"] = "NONE"
    display_order: int = 0


class GameTypeUpdate(BaseModel):
    is_active: bool | None = None
    display_order: int | None = None


class GameTypeOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    digit_length: int
    classification_rule: str
    is_active: bool
    display_order: int

    model_config = {"from_attributes": True}
