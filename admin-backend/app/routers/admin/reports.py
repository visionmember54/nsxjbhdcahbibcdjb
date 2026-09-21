from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_permission
from app.models.admin import Admin
from app.services.report_service import compute_game_statistics, compute_market_statistics, compute_number_frequency

router = APIRouter(prefix="/admin/reports", tags=["reports"])


@router.get("/simulation-statistics")
async def simulation_statistics(current_admin: Admin = Depends(require_permission("reports.view")), db: Session = Depends(get_db)):
    return compute_market_statistics(db)


@router.get("/game-statistics")
async def game_statistics(current_admin: Admin = Depends(require_permission("reports.view")), db: Session = Depends(get_db)):
    return compute_game_statistics(db)


@router.get("/number-frequency")
async def number_frequency(
    market_id: int | None = None,
    game_type: str | None = None,
    limit: int = 20,
    current_admin: Admin = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
):
    return compute_number_frequency(db, market_id=market_id, game_type_code=game_type, limit=limit)
