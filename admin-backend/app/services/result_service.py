"""Result draft/publish/correction workflow and server-side evaluation of
pending SimulationEntry rows. Matka markets declare open_panna/close_panna and
get open_ank/close_ank/jodi derived server-side; Starline slots and
Gali-Disawar markets can declare open_ank/close_ank directly (no panna) or a
panna (for Starline SP/DP/TP). Jodi only resolves once both stages are set.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import INVALID_RESULT, AppError
from app.models.credit import CreditLedger
from app.models.game_type import GameType
from app.models.market import Market
from app.models.market_result import MarketResult
from app.models.simulation import SimulationEntry
from app.models.user import User
from app.services import credit_service, validation_service


def upsert_result(
    db: Session,
    *,
    market_id: int,
    slot_id: int | None,
    result_date: str,
    open_panna: str | None,
    open_ank: str | None,
    close_panna: str | None,
    close_ank: str | None,
    single_result: str | None,
    publish: bool,
    admin_id: int,
) -> MarketResult:
    existing = (
        db.query(MarketResult)
        .filter(
            MarketResult.market_id == market_id,
            MarketResult.slot_id == slot_id,
            MarketResult.result_date == result_date,
            MarketResult.status != "Corrected",
        )
        .order_by(MarketResult.id.desc())
        .first()
    )
    result = existing or MarketResult(market_id=market_id, slot_id=slot_id, result_date=result_date, status="Draft")

    if open_panna is not None:
        try:
            validation_service.validate_panna_shape(open_panna)
        except validation_service.SelectionValidationError as exc:
            raise AppError(INVALID_RESULT, str(exc))
        result.open_panna = open_panna
        result.open_ank = validation_service.derive_ank_from_panna(open_panna)
    elif open_ank is not None:
        try:
            validation_service.validate_single(open_ank)
        except validation_service.SelectionValidationError as exc:
            raise AppError(INVALID_RESULT, str(exc))
        result.open_ank = open_ank

    if close_panna is not None:
        try:
            validation_service.validate_panna_shape(close_panna)
        except validation_service.SelectionValidationError as exc:
            raise AppError(INVALID_RESULT, str(exc))
        result.close_panna = close_panna
        result.close_ank = validation_service.derive_ank_from_panna(close_panna)
    elif close_ank is not None:
        try:
            validation_service.validate_single(close_ank)
        except validation_service.SelectionValidationError as exc:
            raise AppError(INVALID_RESULT, str(exc))
        result.close_ank = close_ank

    if single_result is not None:
        result.single_result = single_result

    if result.open_ank and result.close_ank:
        result.jodi = validation_service.derive_jodi(result.open_ank, result.close_ank)

    if publish:
        result.status = "Published"
        result.published_by_admin_id = admin_id
        result.published_at = datetime.now(timezone.utc)
    else:
        result.status = "Draft"

    db.add(result)
    db.flush()

    if publish:
        evaluate_pending_entries(db, result)

    return result


def _resolve_winning_value(
    game_type: GameType,
    entry: SimulationEntry,
    *,
    open_panna: str | None,
    open_ank: str | None,
    close_panna: str | None,
    close_ank: str | None,
    jodi: str | None,
) -> str | None:
    """The single source of truth for 'what value beats this entry', shared by
    the real publish/correct settlement path and the draft-safe preview."""
    if game_type.code == validation_service.HALF_SANGAM:
        if not (open_panna and open_ank and close_panna and close_ank):
            return None
        if entry.game_variant == "OPEN_PANNA_CLOSE_ANK":
            return f"{open_panna}-{close_ank}"
        if entry.game_variant == "OPEN_ANK_CLOSE_PANNA":
            # Canonical Half Sangam input remains PANNA-ANK for both
            # directions; this variant means close panna + open ank.
            return f"{close_panna}-{open_ank}"
        return None
    if game_type.code == validation_service.FULL_SANGAM:
        if not (open_panna and close_panna):
            return None
        return f"{open_panna}-{close_panna}"
    if game_type.code == "JODI":
        return jodi
    if game_type.classification_rule in ("PANNA_SINGLE", "PANNA_DOUBLE", "PANNA_TRIPLE"):
        return close_panna if entry.stage == "CLOSE" else open_panna
    return close_ank if (entry.stage == "CLOSE" or game_type.code == "CLOSE") else open_ank


def evaluate_pending_entries(db: Session, result: MarketResult) -> list[SimulationEntry]:
    entries = (
        db.query(SimulationEntry)
        .filter(
            SimulationEntry.market_id == result.market_id,
            SimulationEntry.slot_id == result.slot_id,
            SimulationEntry.status == "Pending",
        )
        .all()
    )

    resolved: list[SimulationEntry] = []
    for entry in entries:
        game_type = db.get(GameType, entry.game_type_id)
        winning_value = _resolve_winning_value(
            game_type, entry,
            open_panna=result.open_panna, open_ank=result.open_ank,
            close_panna=result.close_panna, close_ank=result.close_ank, jodi=result.jodi,
        )
        if winning_value is None:
            continue  # not resolvable yet (e.g. jodi awaiting the other stage)

        won = entry.selection == winning_value
        entry.status = "Won" if won else "Lost"
        entry.resolved_at = datetime.now(timezone.utc)
        entry.result_id = result.id

        if won:
            user = db.get(User, entry.user_id)
            credit_service.apply_ledger_entry(
                db, user=user, type="payout", amount=entry.simulated_return,
                reference_type="simulation_entry", reference_id=str(entry.id),
                created_by_admin_id=result.published_by_admin_id,
                note=f"Payout: {game_type.code} {entry.selection}",
            )
        resolved.append(entry)

    db.flush()
    return resolved


def preview_result(
    db: Session,
    *,
    market_id: int,
    slot_id: int | None,
    open_panna: str | None,
    open_ank: str | None,
    close_panna: str | None,
    close_ank: str | None,
) -> dict:
    """Read-only dry run: shows who would win/lose with this draft result,
    without touching SimulationEntry rows, the credit ledger, or the DB at
    all. Lets an admin check winners before committing to a publish."""
    if open_panna:
        try:
            validation_service.validate_panna_shape(open_panna)
        except validation_service.SelectionValidationError as exc:
            raise AppError(INVALID_RESULT, str(exc))
        open_ank = validation_service.derive_ank_from_panna(open_panna)
    if close_panna:
        try:
            validation_service.validate_panna_shape(close_panna)
        except validation_service.SelectionValidationError as exc:
            raise AppError(INVALID_RESULT, str(exc))
        close_ank = validation_service.derive_ank_from_panna(close_panna)
    jodi = validation_service.derive_jodi(open_ank, close_ank) if (open_ank and close_ank) else None

    entries = (
        db.query(SimulationEntry)
        .filter(
            SimulationEntry.market_id == market_id,
            SimulationEntry.slot_id == slot_id,
            SimulationEntry.status == "Pending",
        )
        .all()
    )

    winners: list[dict] = []
    losers_count = 0
    unresolved_count = 0
    total_stake_at_risk = 0
    total_potential_payout = 0

    for entry in entries:
        game_type = db.get(GameType, entry.game_type_id)
        winning_value = _resolve_winning_value(
            game_type, entry,
            open_panna=open_panna, open_ank=open_ank,
            close_panna=close_panna, close_ank=close_ank, jodi=jodi,
        )
        if winning_value is None:
            unresolved_count += 1
            continue

        total_stake_at_risk += entry.simulated_credits
        if entry.selection == winning_value:
            user = db.get(User, entry.user_id)
            total_potential_payout += entry.simulated_return
            winners.append(
                {
                    "entryId": entry.id,
                    "userId": entry.user_id,
                    "userName": user.name if user else "",
                    "userPhone": user.phone if user else "",
                    "gameType": game_type.code,
                    "stage": entry.stage,
                    "selection": entry.selection,
                    "gameVariant": entry.game_variant,
                    "credits": entry.simulated_credits,
                    "simulatedRate": entry.simulated_rate,
                    "potentialPayout": entry.simulated_return,
                }
            )
        else:
            losers_count += 1

    return {
        "openPanna": open_panna,
        "openAnk": open_ank,
        "closePanna": close_panna,
        "closeAnk": close_ank,
        "jodi": jodi,
        "totalPendingEntries": len(entries),
        "resolvableEntries": len(entries) - unresolved_count,
        "unresolvedEntries": unresolved_count,
        "winnersCount": len(winners),
        "losersCount": losers_count,
        "totalStakeAtRisk": total_stake_at_risk,
        "totalPotentialPayout": total_potential_payout,
        "winners": winners,
    }


def correct_result(
    db: Session,
    *,
    result_id: int,
    admin_id: int,
    reason: str,
    open_panna: str | None,
    open_ank: str | None,
    close_panna: str | None,
    close_ank: str | None,
    single_result: str | None,
) -> MarketResult:
    old = db.get(MarketResult, result_id)
    if not old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    if old.status != "Published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a published result can be corrected")

    affected = db.query(SimulationEntry).filter(SimulationEntry.result_id == old.id).all()
    for entry in affected:
        # A manual override is intentionally independent from result correction.
        if entry.override_status == "OVERRIDDEN":
            continue
        if entry.status == "Won":
            user = db.get(User, entry.user_id)
            game_type = db.get(GameType, entry.game_type_id)
            market = db.get(Market, entry.market_id)
            credit_service.apply_ledger_entry(
                db, user=user, type="adjustment", amount=-entry.simulated_return,
                reference_type="result_correction", reference_id=str(old.id),
                created_by_admin_id=admin_id,
                note=f"Payout reversed: {game_type.code} {entry.selection} on {market.name} (result corrected: {reason})",
            )
        entry.status = "Pending"
        entry.result_id = None
        entry.resolved_at = None
    db.flush()

    old.status = "Corrected"
    db.flush()

    new_result = MarketResult(
        market_id=old.market_id, slot_id=old.slot_id, result_date=old.result_date,
        open_panna=old.open_panna, open_ank=old.open_ank, close_panna=old.close_panna,
        close_ank=old.close_ank, jodi=old.jodi, single_result=old.single_result,
        corrected_from_id=old.id, correction_reason=reason, status="Published",
        published_by_admin_id=admin_id, published_at=datetime.now(timezone.utc),
    )

    try:
        if open_panna is not None:
            validation_service.validate_panna_shape(open_panna)
            new_result.open_panna = open_panna
            new_result.open_ank = validation_service.derive_ank_from_panna(open_panna)
        elif open_ank is not None:
            new_result.open_ank = open_ank
        if close_panna is not None:
            validation_service.validate_panna_shape(close_panna)
            new_result.close_panna = close_panna
            new_result.close_ank = validation_service.derive_ank_from_panna(close_panna)
        elif close_ank is not None:
            new_result.close_ank = close_ank
    except validation_service.SelectionValidationError as exc:
        raise AppError(INVALID_RESULT, str(exc))
    if single_result is not None:
        new_result.single_result = single_result
    if new_result.open_ank and new_result.close_ank:
        new_result.jodi = validation_service.derive_jodi(new_result.open_ank, new_result.close_ank)

    db.add(new_result)
    db.flush()

    evaluate_pending_entries(db, new_result)
    return new_result
