from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.audit import AuditLog
from app.models.credit_request import CreditRequest
from app.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.credit_request import CreditRequestOut, CreditRequestReview
from app.services import credit_service

router = APIRouter(prefix="/admin/credit-requests", tags=["credit-requests"])


def _out(req: CreditRequest, user: User) -> CreditRequestOut:
    return CreditRequestOut(
        id=req.id, userId=req.user_id, userName=user.name, userPhone=user.phone,
        requestedAmount=req.requested_amount, requestType=req.request_type, utrNumber=req.utr_number, screenshotUrl=req.screenshot_url, paymentDetails=req.payment_details, reason=req.reason, status=req.status,
        adminNote=req.admin_note, reviewedByAdminId=req.reviewed_by_admin_id,
        reviewedAt=req.reviewed_at, createdAt=req.created_at,
    )


@router.get("", response_model=Page[CreditRequestOut])
async def list_credit_requests(
    pagination: PageParams = Depends(),
    status_filter: str | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(CreditRequest, User).join(User, User.id == CreditRequest.user_id)
    if status_filter:
        query = query.filter(CreditRequest.status == status_filter)
    total = query.count()
    rows = query.order_by(CreditRequest.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    return Page(items=[_out(r, u) for r, u in rows], total=total, limit=pagination.limit, offset=pagination.offset)


@router.post("/{request_id}/approve", response_model=CreditRequestOut)
async def approve_credit_request(
    request_id: int,
    payload: CreditRequestReview,
    current_admin: Admin = Depends(require_permission("credits.manage")),
    db: Session = Depends(get_db),
):
    req = db.get(CreditRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit request not found")
    if req.status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request is already {req.status}, not Pending")

    user = db.get(User, req.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if req.request_type.lower() == "deposit":
        credit_service.apply_ledger_entry(
            db, user=user, type="grant", amount=req.requested_amount,
            reference_type="credit_request", reference_id=str(req.id),
            created_by_admin_id=current_admin.id,
            note=f"Deposit request #{req.id} approved" + (f": {req.reason}" if req.reason else ""),
        )
    # A withdrawal was already deducted as a hold when requested, so approving it moves no money and
    # writes no ledger row; the hold row's linked request status is what shows it as settled.

    req.status = "Approved"
    req.admin_note = payload.admin_note
    req.reviewed_by_admin_id = current_admin.id
    req.reviewed_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        actor=current_admin.name, action="credit_request_approved",
        details=f"Approved {req.request_type} request #{req.id} for {user.name}",
        subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    ))
    db.commit()
    db.refresh(req)
    return _out(req, user)


@router.post("/{request_id}/reject", response_model=CreditRequestOut)
async def reject_credit_request(
    request_id: int,
    payload: CreditRequestReview,
    current_admin: Admin = Depends(require_permission("credits.manage")),
    db: Session = Depends(get_db),
):
    req = db.get(CreditRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit request not found")
    if req.status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request is already {req.status}, not Pending")

    user = db.get(User, req.user_id)

    if req.request_type.lower() == "withdrawal" and user:
        # Refund the hold
        credit_service.apply_ledger_entry(
            db, user=user, type="refund", amount=req.requested_amount,
            reference_type="credit_request", reference_id=str(req.id),
            created_by_admin_id=current_admin.id,
            note=f"Withdrawal request #{req.id} rejected, amount refunded" + (f": {payload.admin_note}" if payload.admin_note else ""),
        )

    req.status = "Rejected"
    req.admin_note = payload.admin_note
    req.reviewed_by_admin_id = current_admin.id
    req.reviewed_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        actor=current_admin.name, action="credit_request_rejected",
        details=f"Rejected {req.request_type} request #{req.id} for {user.name if user else req.user_id}",
        subject_user_id=req.user_id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    ))
    db.commit()
    db.refresh(req)
    return _out(req, user)
