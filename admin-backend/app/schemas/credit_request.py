from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.services.app_api_service import iso_ist


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
    orderId: str | None = None
    transactionId: str | None = None
    upiApp: str | None = None
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

    @field_serializer("reviewedAt", "createdAt")
    def _serialize_ist(self, value: datetime | None) -> str | None:
        return iso_ist(value)
