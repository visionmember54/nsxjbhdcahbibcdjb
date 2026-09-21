from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.market import Market, MarketCategory
from app.schemas.market import MarketOut

router = APIRouter(prefix="/gali-disawar", tags=["public-gali-disawar"])


def _market_out(market: Market, category_slug: str) -> MarketOut:
    return MarketOut(
        id=market.id, category_id=market.category_id, category=category_slug, name=market.name, slug=market.slug,
        description=market.description, status=market.status, timezone=market.timezone,
        opening_time=market.opening_time, closing_time=market.closing_time, cutoff_time=market.cutoff_time,
        result_time=market.result_time, display_order=market.display_order,
    )


@router.get("", response_model=list[MarketOut])
async def list_gali_disawar_markets(db: Session = Depends(get_db)):
    rows = (
        db.query(Market, MarketCategory.slug)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(MarketCategory.slug == "GALI_DISAWAR")
        .order_by(Market.display_order)
        .all()
    )
    return [_market_out(m, slug) for m, slug in rows]


@router.get("/{market_id}", response_model=MarketOut)
async def get_gali_disawar_market(market_id: int, db: Session = Depends(get_db)):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    category = db.get(MarketCategory, market.category_id)
    if category.slug != "GALI_DISAWAR":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    return _market_out(market, category.slug)
