from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QueryMessageOut(BaseModel):
    id: int
    sender: Literal["user", "admin"]
    text: str
    time: str

    model_config = {"from_attributes": True}


class QueryCreate(BaseModel):
    user_id: int
    subject: str = Field(min_length=1, max_length=255)
    priority: Literal["Low", "Normal", "High"] = "Normal"
    message: str = Field(min_length=1)


class ReplyCreate(BaseModel):
    message: str = Field(min_length=1)


class SupportQueryOut(BaseModel):
    id: int
    user: str
    subject: str
    status: str
    priority: str
    updatedAt: str
    messages: list[QueryMessageOut]

    model_config = {"populate_by_name": True}
