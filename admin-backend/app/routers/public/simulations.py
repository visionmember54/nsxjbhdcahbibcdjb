from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.game_type import GameType
from app.models.simulation import SimulationEntry
from app.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.simulation import BulkSimulationCreate, SelectionEntry, SimulationBatchOut, SimulationCreate, SimulationEntryOut
from app.services import simulation_service

router = APIRouter(prefix="/simulations", tags=["public-simulations"])


def _entry_out(entry: SimulationEntry, code: str) -> SimulationEntryOut:
    return SimulationEntryOut(
        id=entry.id, batchId=entry.batch_id, userId=entry.user_id, marketId=entry.market_id,
        slotId=entry.slot_id, gameType=code, stage=entry.stage, selection=entry.selection, gameVariant=entry.game_variant,
        simulatedCredits=entry.simulated_credits, simulatedRate=entry.simulated_rate,
        simulatedReturn=entry.simulated_return, status=entry.status, createdAt=entry.created_at,
        resolvedAt=entry.resolved_at, originalStatus=entry.original_status,
        overrideStatus=entry.override_status, overrideReason=entry.override_reason,
        overriddenByAdminId=entry.overridden_by_admin_id, overriddenAt=entry.overridden_at,
    )


@router.post("", response_model=SimulationBatchOut, status_code=status.HTTP_201_CREATED)
async def submit_simulation(
    payload: SimulationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    batch, entries, total = simulation_service.submit_bulk_simulation(
        db, user=current_user, market_id=payload.market_id, slot_id=payload.slot_id,
        game_type_code=payload.game_type, stage=payload.stage,
        selections=[SelectionEntry(value=payload.value, credits=payload.credits, game_variant=payload.game_variant)],
        admin_id=None, created_via="api_bulk",
    )
    db.commit()
    db.refresh(current_user)
    game_type = db.get(GameType, entries[0].game_type_id)
    return SimulationBatchOut(
        batchId=batch.id, entries=[_entry_out(e, game_type.code) for e in entries],
        totalCredits=total, remainingBalance=current_user.balance,
    )


@router.post("/bulk", response_model=SimulationBatchOut, status_code=status.HTTP_201_CREATED)
async def submit_bulk_simulation(
    payload: BulkSimulationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    batch, entries, total = simulation_service.submit_bulk_simulation(
        db, user=current_user, market_id=payload.market_id, slot_id=payload.slot_id,
        game_type_code=payload.game_type, stage=payload.stage, selections=payload.selections,
        admin_id=None, created_via="api_bulk",
    )
    db.commit()
    db.refresh(current_user)
    game_type = db.get(GameType, entries[0].game_type_id)
    return SimulationBatchOut(
        batchId=batch.id, entries=[_entry_out(e, game_type.code) for e in entries],
        totalCredits=total, remainingBalance=current_user.balance,
    )


@router.get("/my", response_model=Page[SimulationEntryOut])
async def my_simulations(
    pagination: PageParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.query(SimulationEntry).filter(SimulationEntry.user_id == current_user.id).count()
    rows = (
        db.query(SimulationEntry, GameType.code)
        .join(GameType, GameType.id == SimulationEntry.game_type_id)
        .filter(SimulationEntry.user_id == current_user.id)
        .order_by(SimulationEntry.id.desc())
        .limit(pagination.limit).offset(pagination.offset).all()
    )
    items = [_entry_out(e, code) for e, code in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.get("/{entry_id}", response_model=SimulationEntryOut)
async def get_simulation(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.get(SimulationEntry, entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found")
    game_type = db.get(GameType, entry.game_type_id)
    return _entry_out(entry, game_type.code)
