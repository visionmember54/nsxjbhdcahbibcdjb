from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CreditRequest(Base):
    """A deposit/withdrawal request with optional UPI references.

    Deposit order references support idempotency and status lookup; they do not
    prove settlement. Approval remains an explicit admin action.
    """

    __tablename__ = "credit_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    request_type: Mapped[str] = mapped_column(String(20), default="Deposit") # Deposit or Withdrawal
    requested_amount: Mapped[int] = mapped_column(Integer)
    order_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    upi_app: Mapped[str | None] = mapped_column(String(32), nullable=True)
    utr_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    screenshot_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_details: Mapped[str | None] = mapped_column(Text, nullable=True) # E.g., UPI ID for withdrawal
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pending", index=True)  # Pending|Approved|Rejected
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
