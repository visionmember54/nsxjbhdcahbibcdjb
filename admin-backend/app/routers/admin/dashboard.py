from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_permission
from app.models.admin import Admin
from app.models.audit import AuditLog
from app.models.game_type import GameType
from app.models.market import Market, StarlineSlot
from app.models.market_result import MarketResult
from app.models.simulation import SimulationEntry
from app.models.user import User
from app.services.report_service import compute_market_statistics

router = APIRouter(prefix="/admin/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(current_admin: Admin = Depends(require_permission("dashboard.view")), db: Session = Depends(get_db)):
    today = date.today().isoformat()
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == "active").count()
    open_markets = db.query(Market).filter(Market.status == "OPEN").count()
    pending_results = db.query(MarketResult).filter(MarketResult.status == "Draft").count()
    total_simulations = db.query(SimulationEntry).count()
    total_credits_staked = sum(a[0] for a in db.query(SimulationEntry.simulated_credits).all())
    total_credits_paid_out = sum(
        a[0] for a in db.query(SimulationEntry.simulated_return).filter(SimulationEntry.status == "Won").all()
    )
    total_won = db.query(SimulationEntry).filter(SimulationEntry.status == "Won").count()
    total_lost = db.query(SimulationEntry).filter(SimulationEntry.status == "Lost").count()
    total_pending = db.query(SimulationEntry).filter(SimulationEntry.status == "Pending").count()
    active_starline_slots = db.query(StarlineSlot).filter(StarlineSlot.enabled.is_(True)).count()

    popular_market = (
        db.query(Market.name, func.count(SimulationEntry.id).label("count"))
        .join(SimulationEntry, SimulationEntry.market_id == Market.id)
        .group_by(Market.id, Market.name)
        .order_by(func.count(SimulationEntry.id).desc())
        .first()
    )
    popular_game = (
        db.query(GameType.code, func.count(SimulationEntry.id).label("count"))
        .join(SimulationEntry, SimulationEntry.game_type_id == GameType.id)
        .group_by(GameType.id, GameType.code)
        .order_by(func.count(SimulationEntry.id).desc())
        .first()
    )
    upcoming_markets = [
        {"id": market.id, "name": market.name, "openingTime": market.opening_time.isoformat() if market.opening_time else None,
         "cutoffTime": market.cutoff_time.isoformat() if market.cutoff_time else None}
        for market in db.query(Market).filter(Market.status == "UPCOMING").order_by(Market.display_order, Market.id).limit(5).all()
    ]
    recent_admin_actions = [
        {"id": row.id, "actor": row.actor, "action": row.action, "details": row.details,
         "subjectUserId": row.subject_user_id, "createdAt": row.created_at}
        for row in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(8).all()
    ]

    today_entries = db.query(SimulationEntry).filter(func.date(SimulationEntry.created_at) == today).all()
    today_staked = sum(entry.simulated_credits for entry in today_entries)
    today_payout = sum(entry.simulated_return for entry in today_entries if entry.status == "Won")
    today_won = sum(1 for entry in today_entries if entry.status == "Won")
    today_pending = sum(1 for entry in today_entries if entry.status == "Pending")
    today_new_users = db.query(User).filter(func.date(User.created_at) == today).count()
    today_results = db.query(MarketResult).filter(
        MarketResult.result_date == today,
        MarketResult.status.in_(["Published", "Corrected"]),
    ).count()

    market_by_id = {market.id: market.name for market in db.query(Market).all()}
    performance_by_market: dict[int, dict] = {}
    for entry in today_entries:
        performance = performance_by_market.setdefault(entry.market_id, {
            "marketId": entry.market_id,
            "market": market_by_id.get(entry.market_id, "Unknown market"),
            "simulations": 0,
            "staked": 0,
            "payout": 0,
        })
        performance["simulations"] += 1
        performance["staked"] += entry.simulated_credits
        if entry.status == "Won":
            performance["payout"] += entry.simulated_return

    today_market_performance = sorted(
        [{**performance, "net": performance["staked"] - performance["payout"]} for performance in performance_by_market.values()],
        key=lambda performance: performance["staked"],
        reverse=True,
    )

    return {
        "stats": {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "openMarkets": open_markets,
            "pendingResults": pending_results,
            "totalSimulations": total_simulations,
            "totalCreditsStaked": total_credits_staked,
            "totalCreditsPaidOut": total_credits_paid_out,
            "totalNetCredits": total_credits_staked - total_credits_paid_out,
            "totalWon": total_won,
            "totalLost": total_lost,
            "totalPending": total_pending,
            "activeStarlineSlots": active_starline_slots,
        },
        "today": {
            "date": today,
            "simulations": len(today_entries),
            "staked": today_staked,
            "payout": today_payout,
            "net": today_staked - today_payout,
            "won": today_won,
            "pending": today_pending,
            "newUsers": today_new_users,
            "publishedResults": today_results,
        },
        "todayMarketPerformance": today_market_performance,
        "marketStatistics": compute_market_statistics(db),
        "popularMarket": {"name": popular_market[0], "count": popular_market[1]} if popular_market else None,
        "popularGame": {"code": popular_game[0], "count": popular_game[1]} if popular_game else None,
        "upcomingMarkets": upcoming_markets,
        "recentAdminActions": recent_admin_actions,
    }
