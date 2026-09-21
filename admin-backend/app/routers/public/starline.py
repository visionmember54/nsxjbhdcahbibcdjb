from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.market import Market, MarketCategory, StarlineSlot
from app.schemas.market import MarketOut
from app.schemas.starline import StarlineSlotOut

router = APIRouter(prefix="/starline", tags=["public-starline"])


@router.get("", response_model=list[MarketOut])
async def list_starline_markets(db: Session = Depends(get_db)):
    rows = (
        db.query(Market, MarketCategory.slug)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(MarketCategory.slug == "STARLINE")
        .order_by(Market.display_order)
        .all()
    )
    return [
        MarketOut(
            id=m.id, category_id=m.category_id, category=slug, name=m.name, slug=m.slug, description=m.description,
            status=m.status, timezone=m.timezone, opening_time=m.opening_time, closing_time=m.closing_time,
            cutoff_time=m.cutoff_time, result_time=m.result_time, display_order=m.display_order,
        )
        for m, slug in rows
    ]


@router.get("/{market_id}/slots", response_model=list[StarlineSlotOut])
async def list_starline_slots(market_id: int, db: Session = Depends(get_db)):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    rows = (
        db.query(StarlineSlot)
        .filter(StarlineSlot.market_id == market_id, StarlineSlot.enabled.is_(True))
        .order_by(StarlineSlot.display_order)
        .all()
    )
    return [StarlineSlotOut.model_validate(r) for r in rows]
