from __future__ import annotations

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field, computed_field, field_serializer

from app.services.app_api_service import iso_ist


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=6, max_length=20)
    email: str = ""
    password: str = Field(min_length=6, max_length=255)


class UserLogin(BaseModel):
    phone: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    status: str
    balance: int
    last_seen: datetime | None = None
    created_at: datetime
    # Pulled from the ORM column but never serialized raw -- only whether one exists (see below).
    fcm_token: str | None = Field(default=None, exclude=True)

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def has_fcm_token(self) -> bool:
        return bool(self.fcm_token)

    # Stored naive-UTC (no offset) -- serialize with the explicit +05:30 IST offset so the
    # admin panel's `new Date(...)` doesn't misread it as already-local time and shift it.
    @field_serializer("last_seen", "created_at")
    def _serialize_ist(self, value: datetime | None) -> str | None:
        return iso_ist(value)


class UserStatsOut(BaseModel):
    total_added: int
    total_withdrawn: int
    overall_in: int
    overall_out: int


class UserPaymentInfoOut(BaseModel):
    id: int
    payment_method: str
    account_name: str | None = None
    account_number: str | None = None
    ifsc_code: str | None = None
    upi_id: str | None = None

    model_config = {"from_attributes": True}


class UserWithdrawalOut(BaseModel):
    id: int
    requested_amount: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def _serialize_ist(self, value: datetime) -> str | None:
        return iso_ist(value)


class UserBidOut(BaseModel):
    id: int
    game_name: str
    game_type: str
    session: str | None = None
    selection: str
    points: int
    created_at: datetime
    status: str

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def _serialize_ist(self, value: datetime) -> str | None:
        return iso_ist(value)


class UserTransactionOut(BaseModel):
    id: int
    type: str
    amount: int
    balance_after: int
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def _serialize_ist(self, value: datetime) -> str | None:
        return iso_ist(value)


class UserWinningOut(BaseModel):
    id: int
    date: datetime
    game_name: str
    winning_amount: int

    model_config = {"from_attributes": True}

    @field_serializer("date")
    def _serialize_ist(self, value: datetime) -> str | None:
        return iso_ist(value)


class UserTokenResponse(BaseModel):
    token: str
    user: UserOut


class UserCreatedOut(UserOut):
    temporary_password: str | None = None


class UserUpdate(BaseModel):
    status: Literal["active", "disabled"] | None = None
    reason: str | None = Field(default=None, max_length=500)


class UserCreate(BaseModel):
    """Admin-created user account (mirrors the prior manual-entry pattern)."""

    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=6, max_length=20)
    email: str = ""
    # Omit to have the server generate a random temporary password (returned once on create).
    password: str | None = Field(min_length=8, max_length=255, default=None)


class UserNotifyRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=500)
