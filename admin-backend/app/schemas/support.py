from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QueryMessageOut(BaseModel):
    id: int
    sender: Literal["user", "admin"]
    text: str | None
    time: str
    attachment_url: str | None = Field(default=None, serialization_alias="attachmentUrl")
    attachment_type: str | None = Field(default=None, serialization_alias="attachmentType")

    model_config = {"from_attributes": True, "populate_by_name": True}


class QueryCreate(BaseModel):
    user_id: int
    subject: str = Field(min_length=1, max_length=255)
    priority: Literal["Low", "Normal", "High"] = "Normal"
    message: str = Field(min_length=1)


class ReplyCreate(BaseModel):
    message: str | None = Field(default=None, min_length=1)
    attachmentUrl: str | None = None
    attachmentType: Literal["image", "audio"] | None = None

    @model_validator(mode="after")
    def _require_text_or_attachment(self):
        if not self.message and not self.attachmentUrl:
            raise ValueError("Either message or attachmentUrl is required")
        if self.attachmentUrl and not self.attachmentType:
            raise ValueError("attachmentType is required when attachmentUrl is set")
        return self


class StatusUpdate(BaseModel):
    status: Literal["Open", "Pending", "Resolved"]


class SupportQueryOut(BaseModel):
    id: int
    user: str
    subject: str
    status: str
    priority: str
    updatedAt: str
    messages: list[QueryMessageOut]

    model_config = {"populate_by_name": True}
