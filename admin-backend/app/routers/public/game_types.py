from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.game_type import GameType
from app.schemas.game_type import GameTypeOut

router = APIRouter(prefix="/game-types", tags=["public-game-types"])


@router.get("", response_model=list[GameTypeOut])
async def list_game_types(db: Session = Depends(get_db)):
    rows = db.query(GameType).filter(GameType.is_active.is_(True)).order_by(GameType.display_order).all()
    return [GameTypeOut.model_validate(r) for r in rows]


@router.get("/{code}/rules", response_model=GameTypeOut)
async def get_game_type_rules(code: str, db: Session = Depends(get_db)):
    game_type = db.query(GameType).filter(GameType.code == code.upper()).first()
    if not game_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game type not found")
    return GameTypeOut.model_validate(game_type)
