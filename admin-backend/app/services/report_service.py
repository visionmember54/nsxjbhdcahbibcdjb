from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.game_type import GameType
from app.models.market import Market
from app.models.simulation import SimulationEntry


def compute_market_statistics(db: Session) -> list[dict]:
    """Sales/winners/payout/profit per market, computed live from
    SimulationEntry -- never stored, so it can never drift out of sync."""
    markets = db.query(Market).all()
    stats = []
    for market in markets:
        entries = db.query(SimulationEntry).filter(SimulationEntry.market_id == market.id).all()
        if not entries:
            continue
        sales = sum(e.simulated_credits for e in entries)
        won = [e for e in entries if e.status == "Won"]
        payout = sum(e.simulated_return for e in won)
        stats.append({
            "marketId": market.id, "market": market.name, "sales": sales,
            "winners": len(won), "payout": payout, "profit": sales - payout,
        })
    return stats


def compute_game_statistics(db: Session) -> list[dict]:
    """Same rollup, grouped by game type instead of market."""
    rows = (
        db.query(SimulationEntry, GameType.code)
        .join(GameType, GameType.id == SimulationEntry.game_type_id)
        .all()
    )
    by_code: dict[str, list[SimulationEntry]] = {}
    for entry, code in rows:
        by_code.setdefault(code, []).append(entry)

    stats = []
    for code, entries in by_code.items():
        sales = sum(e.simulated_credits for e in entries)
        won = [e for e in entries if e.status == "Won"]
        payout = sum(e.simulated_return for e in won)
        stats.append({"gameType": code, "sales": sales, "winners": len(won), "payout": payout, "profit": sales - payout})
    return stats


def compute_number_frequency(db: Session, market_id: int | None = None, game_type_code: str | None = None, limit: int = 20) -> list[dict]:
    query = db.query(SimulationEntry.selection, func.count(SimulationEntry.id).label("count"))
    if market_id is not None:
        query = query.filter(SimulationEntry.market_id == market_id)
    if game_type_code is not None:
        query = query.join(GameType, GameType.id == SimulationEntry.game_type_id).filter(GameType.code == game_type_code.upper())
    rows = query.group_by(SimulationEntry.selection).order_by(func.count(SimulationEntry.id).desc()).limit(limit).all()
    return [{"selection": selection, "count": count} for selection, count in rows]
