from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Role is validated against the `roles` table at request time (app/routers/admin/admins.py),
# not restricted to a fixed set here -- admins can define custom roles via /admin/roles.


class AdminCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    role: str = Field(default="admin", min_length=1, max_length=30)


class AdminUpdate(BaseModel):
    status: Literal["active", "disabled"] | None = None
    role: str | None = Field(default=None, min_length=1, max_length=30)


class AdminOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str

    model_config = {"from_attributes": True}
