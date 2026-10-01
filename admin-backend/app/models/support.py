from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SupportQuery(Base):
    __tablename__ = "support_queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="Open")
    priority: Mapped[str] = mapped_column(String(20), default="Normal")
    updated_at: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("support_queries.id"), index=True)
    sender: Mapped[str] = mapped_column(String(10))  # user|admin
    # Nullable because an attachment-only message (a photo or voice note with no
    # caption) is valid -- exactly one of text/attachment_url must be present,
    # enforced in the request schema, not here.
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    time: Mapped[str] = mapped_column(String(20))
    # Points at GET /api/v1/support/chat/attachments/{attachment_id} on this same
    # backend -- the file bytes live in SupportAttachment below, in this app's
    # own Postgres database. No third-party storage service, no new credentials,
    # no cost: Render's web filesystem is ephemeral so local disk was never an
    # option, but the database is already paid for and already durable.
    attachment_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    attachment_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # image|audio


class SupportAttachment(Base):
    """The actual file bytes for one chat attachment, keyed by an unguessable
    UUID (not a sequential id) so a URL can be safely served with no auth check
    -- exactly how every other chat app's media links work (WhatsApp, S3
    presigned URLs, Firebase Storage's own default download links are all
    "public if you have the exact link", not sequential/enumerable)."""

    __tablename__ = "support_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(100))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
