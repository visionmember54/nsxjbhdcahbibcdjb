from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends
from app.core.deps import get_db
from app.models.market_result import MarketResult
from app.schemas.common import Page, PageParams
from app.schemas.result import MarketResultOut

router = APIRouter(prefix="/results", tags=["public-results"])


def _result_out(result: MarketResult) -> MarketResultOut:
    return MarketResultOut(
        id=result.id, marketId=result.market_id, slotId=result.slot_id, date=result.result_date,
        openPanna=result.open_panna, openAnk=result.open_ank, closePanna=result.close_panna,
        closeAnk=result.close_ank, jodi=result.jodi, singleResult=result.single_result, status=result.status,
        publishedAt=result.published_at, correctedFromId=result.corrected_from_id,
    )


@router.get("", response_model=Page[MarketResultOut])
async def list_results(
    pagination: PageParams = Depends(),
    market_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(MarketResult).filter(MarketResult.status == "Published")
    if market_id is not None:
        query = query.filter(MarketResult.market_id == market_id)
    total = query.count()
    rows = query.order_by(MarketResult.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    return Page(items=[_result_out(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


@router.get("/history", response_model=Page[MarketResultOut])
async def result_history(
    pagination: PageParams = Depends(),
    market_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(MarketResult).filter(MarketResult.status.in_(["Published", "Corrected"]))
    if market_id is not None:
        query = query.filter(MarketResult.market_id == market_id)
    if date_from:
        query = query.filter(MarketResult.result_date >= date_from)
    if date_to:
        query = query.filter(MarketResult.result_date <= date_to)
    total = query.count()
    rows = query.order_by(MarketResult.result_date.desc()).limit(pagination.limit).offset(pagination.offset).all()
    return Page(items=[_result_out(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)
