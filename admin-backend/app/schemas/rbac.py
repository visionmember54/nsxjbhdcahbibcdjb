from __future__ import annotations

from pydantic import BaseModel, Field


class PermissionOut(BaseModel):
    id: int
    code: str
    description: str

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=80)


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str]


class RoleOut(BaseModel):
    id: int
    slug: str
    name: str
    permissions: list[str]
