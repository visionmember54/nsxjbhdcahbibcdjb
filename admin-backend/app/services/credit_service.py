"""The atomic single-writer for every Learning Credits balance mutation.

Ported from the prior session's wallet_service.apply_ledger_entry, same
overdraw-safe guarantee -- but there is no deposit/withdrawal/payment-method
concept anywhere in this module. Balance only ever moves via grant, admin
adjustment, admin reset, or the simulation engine's stake/payout.
"""
from __future__ import annotations

from app.models.credit import CreditLedger
from app.models.user import User
from sqlalchemy.orm import Session


class InsufficientCreditsError(Exception):
    pass


def apply_ledger_entry(
    db: Session,
    *,
    user: User,
    type: str,
    amount: int,
    reference_type: str | None = None,
    reference_id: str | None = None,
    created_by_admin_id: int | None = None,
    note: str | None = None,
    visible_to_user: bool = True,
) -> CreditLedger:
    new_balance = user.balance + amount
    if new_balance < 0:
        raise InsufficientCreditsError(f"balance {user.balance} + amount {amount} would go negative")

    user.balance = new_balance
    entry = CreditLedger(
        user_id=user.id,
        type=type,
        amount=amount,
        balance_after=new_balance,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by_admin_id=created_by_admin_id,
        note=note,
        visible_to_user=visible_to_user,
    )
    db.add(entry)
    db.flush()
    return entry


def grant_credits(db: Session, user: User, amount: int, admin_id: int, note: str | None = None, visible_to_user: bool = True) -> CreditLedger:
    return apply_ledger_entry(
        db, user=user, type="grant", amount=amount,
        reference_type="admin_grant", created_by_admin_id=admin_id, note=note,
        visible_to_user=visible_to_user,
    )


def adjust_credits(db: Session, user: User, amount: int, admin_id: int, note: str | None = None, visible_to_user: bool = True) -> CreditLedger:
    """`amount` is signed -- positive credits, negative debits an admin correction."""
    return apply_ledger_entry(
        db, user=user, type="adjustment", amount=amount,
        reference_type="admin_adjustment", created_by_admin_id=admin_id, note=note,
        visible_to_user=visible_to_user,
    )


def reset_credits(db: Session, user: User, new_balance: int, admin_id: int, note: str | None = None, visible_to_user: bool = True) -> CreditLedger:
    delta = new_balance - user.balance
    return apply_ledger_entry(
        db, user=user, type="reset", amount=delta,
        reference_type="admin_reset", created_by_admin_id=admin_id, note=note,
        visible_to_user=visible_to_user,
    )
