from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.market import Market, StarlineSlot
from app.schemas.starline import StarlineSlotCreate, StarlineSlotOut, StarlineSlotUpdate
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/starline/slots", tags=["starline"])


@router.get("", response_model=list[StarlineSlotOut])
async def list_slots(
    market_id: int | None = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(StarlineSlot)
    if market_id is not None:
        query = query.filter(StarlineSlot.market_id == market_id)
    rows = query.order_by(StarlineSlot.display_order).all()
    return [StarlineSlotOut.model_validate(r) for r in rows]


@router.post("", response_model=StarlineSlotOut, status_code=status.HTTP_201_CREATED)
async def create_slot(
    payload: StarlineSlotCreate,
    current_admin: Admin = Depends(require_permission("starline.manage")),
    db: Session = Depends(get_db),
):
    market = db.get(Market, payload.market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    slot = StarlineSlot(
        market_id=payload.market_id, slot_name=payload.slot_name, start_time=payload.start_time,
        cutoff_time=payload.cutoff_time, display_order=payload.display_order,
    )
    db.add(slot)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="starline_slot_created", details=f"Slot created: {payload.slot_name} on market #{payload.market_id}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(slot)
    return StarlineSlotOut.model_validate(slot)


@router.patch("/{slot_id}", response_model=StarlineSlotOut)
async def update_slot(
    slot_id: int,
    payload: StarlineSlotUpdate,
    current_admin: Admin = Depends(require_permission("starline.manage")),
    db: Session = Depends(get_db),
):
    slot = db.get(StarlineSlot, slot_id)
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(slot, field, value)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="starline_slot_updated", details=f"Slot updated: {slot.slot_name}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(slot)
    return StarlineSlotOut.model_validate(slot)
