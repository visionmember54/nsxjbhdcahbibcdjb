from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db
from app.models.admin import Admin
from app.models.market import Market, MarketCategory
from app.models.simulation import SimulationEntry
from app.models.user import User

router = APIRouter(prefix="/admin/search", tags=["search"])


@router.get("")
async def global_search(
    q: str = Query(min_length=1, max_length=120),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """One box, three jump targets: a user by name/phone/email, a market by
    name, or a bid by its exact numeric id. Read-only and gated only by
    being a logged-in admin -- same as the list endpoints it's shortcutting."""
    stripped = q.strip()
    needle = f"%{stripped}%"

    users = (
        db.query(User)
        .filter(or_(User.name.ilike(needle), User.phone.ilike(needle), User.email.ilike(needle)))
        .order_by(User.id.desc())
        .limit(5)
        .all()
    )
    markets = (
        db.query(Market, MarketCategory.slug)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(Market.name.ilike(needle))
        .order_by(Market.display_order, Market.id)
        .limit(5)
        .all()
    )

    bid = None
    if stripped.isdigit():
        entry = db.get(SimulationEntry, int(stripped))
        if entry:
            user = db.get(User, entry.user_id)
            market = db.get(Market, entry.market_id)
            bid = {
                "id": entry.id,
                "userId": entry.user_id,
                "userName": user.name if user else None,
                "marketId": entry.market_id,
                "marketName": market.name if market else None,
                "selection": entry.selection,
                "status": entry.status,
            }

    return {
        "users": [{"id": u.id, "name": u.name, "phone": u.phone, "email": u.email} for u in users],
        "markets": [{"id": m.id, "name": m.name, "category": slug} for m, slug in markets],
        "bid": bid,
    }
