from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CreditRequest(Base):
    """A user's ask for more virtual Learning Credits, reviewed by an admin.

    Deliberately has no payment-reference field of any kind -- approving a
    request grants credits for free (an educational allowance), the same way
    an admin's manual grant already works. There is no real-money concept
    anywhere in this table.
    """

    __tablename__ = "credit_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    request_type: Mapped[str] = mapped_column(String(20), default="Deposit") # Deposit or Withdrawal
    requested_amount: Mapped[int] = mapped_column(Integer)
    utr_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    screenshot_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_details: Mapped[str | None] = mapped_column(Text, nullable=True) # E.g., UPI ID for withdrawal
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pending", index=True)  # Pending|Approved|Rejected
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
