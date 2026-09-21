from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.core.security import hash_password
from app.models.admin import Admin
from app.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.user import UserCreate, UserCreatedOut, UserOut, UserUpdate, UserStatsOut, UserPaymentInfoOut, UserWithdrawalOut, UserBidOut, UserTransactionOut, UserWinningOut
from app.models.credit import CreditLedger
from app.models.credit_request import CreditRequest
from app.models.user_payment_info import UserPaymentInfo
from app.models.simulation import SimulationEntry, SimulationBatch
from app.models.market import Market
from app.models.game_type import GameType
from sqlalchemy import func
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/users", tags=["users"])


@router.get("", response_model=Page[UserOut])
async def list_users(
    pagination: PageParams = Depends(),
    search: str | None = Query(default=None, max_length=120),
    status_filter: str | None = Query(default=None, alias="status"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search:
        needle = f"%{search.strip()}%"
        query = query.filter(or_(User.name.ilike(needle), User.phone.ilike(needle), User.email.ilike(needle)))
    if status_filter in {"active", "disabled"}:
        query = query.filter(User.status == status_filter)
    total = query.count()
    rows = query.order_by(User.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    return Page(items=[UserOut.model_validate(u) for u in rows], total=total, limit=pagination.limit, offset=pagination.offset)


@router.post("", response_model=UserCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_admin: Admin = Depends(require_permission("users.manage")),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this phone number already exists")

    temporary_password = None if payload.password else secrets.token_urlsafe(9)
    user = User(
        name=payload.name, phone=payload.phone, email=payload.email,
        password_hash=hash_password(payload.password or temporary_password), status="active", balance=0,
    )
    db.add(user)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="user_created", details=f"User created: {user.name}", subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(user)
    return UserCreatedOut(**UserOut.model_validate(user).model_dump(), temporary_password=temporary_password)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_admin: Admin = Depends(require_permission("users.manage")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.status is not None:
        previous = user.status
        user.status = payload.status
    db.flush()
    details = f"User status changed: {user.name}: {previous} -> {user.status}" if payload.status is not None else f"User updated: {user.name}"
    if payload.reason:
        details = f"{details}. Reason: {payload.reason.strip()}"
    db.add(AuditLog(actor=current_admin.name, action="user_updated", details=details, subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)

@router.get("/{user_id}/stats", response_model=UserStatsOut)
async def get_user_stats(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_added = db.query(func.sum(CreditRequest.requested_amount)).filter(
        CreditRequest.user_id == user_id,
        CreditRequest.request_type == "Deposit",
        CreditRequest.status == "Approved"
    ).scalar() or 0

    total_withdrawn = db.query(func.sum(CreditRequest.requested_amount)).filter(
        CreditRequest.user_id == user_id,
        CreditRequest.request_type == "Withdrawal",
        CreditRequest.status == "Approved"
    ).scalar() or 0

    overall_in = db.query(func.sum(CreditLedger.amount)).filter(
        CreditLedger.user_id == user_id,
        CreditLedger.amount > 0
    ).scalar() or 0

    overall_out = db.query(func.sum(CreditLedger.amount)).filter(
        CreditLedger.user_id == user_id,
        CreditLedger.amount < 0
    ).scalar() or 0

    return UserStatsOut(
        total_added=total_added,
        total_withdrawn=total_withdrawn,
        overall_in=overall_in,
        overall_out=abs(overall_out)
    )

@router.get("/{user_id}/payment-info", response_model=list[UserPaymentInfoOut])
async def get_user_payment_info(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    payment_info = db.query(UserPaymentInfo).filter(UserPaymentInfo.user_id == user_id).all()
    return [UserPaymentInfoOut.model_validate(info) for info in payment_info]

@router.get("/{user_id}/withdrawals", response_model=list[UserWithdrawalOut])
async def get_user_withdrawals(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    withdrawals = db.query(CreditRequest).filter(
        CreditRequest.user_id == user_id,
        CreditRequest.request_type == "Withdrawal"
    ).order_by(CreditRequest.created_at.desc()).all()
    
    return [UserWithdrawalOut(
        id=w.id,
        requested_amount=w.requested_amount,
        status=w.status,
        created_at=w.created_at
    ) for w in withdrawals]

@router.get("/{user_id}/bids", response_model=list[UserBidOut])
async def get_user_bids(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    bids = db.query(SimulationEntry, Market, GameType).join(
        Market, SimulationEntry.market_id == Market.id
    ).join(
        GameType, SimulationEntry.game_type_id == GameType.id
    ).filter(
        SimulationEntry.user_id == user_id,
        ~Market.slug.in_(["gali", "disawar", "starline"])
    ).order_by(SimulationEntry.created_at.desc()).all()

    return [UserBidOut(
        id=entry.id,
        game_name=market.name,
        game_type=game_type.name,
        session=entry.stage,
        selection=entry.selection,
        points=entry.simulated_credits,
        created_at=entry.created_at,
        status=entry.status
    ) for entry, market, game_type in bids]

@router.get("/{user_id}/transactions", response_model=list[UserTransactionOut])
async def get_user_transactions(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    transactions = db.query(CreditLedger).filter(
        CreditLedger.user_id == user_id
    ).order_by(CreditLedger.created_at.desc()).all()

    return [UserTransactionOut(
        id=t.id,
        type=t.type,
        amount=t.amount,
        balance_after=t.balance_after,
        note=t.note,
        created_at=t.created_at
    ) for t in transactions]

@router.get("/{user_id}/winnings", response_model=list[UserWinningOut])
async def get_user_winnings(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    winnings = db.query(SimulationEntry, Market).join(
        Market, SimulationEntry.market_id == Market.id
    ).filter(
        SimulationEntry.user_id == user_id,
        SimulationEntry.status == "Won"
    ).order_by(SimulationEntry.created_at.desc()).all()

    return [UserWinningOut(
        id=entry.id,
        date=entry.created_at,
        game_name=market.name,
        winning_amount=entry.simulated_return
    ) for entry, market in winnings]

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    current_admin: Admin = Depends(require_permission("users.manage")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    temporary_password = secrets.token_urlsafe(9)
    user.password_hash = hash_password(temporary_password)
    db.add(AuditLog(actor=current_admin.name, action="user_password_reset", details=f"Admin reset password for user: {user.name}", subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    return {"message": "Password reset", "temporary_password": temporary_password}
