from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class AdminOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str
    permissions: list[str] = []

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    token: str
    user: AdminOut
