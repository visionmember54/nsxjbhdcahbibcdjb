from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.market_result import MarketResult
from app.schemas.common import Page, PageParams
from app.schemas.result import MarketResultOut, ResultCorrection, ResultPreviewOut, ResultPreviewRequest, ResultUpsert
from app.services import result_service
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/results", tags=["results"])


def _result_out(result: MarketResult) -> MarketResultOut:
    return MarketResultOut(
        id=result.id, marketId=result.market_id, slotId=result.slot_id, date=result.result_date,
        openPanna=result.open_panna, openAnk=result.open_ank, closePanna=result.close_panna,
        closeAnk=result.close_ank, jodi=result.jodi, singleResult=result.single_result, status=result.status,
        publishedAt=result.published_at, correctedFromId=result.corrected_from_id,
        correctionReason=result.correction_reason,
    )


@router.get("", response_model=Page[MarketResultOut])
async def list_results(
    pagination: PageParams = Depends(),
    market_id: int | None = None,
    status_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(MarketResult)
    if market_id is not None:
        query = query.filter(MarketResult.market_id == market_id)
    if status_filter is not None:
        query = query.filter(MarketResult.status == status_filter)
    if date_from:
        query = query.filter(MarketResult.result_date >= date_from)
    if date_to:
        query = query.filter(MarketResult.result_date <= date_to)
    total = query.count()
    rows = query.order_by(MarketResult.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    return Page(items=[_result_out(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


@router.post("/preview", response_model=ResultPreviewOut)
async def preview_result(
    payload: ResultPreviewRequest,
    current_admin: Admin = Depends(require_permission("results.manage")),
    db: Session = Depends(get_db),
):
    """Read-only: shows who would win with this draft result, before it's
    saved or published. Nothing is written to the database."""
    preview = result_service.preview_result(
        db, market_id=payload.market_id, slot_id=payload.slot_id,
        open_panna=payload.open_panna, open_ank=payload.open_ank,
        close_panna=payload.close_panna, close_ank=payload.close_ank,
    )
    return ResultPreviewOut(**preview)


@router.post("", response_model=MarketResultOut, status_code=status.HTTP_201_CREATED)
async def upsert_result(
    payload: ResultUpsert,
    current_admin: Admin = Depends(require_permission("results.manage")),
    db: Session = Depends(get_db),
):
    result = result_service.upsert_result(
        db, market_id=payload.market_id, slot_id=payload.slot_id, result_date=payload.date,
        open_panna=payload.open_panna, open_ank=payload.open_ank, close_panna=payload.close_panna,
        close_ank=payload.close_ank, single_result=payload.single_result, publish=payload.publish,
        admin_id=current_admin.id,
    )
    action = "result_published" if payload.publish else "result_draft_saved"
    db.add(AuditLog(actor=current_admin.name, action=action, details=f"Result for market #{payload.market_id} on {payload.date}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(result)
    return _result_out(result)


@router.post("/{result_id}/publish", response_model=MarketResultOut)
async def publish_draft(
    result_id: int,
    current_admin: Admin = Depends(require_permission("results.manage")),
    db: Session = Depends(get_db),
):
    result = db.get(MarketResult, result_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    result = result_service.upsert_result(
        db, market_id=result.market_id, slot_id=result.slot_id, result_date=result.result_date,
        open_panna=None, open_ank=None, close_panna=None, close_ank=None, single_result=None,
        publish=True, admin_id=current_admin.id,
    )
    db.add(AuditLog(actor=current_admin.name, action="result_published", details=f"Draft result #{result_id} published", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(result)
    return _result_out(result)


@router.post("/{result_id}/correct", response_model=MarketResultOut)
async def correct_result(
    result_id: int,
    payload: ResultCorrection,
    current_admin: Admin = Depends(require_permission("results.correct")),
    db: Session = Depends(get_db),
):
    new_result = result_service.correct_result(
        db, result_id=result_id, admin_id=current_admin.id, reason=payload.reason, open_panna=payload.open_panna,
        open_ank=payload.open_ank, close_panna=payload.close_panna, close_ank=payload.close_ank,
        single_result=payload.single_result,
    )
    db.add(AuditLog(actor=current_admin.name, action="result_corrected", details=f"Result #{result_id} corrected -> #{new_result.id}: {payload.reason}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(new_result)
    return _result_out(new_result)


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_result(
    result_id: int,
    current_admin: Admin = Depends(require_permission("results.delete")),
    db: Session = Depends(get_db),
):
    """Single-record delete only -- there is no bulk-delete-by-market endpoint."""
    result = db.get(MarketResult, result_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    db.delete(result)
    db.add(AuditLog(actor=current_admin.name, action="result_deleted", details=f"Result #{result_id} deleted", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
