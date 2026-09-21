"""The generic BulkSelectionEngine: the same code path handles a single selection
and a bulk batch of any enabled game type on any market or Starline slot."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import errors
from app.core.errors import AppError
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, StarlineSlot
from app.models.simulation import SimulationBatch, SimulationEntry
from app.models.user import User
from app.services import credit_service, validation_service
from app.services.market_service import assert_market_open, assert_slot_open


def _get_game_type(db: Session, code: str) -> GameType:
    game_type = db.query(GameType).filter(GameType.code == code.upper(), GameType.is_active.is_(True)).first()
    if not game_type:
        raise AppError(errors.GAME_DISABLED, f"Game type '{code}' not found or inactive", status.HTTP_404_NOT_FOUND)
    return game_type


def _get_config(db: Session, market_id: int, slot_id: int | None, game_type_id: int, stage: str | None) -> GameTypeConfig:
    query = db.query(GameTypeConfig).filter(
        GameTypeConfig.market_id == market_id,
        GameTypeConfig.slot_id == slot_id,
        GameTypeConfig.game_type_id == game_type_id,
        GameTypeConfig.enabled.is_(True),
    )
    configs = query.all()
    # exact stage match first, then a BOTH/no-stage config as fallback
    for config in configs:
        if config.stage == stage:
            return config
    for config in configs:
        if config.stage in (None, "BOTH"):
            return config

    raise AppError(errors.GAME_DISABLED, "This game type is not available for this market/slot/stage")


def _assert_market_or_slot_open(db: Session, market: Market, slot_id: int | None, stage: str | None = None) -> None:
    if slot_id is not None:
        slot = db.get(StarlineSlot, slot_id)
        if not slot or slot.market_id != market.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found on this market")
        assert_slot_open(slot, market)
        return
    assert_market_open(market, stage)


def submit_bulk_simulation(
    db: Session,
    *,
    user: User,
    market_id: int,
    slot_id: int | None,
    game_type_code: str,
    stage: str | None,
    selections: list,
    admin_id: int | None,
    created_via: str,
) -> tuple[SimulationBatch, list[SimulationEntry], int]:
    if not selections:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one selection is required")

    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    game_type = _get_game_type(db, game_type_code)
    # Only single-session games can run into the close window; jodi/sangam need the open result, so
    # they always stop at the cutoff whatever `stage` the client sent.
    session_stage = stage.upper() if stage and game_type.code not in ("JODI", "HALF_SANGAM", "FULL_SANGAM") else None
    if game_type.code == "CLOSE":
        session_stage = "CLOSE"
    _assert_market_or_slot_open(db, market, slot_id, session_stage)

    config = _get_config(db, market_id, slot_id, game_type.id, stage)

    if len(selections) > 1 and not config.bulk_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bulk selection is not enabled for this game type here")
    if len(selections) > config.max_bulk_selections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At most {config.max_bulk_selections} selections are allowed in one batch",
        )
    if not config.duplicate_selection_allowed:
        values = [(s.value.strip(), getattr(s, "game_variant", None)) for s in selections]
        if len(values) != len(set(values)):
            raise AppError(errors.DUPLICATE_SELECTION, "Duplicate selections are not allowed in this batch")
    if not config.individual_amount_allowed:
        credits_set = {s.credits for s in selections}
        if len(credits_set) > 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All selections in this batch must use the same credits amount")

    for entry in selections:
        try:
            validation_service.validate_selection(
                game_type.code, game_type.classification_rule, entry.value, getattr(entry, "game_variant", None)
            )
        except validation_service.SelectionValidationError as exc:
            raise AppError(exc.code, str(exc))
        if not (config.min_credits <= entry.credits <= config.max_credits):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Credits for '{entry.value}' must be between {config.min_credits} and {config.max_credits}",
            )

    from datetime import date
    from app.models.rate import Rate
    rate_obj = (
        db.query(Rate)
        .filter(
            Rate.market_id == market_id,
            Rate.slot_id == slot_id,
            Rate.game_type_id == game_type.id,
            Rate.status == "Active",
            Rate.effective_from <= date.today(),
        )
        .order_by(Rate.effective_from.desc(), Rate.id.desc())
        .first()
    )
    rate = rate_obj.rate if rate_obj else 95
    total_credits = sum(e.credits for e in selections)

    batch = SimulationBatch(
        user_id=user.id, market_id=market_id, slot_id=slot_id, game_type_id=game_type.id,
        stage=stage, created_via=created_via,
    )
    db.add(batch)
    db.flush()

    entries = [
        SimulationEntry(
            batch_id=batch.id, user_id=user.id, market_id=market_id, slot_id=slot_id,
            game_type_id=game_type.id, stage=stage, selection=entry.value.strip(),
            game_variant=getattr(entry, "game_variant", None),
            simulated_credits=entry.credits, simulated_rate=rate,
            simulated_return=validation_service.compute_simulated_return(entry.credits, rate),
            status="Pending",
        )
        for entry in selections
    ]
    db.add_all(entries)
    db.flush()

    # Check the whole batch up front so it is all-or-nothing, then write one ledger row per number
    # so each bid has its own line (amount, running balance) in the user's wallet history.
    if user.balance < total_credits:
        raise AppError(errors.INSUFFICIENT_LEARNING_CREDITS, "Insufficient Learning Credits for this batch")
    for entry in entries:
        credit_service.apply_ledger_entry(
            db, user=user, type="stake", amount=-entry.simulated_credits,
            reference_type="simulation_entry", reference_id=str(entry.id),
            created_by_admin_id=admin_id, note=f"{game_type.code} {entry.selection} on {market.name}",
        )

    return batch, entries, total_credits


def override_outcome(
    db: Session, *, entry_id: int, new_status: str, reason: str, admin_id: int
) -> SimulationEntry:
    entry = db.get(SimulationEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found")
    if entry.status not in ("Won", "Lost"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a resolved (Won/Lost) simulation can be overridden")
    if new_status not in ("Won", "Lost"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Override outcome must be 'Won' or 'Lost'")
    if new_status == entry.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New outcome matches the current outcome")

    user = db.get(User, entry.user_id)
    ledger_amount = entry.simulated_return if new_status == "Won" else -entry.simulated_return
    credit_service.apply_ledger_entry(
        db, user=user, type="adjustment", amount=ledger_amount,
        reference_type="simulation_override", reference_id=str(entry.id),
        created_by_admin_id=admin_id, note=f"Outcome override: {reason}",
    )

    if entry.original_status is None:
        entry.original_status = entry.status
    entry.status = new_status
    entry.override_status = "OVERRIDDEN"
    entry.override_reason = reason
    entry.overridden_by_admin_id = admin_id
    entry.overridden_at = datetime.now(timezone.utc)
    db.flush()
    return entry
