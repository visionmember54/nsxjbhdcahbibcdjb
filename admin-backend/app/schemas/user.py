from __future__ import annotations

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field


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

    model_config = {"from_attributes": True}


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


class UserTransactionOut(BaseModel):
    id: int
    type: str
    amount: int
    balance_after: int
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWinningOut(BaseModel):
    id: int
    date: datetime
    game_name: str
    winning_amount: int

    model_config = {"from_attributes": True}


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
