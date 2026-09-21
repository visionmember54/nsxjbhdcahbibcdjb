from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, MarketCategory
from app.schemas.common import Page, PageParams
from app.schemas.game_type_config import GameTypeConfigOut
from app.schemas.market import MarketOut
from app.schemas.rate import RateOut

router = APIRouter(prefix="/markets", tags=["public-markets"])


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
    db: Session = Depends(get_db),
):
    query = db.query(Market, MarketCategory.slug).join(MarketCategory, MarketCategory.id == Market.category_id)
    if category:
        query = query.filter(MarketCategory.slug == category.upper())
    total = query.count()
    rows = query.order_by(Market.display_order, Market.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    items = [_market_out(m, slug) for m, slug in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.get("/{market_id}", response_model=MarketOut)
async def get_market(market_id: int, db: Session = Depends(get_db)):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    category = db.get(MarketCategory, market.category_id)
    return _market_out(market, category.slug)


@router.get("/{market_id}/games", response_model=list[GameTypeConfigOut])
async def get_market_games(market_id: int, slot_id: int | None = None, db: Session = Depends(get_db)):
    """Only enabled game types are returned -- if an admin disables a type here,
    it disappears from what the app would show, with zero frontend changes."""
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    query = (
        db.query(GameTypeConfig, GameType.code)
        .join(GameType, GameType.id == GameTypeConfig.game_type_id)
        .filter(GameTypeConfig.market_id == market_id, GameTypeConfig.enabled.is_(True), GameType.is_active.is_(True))
    )
    query = query.filter(GameTypeConfig.slot_id == slot_id) if slot_id is not None else query.filter(GameTypeConfig.slot_id.is_(None))
    rows = query.all()
    return [
        GameTypeConfigOut(
            id=c.id, market_id=c.market_id, slot_id=c.slot_id, game_type_id=c.game_type_id, game_type_code=code,
            stage=c.stage, enabled=c.enabled, min_credits=c.min_credits, max_credits=c.max_credits,
            bulk_enabled=c.bulk_enabled, max_bulk_selections=c.max_bulk_selections,
            same_amount_allowed=c.same_amount_allowed, individual_amount_allowed=c.individual_amount_allowed,
            duplicate_selection_allowed=c.duplicate_selection_allowed,
        )
        for c, code in rows
    ]


@router.get("/{market_id}/rates", response_model=list[RateOut])
async def get_market_rates(market_id: int, slot_id: int | None = None, db: Session = Depends(get_db)):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    configs = (
        db.query(GameTypeConfig, GameType.code)
        .join(GameType, GameType.id == GameTypeConfig.game_type_id)
        .filter(GameTypeConfig.market_id == market_id, GameTypeConfig.enabled.is_(True))
    )
    configs = configs.filter(GameTypeConfig.slot_id == slot_id) if slot_id is not None else configs.filter(GameTypeConfig.slot_id.is_(None))

    results: list[RateOut] = []
    for config, code in configs.all():
        from datetime import date
        from app.models.rate import Rate
        rate = (
            db.query(Rate)
            .filter(
                Rate.market_id == market_id,
                Rate.slot_id == slot_id,
                Rate.game_type_id == config.game_type_id,
                Rate.status == "Active",
                Rate.effective_from <= date.today(),
            )
            .order_by(Rate.effective_from.desc(), Rate.id.desc())
            .first()
        )
        if rate:
            results.append(RateOut(
                id=rate.id, market_id=rate.market_id, slot_id=rate.slot_id, game_type_id=rate.game_type_id,
                game_type_code=code, rate=rate.rate, effective_from=rate.effective_from, status=rate.status,
            ))
    return results
