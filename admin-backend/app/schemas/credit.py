from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreditGrant(BaseModel):
    amount: int = Field(gt=0, le=10_000_000)
    note: str = Field(min_length=1, max_length=500)
    visibleToUser: bool = True


class CreditAdjustment(BaseModel):
    amount: int = Field(le=10_000_000)  # signed; can be negative
    note: str = Field(min_length=1, max_length=500)
    visibleToUser: bool = True


class CreditReset(BaseModel):
    new_balance: int = Field(ge=0, le=10_000_000)
    note: str = Field(min_length=1, max_length=500)
    visibleToUser: bool = True


class CreditLedgerOut(BaseModel):
    id: int
    user_id: int
    type: str
    amount: int
    balanceAfter: int
    referenceType: str | None
    referenceId: str | None
    note: str | None
    visibleToUser: bool
    createdAt: datetime

    model_config = {"populate_by_name": True}


class GlobalCreditLedgerOut(BaseModel):
    id: int
    userId: int
    userName: str
    userPhone: str
    type: str
    amount: int
    balanceAfter: int
    referenceType: str | None
    referenceId: str | None
    note: str | None
    visibleToUser: bool
    createdAt: datetime
