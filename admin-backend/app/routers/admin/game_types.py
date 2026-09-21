from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.game_type import GameType
from app.schemas.game_type import GameTypeCreate, GameTypeOut, GameTypeUpdate
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/game-types", tags=["game-types"])


@router.get("", response_model=list[GameTypeOut])
async def list_game_types(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(GameType).order_by(GameType.display_order).all()
    return [GameTypeOut.model_validate(r) for r in rows]


@router.post("", response_model=GameTypeOut, status_code=status.HTTP_201_CREATED)
async def create_game_type(
    payload: GameTypeCreate,
    current_admin: Admin = Depends(require_permission("game_types.manage")),
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()
    if db.query(GameType).filter(GameType.code == code).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A game type with this code already exists")

    game_type = GameType(
        code=code, name=payload.name, description=payload.description, digit_length=payload.digit_length,
        classification_rule=payload.classification_rule, display_order=payload.display_order,
    )
    db.add(game_type)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="game_type_created", details=f"Game type created: {code}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(game_type)
    return GameTypeOut.model_validate(game_type)


@router.patch("/{game_type_id}", response_model=GameTypeOut)
async def update_game_type(
    game_type_id: int,
    payload: GameTypeUpdate,
    current_admin: Admin = Depends(require_permission("game_types.manage")),
    db: Session = Depends(get_db),
):
    game_type = db.get(GameType, game_type_id)
    if not game_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game type not found")
    if payload.is_active is not None:
        game_type.is_active = payload.is_active
    if payload.display_order is not None:
        game_type.display_order = payload.display_order
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="game_type_updated", details=f"Game type updated: {game_type.code}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(game_type)
    return GameTypeOut.model_validate(game_type)
