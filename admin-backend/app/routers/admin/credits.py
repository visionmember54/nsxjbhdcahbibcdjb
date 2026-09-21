from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.core.errors import INSUFFICIENT_LEARNING_CREDITS, AppError
from app.models.admin import Admin
from app.models.credit import CreditLedger
from app.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.credit import CreditAdjustment, CreditGrant, CreditLedgerOut, CreditReset, GlobalCreditLedgerOut
from app.schemas.user import UserOut
from app.services import credit_service
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/users/{user_id}/credits", tags=["credits"])
global_router = APIRouter(prefix="/admin/credit-ledger", tags=["credits"])


@global_router.get("", response_model=Page[GlobalCreditLedgerOut])
async def global_ledger(
    pagination: PageParams = Depends(),
    type_filter: str | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Every credit movement, across every user -- the wallet-wide view that
    the per-user /credits/history endpoint above deliberately doesn't give."""
    query = db.query(CreditLedger, User).join(User, User.id == CreditLedger.user_id)
    if type_filter:
        query = query.filter(CreditLedger.type == type_filter)
    total = query.count()
    rows = query.order_by(CreditLedger.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    items = [
        GlobalCreditLedgerOut(
            id=r.id, userId=r.user_id, userName=u.name, userPhone=u.phone, type=r.type, amount=r.amount,
            balanceAfter=r.balance_after, referenceType=r.reference_type, referenceId=r.reference_id,
            note=r.note, visibleToUser=r.visible_to_user, createdAt=r.created_at,
        )
        for r, u in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/grant", response_model=UserOut)
async def grant(
    user_id: int,
    payload: CreditGrant,
    current_admin: Admin = Depends(require_permission("credits.manage")),
    db: Session = Depends(get_db),
):
    user = _get_user(db, user_id)
    credit_service.grant_credits(db, user, payload.amount, current_admin.id, payload.note, payload.visibleToUser)
    db.add(AuditLog(actor=current_admin.name, action="credits_granted", details=f"Granted {payload.amount} credits to {user.name}", subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/adjust", response_model=UserOut)
async def adjust(
    user_id: int,
    payload: CreditAdjustment,
    current_admin: Admin = Depends(require_permission("credits.manage")),
    db: Session = Depends(get_db),
):
    user = _get_user(db, user_id)
    try:
        credit_service.adjust_credits(db, user, payload.amount, current_admin.id, payload.note, payload.visibleToUser)
    except credit_service.InsufficientCreditsError:
        raise AppError(INSUFFICIENT_LEARNING_CREDITS, "Adjustment would take balance below zero")
    db.add(AuditLog(actor=current_admin.name, action="credits_adjusted", details=f"Adjusted {user.name} by {payload.amount} credits", subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/reset", response_model=UserOut)
async def reset(
    user_id: int,
    payload: CreditReset,
    current_admin: Admin = Depends(require_permission("credits.manage")),
    db: Session = Depends(get_db),
):
    user = _get_user(db, user_id)
    credit_service.reset_credits(db, user, payload.new_balance, current_admin.id, payload.note, payload.visibleToUser)
    db.add(AuditLog(actor=current_admin.name, action="credits_reset", details=f"Reset {user.name} balance to {payload.new_balance}", subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/history", response_model=Page[CreditLedgerOut])
async def history(
    user_id: int,
    pagination: PageParams = Depends(),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _get_user(db, user_id)
    total = db.query(CreditLedger).filter(CreditLedger.user_id == user_id).count()
    rows = (
        db.query(CreditLedger)
        .filter(CreditLedger.user_id == user_id)
        .order_by(CreditLedger.id.desc())
        .limit(pagination.limit).offset(pagination.offset).all()
    )
    items = [
        CreditLedgerOut(
            id=r.id, user_id=r.user_id, type=r.type, amount=r.amount, balanceAfter=r.balance_after,
            referenceType=r.reference_type, referenceId=r.reference_id, note=r.note,
            visibleToUser=r.visible_to_user, createdAt=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)
