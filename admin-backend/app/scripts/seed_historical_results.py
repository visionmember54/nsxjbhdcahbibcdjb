"""Backfills synthetic (clearly not-real) historical results so the Panel
Chart and reports have something to show across a real date range, without
touching any existing data. Idempotent -- skips any market/date that already
has a Published/Corrected result. Run with:

    python -m app.scripts.seed_historical_results [days_back]
"""
from __future__ import annotations

import random
import sys
from datetime import date, timedelta

from app.db.base import SessionLocal
from app.models.admin import Admin
from app.models.market import Market, MarketCategory
from app.models.market_result import MarketResult
from app.services import result_service

SINGLE_DRAW_CATEGORIES = {"STARLINE", "GALI_DISAWAR"}


def _random_panna() -> str:
    return f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"


def run(days_back: int = 60) -> None:
    db = SessionLocal()
    try:
        admin = db.query(Admin).order_by(Admin.id.asc()).first()
        if not admin:
            print("No admin account found -- run app.seed first.")
            return

        markets = db.query(Market).all()
        if not markets:
            print("No markets found -- run app.seed first.")
            return
        category_slug_by_id = {c.id: c.slug for c in db.query(MarketCategory).all()}

        existing = {
            (r.market_id, r.result_date)
            for r in db.query(MarketResult.market_id, MarketResult.result_date)
            .filter(MarketResult.slot_id.is_(None), MarketResult.status.in_(["Published", "Corrected"]))
            .all()
        }

        created = 0
        today = date.today()
        for offset in range(1, days_back + 1):
            result_date = (today - timedelta(days=offset)).isoformat()
            for market in markets:
                if (market.id, result_date) in existing:
                    continue

                category_slug = category_slug_by_id.get(market.category_id, "")
                if category_slug in SINGLE_DRAW_CATEGORIES:
                    result_service.upsert_result(
                        db, market_id=market.id, slot_id=None, result_date=result_date,
                        open_panna=None, open_ank=str(random.randint(0, 9)),
                        close_panna=None, close_ank=None, single_result=None,
                        publish=True, admin_id=admin.id,
                    )
                else:
                    result_service.upsert_result(
                        db, market_id=market.id, slot_id=None, result_date=result_date,
                        open_panna=_random_panna(), open_ank=None,
                        close_panna=_random_panna(), close_ank=None, single_result=None,
                        publish=True, admin_id=admin.id,
                    )
                created += 1

        db.commit()
        print(f"Backfilled {created} synthetic historical results across {len(markets)} markets, {days_back} days back.")
    finally:
        db.close()


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    run(days)
