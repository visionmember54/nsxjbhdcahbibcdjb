from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreditRequestCreate(BaseModel):
    requested_amount: int = Field(gt=0, le=1_000_000)
    reason: str | None = Field(default=None, max_length=500)


class CreditRequestReview(BaseModel):
    admin_note: str | None = Field(default=None, max_length=500)


class CreditRequestOut(BaseModel):
    id: int
    userId: int
    userName: str
    userPhone: str
    requestedAmount: int
    requestType: str
    utrNumber: str | None = None
    screenshotUrl: str | None = None
    paymentDetails: str | None = None
    reason: str | None
    status: str
    adminNote: str | None
    reviewedByAdminId: int | None
    reviewedAt: datetime | None
    createdAt: datetime

    model_config = {"populate_by_name": True}
