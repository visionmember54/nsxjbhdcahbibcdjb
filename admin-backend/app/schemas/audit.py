from __future__ import annotations

from pydantic import BaseModel, Field


class AuditLogOut(BaseModel):
    id: int
    actor: str
    action: str
    details: str
    subjectUserId: int | None = Field(default=None, validation_alias="subject_user_id")
    createdAt: str = Field(default="", validation_alias="created_at")

    model_config = {"from_attributes": True, "populate_by_name": True}
