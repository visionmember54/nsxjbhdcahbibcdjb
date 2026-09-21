from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.core.errors import UNAUTHORIZED_OVERRIDE
from app.models.admin import Admin
from app.models.game_type import GameType
from app.models.simulation import SimulationEntry
from app.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.simulation import (
    AdminBulkSimulationCreate,
    AdminSimulationCreate,
    SelectionEntry,
    SimulationBatchOut,
    SimulationEntryOut,
    SimulationOverride,
)
from app.services import simulation_service
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/simulations", tags=["simulations"])


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


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=Page[SimulationEntryOut])
async def list_simulations(
    pagination: PageParams = Depends(),
    user_id: int | None = None,
    market_id: int | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(SimulationEntry, GameType.code).join(GameType, GameType.id == SimulationEntry.game_type_id)
    if user_id is not None:
        query = query.filter(SimulationEntry.user_id == user_id)
    if market_id is not None:
        query = query.filter(SimulationEntry.market_id == market_id)
    total = query.count()
    rows = query.order_by(SimulationEntry.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    items = [_entry_out(e, code) for e, code in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.post("", response_model=SimulationBatchOut, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    payload: AdminSimulationCreate,
    current_admin: Admin = Depends(require_permission("simulations.create")),
    db: Session = Depends(get_db),
):
    user = _get_user(db, payload.user_id)
    batch, entries, total = simulation_service.submit_bulk_simulation(
        db, user=user, market_id=payload.market_id, slot_id=payload.slot_id,
        game_type_code=payload.game_type, stage=payload.stage,
        selections=[SelectionEntry(value=payload.value, credits=payload.credits, game_variant=payload.game_variant)],
        admin_id=current_admin.id, created_via="admin_manual",
    )
    game_type = db.get(GameType, entries[0].game_type_id)
    db.add(AuditLog(actor=current_admin.name, action="simulation_created", details=f"{game_type.code} selection recorded for {user.name}", subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(user)
    return SimulationBatchOut(
        batchId=batch.id, entries=[_entry_out(e, game_type.code) for e in entries],
        totalCredits=total, remainingBalance=user.balance,
    )


@router.post("/bulk", response_model=SimulationBatchOut, status_code=status.HTTP_201_CREATED)
async def create_bulk_simulation(
    payload: AdminBulkSimulationCreate,
    current_admin: Admin = Depends(require_permission("simulations.create")),
    db: Session = Depends(get_db),
):
    user = _get_user(db, payload.user_id)
    batch, entries, total = simulation_service.submit_bulk_simulation(
        db, user=user, market_id=payload.market_id, slot_id=payload.slot_id,
        game_type_code=payload.game_type, stage=payload.stage, selections=payload.selections,
        admin_id=current_admin.id, created_via="admin_manual",
    )
    game_type = db.get(GameType, entries[0].game_type_id)
    db.add(AuditLog(actor=current_admin.name, action="bulk_simulation_created", details=f"{len(entries)} {game_type.code} selections recorded for {user.name} (batch {batch.id})", subject_user_id=user.id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(user)
    return SimulationBatchOut(
        batchId=batch.id, entries=[_entry_out(e, game_type.code) for e in entries],
        totalCredits=total, remainingBalance=user.balance,
    )


@router.post("/{entry_id}/override", response_model=SimulationEntryOut)
async def override_simulation(
    entry_id: int,
    payload: SimulationOverride,
    current_admin: Admin = Depends(require_permission("simulations.override", error_code=UNAUTHORIZED_OVERRIDE)),
    db: Session = Depends(get_db),
):
    """Overrides one simulation's outcome for an educational demonstration -- distinct
    from a market result correction, which corrects the underlying published result."""
    entry = simulation_service.override_outcome(
        db, entry_id=entry_id, new_status=payload.outcome, reason=payload.reason, admin_id=current_admin.id,
    )
    game_type = db.get(GameType, entry.game_type_id)
    db.add(AuditLog(actor=current_admin.name, action="simulation_overridden", details=f"Simulation #{entry_id} outcome overridden to {payload.outcome}: {payload.reason}", subject_user_id=entry.user_id, created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(entry)
    return _entry_out(entry, game_type.code)
