from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, StarlineSlot
from app.schemas.game_type_config import GameTypeConfigCreate, GameTypeConfigOut, GameTypeConfigUpdate
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/markets/{market_id}/game-type-configs", tags=["game-type-configs"])


def _config_out(config: GameTypeConfig, code: str) -> GameTypeConfigOut:
    return GameTypeConfigOut(
        id=config.id, market_id=config.market_id, slot_id=config.slot_id, game_type_id=config.game_type_id,
        game_type_code=code, stage=config.stage, enabled=config.enabled, min_credits=config.min_credits,
        max_credits=config.max_credits, bulk_enabled=config.bulk_enabled, max_bulk_selections=config.max_bulk_selections,
        same_amount_allowed=config.same_amount_allowed, individual_amount_allowed=config.individual_amount_allowed,
        duplicate_selection_allowed=config.duplicate_selection_allowed,
    )


@router.get("", response_model=list[GameTypeConfigOut])
async def list_configs(
    market_id: int,
    slot_id: int | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(GameTypeConfig, GameType.code).join(GameType, GameType.id == GameTypeConfig.game_type_id).filter(
        GameTypeConfig.market_id == market_id
    )
    if slot_id is not None:
        query = query.filter(GameTypeConfig.slot_id == slot_id)
    rows = query.all()
    return [_config_out(c, code) for c, code in rows]


@router.post("", response_model=GameTypeConfigOut, status_code=status.HTTP_201_CREATED)
async def create_config(
    market_id: int,
    payload: GameTypeConfigCreate,
    current_admin: Admin = Depends(require_permission("game_type_configs.manage")),
    db: Session = Depends(get_db),
):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    game_type = db.get(GameType, payload.game_type_id)
    if not game_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game type not found")
    if payload.slot_id is not None:
        slot = db.get(StarlineSlot, payload.slot_id)
        if not slot or slot.market_id != market_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found on this market")

    config = GameTypeConfig(
        market_id=market_id, slot_id=payload.slot_id, game_type_id=payload.game_type_id, stage=payload.stage,
        enabled=payload.enabled, min_credits=payload.min_credits, max_credits=payload.max_credits,
        bulk_enabled=payload.bulk_enabled, max_bulk_selections=payload.max_bulk_selections,
        same_amount_allowed=payload.same_amount_allowed, individual_amount_allowed=payload.individual_amount_allowed,
        duplicate_selection_allowed=payload.duplicate_selection_allowed,
    )
    db.add(config)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="game_type_config_created", details=f"{game_type.code} enabled on market #{market_id}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(config)
    return _config_out(config, game_type.code)


@router.patch("/{config_id}", response_model=GameTypeConfigOut)
async def update_config(
    market_id: int,
    config_id: int,
    payload: GameTypeConfigUpdate,
    current_admin: Admin = Depends(require_permission("game_type_configs.manage")),
    db: Session = Depends(get_db),
):
    config = db.get(GameTypeConfig, config_id)
    if not config or config.market_id != market_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.flush()
    game_type = db.get(GameType, config.game_type_id)
    db.add(AuditLog(actor=current_admin.name, action="game_type_config_updated", details=f"{game_type.code} config updated on market #{market_id}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(config)
    return _config_out(config, game_type.code)
