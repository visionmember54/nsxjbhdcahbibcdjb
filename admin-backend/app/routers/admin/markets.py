from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.market import Market, MarketCategory
from app.schemas.common import Page, PageParams
from app.schemas.market import MarketCreate, MarketOut, MarketStatusUpdate, MarketUpdate
from app.services import market_service
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/markets", tags=["markets"])


def _market_out(market: Market, category_slug: str) -> MarketOut:
    return MarketOut(
        id=market.id, category_id=market.category_id, category=category_slug, name=market.name, slug=market.slug,
        description=market.description, status=market.status, timezone=market.timezone,
        opening_time=market.opening_time, closing_time=market.closing_time, cutoff_time=market.cutoff_time,
        result_time=market.result_time, display_order=market.display_order,
    )


@router.get("", response_model=Page[MarketOut])
async def list_markets(
    pagination: PageParams = Depends(),
    category: str | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Market, MarketCategory.slug).join(MarketCategory, MarketCategory.id == Market.category_id)
    if category:
        query = query.filter(MarketCategory.slug == category.upper())
    total = query.count()
    rows = query.order_by(Market.display_order, Market.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    items = [_market_out(m, slug) for m, slug in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.post("", response_model=MarketOut, status_code=status.HTTP_201_CREATED)
async def create_market(
    payload: MarketCreate,
    current_admin: Admin = Depends(require_permission("markets.manage")),
    db: Session = Depends(get_db),
):
    category = db.get(MarketCategory, payload.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market category not found")
    if db.query(Market).filter(Market.slug == payload.slug).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A market with this slug already exists")

    market = Market(
        category_id=payload.category_id, name=payload.name, slug=payload.slug, description=payload.description,
        status="UPCOMING", timezone=payload.timezone, opening_time=payload.opening_time,
        closing_time=payload.closing_time, cutoff_time=payload.cutoff_time, result_time=payload.result_time,
        display_order=payload.display_order,
    )
    db.add(market)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="market_created", details=f"Market created: {market.name} ({category.slug}, created_at={datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')})"))
    db.commit()
    db.refresh(market)
    return _market_out(market, category.slug)


@router.patch("/{market_id}", response_model=MarketOut)
async def update_market(
    market_id: int,
    payload: MarketUpdate,
    current_admin: Admin = Depends(require_permission("markets.manage")),
    db: Session = Depends(get_db),
):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(market, field, value)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="market_updated", details=f"Market updated: {market.name}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(market)
    category = db.get(MarketCategory, market.category_id)
    return _market_out(market, category.slug)


@router.post("/{market_id}/status", response_model=MarketOut)
async def update_market_status(
    market_id: int,
    payload: MarketStatusUpdate,
    current_admin: Admin = Depends(require_permission("markets.manage")),
    db: Session = Depends(get_db),
):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    previous = market.status
    market_service.transition_status(db, market, payload.status)
    db.add(AuditLog(actor=current_admin.name, action="market_status_changed", details=f"{market.name}: {previous} -> {market.status}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(market)
    category = db.get(MarketCategory, market.category_id)
    return _market_out(market, category.slug)
