"""Builds the /api/v1/wallet/statement feed.

Ledger rows are written in the same transaction as the action that caused them (bet, payout,
refund, ...), so they appear the instant that action succeeds. Pending/rejected deposit requests
have no ledger row yet, so they are merged in from CreditRequest to show up immediately too.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import String, and_, cast, func, or_
from sqlalchemy.orm import Session

from app.models.credit import CreditLedger
from app.models.credit_request import CreditRequest
from app.models.game_type import GameType
from app.models.market import Market, MarketCategory
from app.models.market_result import MarketResult
from app.models.simulation import SimulationBatch, SimulationEntry
from app.services import app_api_service as shape

_BET_STATUS = {"Pending": "PENDING", "Won": "WON", "Lost": "LOST", "Cancelled": "CANCELLED"}
_MAX_LISTED = 5  # numbers spelled out in a description before "+N more"

# ledger type -> (title, kind)
_TITLES = {
    "stake": ("Bet Placed", "BET_PLACED"),
    "payout": ("Bet Won", "BET_WON"),
    "withdraw_hold": ("Withdrawal Requested", "WITHDRAWAL_HOLD"),
    "refund": ("Withdrawal Refunded", "WITHDRAWAL_REFUND"),
}


def _ids(rows, ref_types: tuple[str, ...]) -> list[int]:
    out = []
    for r in rows:
        if r.reference_type in ref_types and r.reference_id and r.reference_id.isdigit():
            out.append(int(r.reference_id))
    return out


def _label(game_code: str | None) -> str:
    return shape.game_mode_slug_label(game_code)[1].title() if game_code else ""


def _in_market_type(db: Session, model, id_col, type_clause):
    return (
        db.query(cast(id_col, String))
        .select_from(model)
        .join(Market, Market.id == model.market_id)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(type_clause)
    )


def _ledger_query(db: Session, user_id: int, transaction_type, from_date, to_date, type_clause):
    q = db.query(CreditLedger).filter(
        CreditLedger.user_id == user_id,
        CreditLedger.visible_to_user.is_(True),
        CreditLedger.amount != 0,  # e.g. the "withdrawal approved" marker; the hold row's status covers it
    )
    if transaction_type == "CREDIT":
        q = q.filter(CreditLedger.amount >= 0)
    elif transaction_type == "DEBIT":
        q = q.filter(CreditLedger.amount < 0)
    if type_clause is not None:
        # Only market-linked rows can match; grants, refunds and plain adjustments have no market.
        q = q.filter(
            or_(
                and_(CreditLedger.reference_type == "simulation_batch",
                     CreditLedger.reference_id.in_(_in_market_type(db, SimulationBatch, SimulationBatch.id, type_clause))),
                and_(CreditLedger.reference_type.in_(["simulation_entry", "simulation_override"]),
                     CreditLedger.reference_id.in_(_in_market_type(db, SimulationEntry, SimulationEntry.id, type_clause))),
                and_(CreditLedger.reference_type == "result_correction",
                     CreditLedger.reference_id.in_(_in_market_type(db, MarketResult, MarketResult.id, type_clause))),
            )
        )
    if from_date:
        q = q.filter(CreditLedger.created_at >= shape.ist_day_bounds(from_date)[0])
    if to_date:
        q = q.filter(CreditLedger.created_at < shape.ist_day_bounds(to_date)[1])
    return q


class _Context:
    """Everything the page's ledger rows reference, loaded with a handful of IN queries."""

    def __init__(self, db: Session, rows: list[CreditLedger]):
        entry_ids = _ids(rows, ("simulation_entry", "simulation_override"))
        self.entries = {e.id: e for e in db.query(SimulationEntry).filter(SimulationEntry.id.in_(entry_ids))} if entry_ids else {}
        batch_ids = set(_ids(rows, ("simulation_batch",)))
        self.batches = {b.id: b for b in db.query(SimulationBatch).filter(SimulationBatch.id.in_(batch_ids))} if batch_ids else {}
        self.batch_entries: dict[int, list[SimulationEntry]] = {}
        if batch_ids:
            for e in db.query(SimulationEntry).filter(SimulationEntry.batch_id.in_(batch_ids)).order_by(SimulationEntry.id):
                self.batch_entries.setdefault(e.batch_id, []).append(e)
        result_ids = _ids(rows, ("result_correction",))
        self.results = {r.id: r for r in db.query(MarketResult).filter(MarketResult.id.in_(result_ids))} if result_ids else {}
        request_ids = _ids(rows, ("credit_request",))
        self.requests = {r.id: r for r in db.query(CreditRequest).filter(CreditRequest.id.in_(request_ids))} if request_ids else {}

        market_ids = {b.market_id for b in self.batches.values()} | {e.market_id for e in self.entries.values()} | {r.market_id for r in self.results.values()}
        self.markets: dict[int, tuple[Market, str]] = {}
        if market_ids:
            for m, slug in db.query(Market, MarketCategory.slug).join(MarketCategory, MarketCategory.id == Market.category_id).filter(Market.id.in_(market_ids)):
                self.markets[m.id] = (m, slug)
        self.game_types = {g.id: g.code for g in db.query(GameType).all()}

    def market(self, market_id: int | None) -> dict | None:
        found = self.markets.get(market_id) if market_id else None
        return {"id": str(found[0].id), "name": found[0].name, "marketType": found[1]} if found else None


def _bet(entry: SimulationEntry) -> dict:
    return {"number": entry.selection, "points": entry.simulated_credits, "status": _BET_STATUS.get(entry.status, entry.status.upper())}


def _ledger_item(row: CreditLedger, ctx: _Context) -> dict:
    title, kind = _TITLES.get(row.type, (row.type.replace("_", " ").title(), "OTHER"))
    ref = int(row.reference_id) if row.reference_id and row.reference_id.isdigit() else None
    status, description = "SUCCESS", row.note or ""
    market = game_code = txn = None
    bets: list[dict] = []

    if row.reference_type == "simulation_batch" and row.type == "stake":
        # Legacy rows: bets placed before stakes were written one row per number.
        batch = ctx.batches.get(ref)
        if batch:
            market, game_code, txn = ctx.market(batch.market_id), ctx.game_types.get(batch.game_type_id), f"SIM-{batch.id}"
            entries = ctx.batch_entries.get(batch.id, [])
            bets = [_bet(e) for e in entries]
            listed = ", ".join(f"{e.selection} ({e.simulated_credits})" for e in entries[:_MAX_LISTED])
            more = f" +{len(entries) - _MAX_LISTED} more" if len(entries) > _MAX_LISTED else ""
            description = f"{_label(game_code)}: {listed}{more} on {market['name'] if market else 'market'}"
    elif row.reference_type in ("simulation_entry", "simulation_override"):
        entry = ctx.entries.get(ref)
        if entry:
            market, game_code, txn = ctx.market(entry.market_id), ctx.game_types.get(entry.game_type_id), f"SIM-{entry.batch_id}"
            bets = [_bet(entry)]
            where = market["name"] if market else "market"
            if row.reference_type == "simulation_override":
                title, kind = "Outcome Override", "OUTCOME_OVERRIDE"
            elif row.type == "stake":
                description = f"{_label(game_code)}: {entry.selection} ({entry.simulated_credits}) on {where}"
            else:
                description = f"{_label(game_code)} {entry.selection} won on {where}"
    elif row.reference_type == "result_correction":
        title, kind = "Result Correction", "RESULT_CORRECTION"
        result = ctx.results.get(ref)
        market = ctx.market(result.market_id) if result else None
        description = row.note or "Payout reversed: result corrected"
    elif row.type == "grant" and row.reference_type == "credit_request":
        title, kind = "Deposit Approved", "DEPOSIT_APPROVED"
    elif row.type == "grant":
        title, kind = "Credits Added", "CREDITS_ADDED"
    elif row.type == "withdraw_hold":
        req = ctx.requests.get(ref)
        status = {"Pending": "PENDING", "Rejected": "REFUNDED"}.get(req.status, "SUCCESS") if req else "SUCCESS"

    return {
        "id": str(row.id),
        "kind": kind,
        "title": title,
        "description": description,
        "type": "CREDIT" if row.amount >= 0 else "DEBIT",
        "amount": abs(row.amount),
        "balanceAfter": row.balance_after,
        "status": status,
        "transactionId": txn,
        "market": market,
        "gameType": game_code,
        "bets": bets,
        "timestamp": shape.iso_ist(row.created_at),
        "_sort": row.created_at or datetime.min,
    }


def _request_item(req: CreditRequest) -> dict:
    pending = req.status == "Pending"
    return {
        "id": f"REQ_{req.id}",
        "kind": "DEPOSIT_PENDING" if pending else "DEPOSIT_REJECTED",
        "title": "Deposit Pending" if pending else "Deposit Rejected",
        "description": (req.reason if pending else req.admin_note or req.reason) or "Deposit request",
        "type": "CREDIT",
        "amount": req.requested_amount,
        "balanceAfter": None,
        "status": "PENDING" if pending else "REJECTED",
        "transactionId": None,
        "market": None,
        "gameType": None,
        "bets": [],
        "timestamp": shape.iso_ist(req.created_at),
        "_sort": req.created_at or datetime.min,
    }


def build_statement(
    db: Session, user_id: int, *, page: int, limit: int, transaction_type: str | None,
    from_date: date | None, to_date: date | None, type_clause,
) -> list[dict]:
    offset = max(0, (page - 1) * limit)
    fetch = offset + limit  # each source is over-fetched so the merged order is exact for this page
    tx = transaction_type.upper() if transaction_type else None

    ledger_rows = (
        _ledger_query(db, user_id, tx, from_date, to_date, type_clause)
        .order_by(CreditLedger.id.desc()).limit(fetch).all()
    )
    ctx = _Context(db, ledger_rows)
    items = [_ledger_item(r, ctx) for r in ledger_rows]

    # Pending / rejected deposits: not market-linked and always a credit-direction row.
    if type_clause is None and tx != "DEBIT":
        q = db.query(CreditRequest).filter(
            CreditRequest.user_id == user_id,
            func.lower(CreditRequest.request_type) == "deposit",
            CreditRequest.status.in_(["Pending", "Rejected"]),
        )
        if from_date:
            q = q.filter(CreditRequest.created_at >= shape.ist_day_bounds(from_date)[0])
        if to_date:
            q = q.filter(CreditRequest.created_at < shape.ist_day_bounds(to_date)[1])
        items += [_request_item(r) for r in q.order_by(CreditRequest.id.desc()).limit(fetch).all()]

    items.sort(key=lambda i: i["_sort"], reverse=True)
    page_items = items[offset:offset + limit]
    for i in page_items:
        i.pop("_sort")
    return page_items
