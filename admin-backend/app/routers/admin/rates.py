from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.game_type import GameType
from app.models.market import Market
from app.models.rate import Rate
from app.schemas.rate import RateCreate, RateOut
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/rates", tags=["rates"])


class RateStatusUpdate(BaseModel):
    status: Literal["Active", "Inactive"]


def _rate_out(rate: Rate, code: str) -> RateOut:
    return RateOut(
        id=rate.id, market_id=rate.market_id, slot_id=rate.slot_id, game_type_id=rate.game_type_id,
        game_type_code=code, rate=rate.rate, effective_from=rate.effective_from, status=rate.status,
    )


@router.get("", response_model=list[RateOut])
async def list_rates(
    market_id: int | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Rate, GameType.code).join(GameType, GameType.id == Rate.game_type_id)
    if market_id is not None:
        query = query.filter(Rate.market_id == market_id)
    rows = query.order_by(Rate.market_id, Rate.effective_from.desc()).all()
    return [_rate_out(r, code) for r, code in rows]


@router.post("", response_model=RateOut, status_code=status.HTTP_201_CREATED)
async def create_rate(
    payload: RateCreate,
    current_admin: Admin = Depends(require_permission("rates.manage")),
    db: Session = Depends(get_db),
):
    market = db.get(Market, payload.market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    game_type = db.get(GameType, payload.game_type_id)
    if not game_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game type not found")

    rate = Rate(
        market_id=payload.market_id, slot_id=payload.slot_id, game_type_id=payload.game_type_id,
        rate=payload.rate, effective_from=payload.effective_from, status="Active",
    )
    db.add(rate)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="rate_created", details=f"Rate set for {game_type.code} on market #{payload.market_id}: {payload.rate}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(rate)
    return _rate_out(rate, game_type.code)


@router.patch("/{rate_id}", response_model=RateOut)
async def update_rate_status(
    rate_id: int,
    payload: RateStatusUpdate,
    current_admin: Admin = Depends(require_permission("rates.manage")),
    db: Session = Depends(get_db),
):
    rate = db.get(Rate, rate_id)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate not found")
    rate.status = payload.status
    db.flush()
    game_type = db.get(GameType, rate.game_type_id)
    db.add(AuditLog(actor=current_admin.name, action="rate_status_updated", details=f"Rate #{rate_id} set to {payload.status}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(rate)
    return _rate_out(rate, game_type.code)
