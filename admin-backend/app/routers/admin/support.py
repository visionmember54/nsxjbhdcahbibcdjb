from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.user import User
from app.models.support import SupportMessage, SupportQuery
from app.schemas.common import Page, PageParams
from app.schemas.support import QueryCreate, QueryMessageOut, ReplyCreate, SupportQueryOut
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/queries", tags=["support"])


def _query_out(db: Session, q: SupportQuery, user_name: str) -> SupportQueryOut:
    messages = db.query(SupportMessage).filter(SupportMessage.query_id == q.id).order_by(SupportMessage.id.asc()).all()
    return SupportQueryOut(
        id=q.id, user=user_name, subject=q.subject, status=q.status, priority=q.priority, updatedAt=q.updated_at,
        messages=[QueryMessageOut.model_validate(m) for m in messages],
    )


@router.get("", response_model=Page[SupportQueryOut])
async def list_queries(
    pagination: PageParams = Depends(),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total = db.query(SupportQuery).count()
    rows = (
        db.query(SupportQuery, User.name)
        .join(User, User.id == SupportQuery.user_id)
        .order_by(SupportQuery.id.desc())
        .limit(pagination.limit).offset(pagination.offset).all()
    )
    items = [_query_out(db, q, name) for q, name in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.post("", response_model=SupportQueryOut, status_code=status.HTTP_201_CREATED)
async def create_query(
    payload: QueryCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    now = datetime.now(timezone.utc)
    query = SupportQuery(user_id=user.id, subject=payload.subject, status="Open", priority=payload.priority, updated_at=now.strftime("%Y-%m-%d %H:%M:%S"))
    db.add(query)
    db.flush()
    db.add(SupportMessage(query_id=query.id, sender="user", text=payload.message, time=now.strftime("%H:%M %p")))
    db.add(AuditLog(actor=current_admin.name, action="support_ticket_created", details=f"Ticket created for {user.name}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(query)
    return _query_out(db, query, user.name)


@router.post("/{query_id}/reply", response_model=SupportQueryOut)
async def reply_to_query(
    query_id: int,
    payload: ReplyCreate,
    current_admin: Admin = Depends(require_permission("support.manage")),
    db: Session = Depends(get_db),
):
    query = db.get(SupportQuery, query_id)
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")

    now = datetime.now(timezone.utc)
    db.add(SupportMessage(query_id=query_id, sender="admin", text=payload.message, time=now.strftime("%H:%M %p")))
    query.status = "Pending"
    query.updated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    db.add(AuditLog(actor=current_admin.name, action="support_reply", details=f"Replied to ticket #{query_id}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(query)
    user = db.get(User, query.user_id)
    return _query_out(db, query, user.name if user else "")
