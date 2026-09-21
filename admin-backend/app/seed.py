"""Idempotent game-catalog seeding. Run with `python -m app.seed_games`.

Unlike `app.seed` (which wipes and rebuilds EVERY table, including real users,
credits, and bet history -- meant for local/demo resets only), this script
only ensures the game catalog exists: market categories, game types, markets,
Starline slots, per-market game-type configs, and payout rates.

It is get-or-create by natural key (MarketCategory.slug, Market.slug,
GameType.code) -- running it twice, or running it against a database that
already has real users/deposits/bets, never deletes or recreates anything.
It is safe to run as a one-off job on Render at any time.

No fake users, credits, simulated bets, or results are created here --
that demo "money" data lives only in app.seed.wipe_and_reseed for local dev.
"""
from __future__ import annotations

from datetime import date, time

from app.db.base import Base, SessionLocal, engine
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, MarketCategory, StarlineSlot
from app.models.rate import Rate
from app.services import validation_service as vs

RATE_BY_CODE = {
    vs.SINGLE: 95,
    vs.OPEN: 95,
    vs.CLOSE: 95,
    vs.JODI: 950,
    vs.SINGLE_PANNA: 1500,
    vs.DOUBLE_PANNA: 3000,
    vs.TRIPLE_PANNA: 9000,
    vs.HALF_SANGAM: 10000,
    vs.FULL_SANGAM: 100000,
}

GAME_TYPES = [
    (vs.SINGLE, "Single / Ank", 1, "NONE"),
    (vs.JODI, "Jodi", 2, "NONE"),
    (vs.SINGLE_PANNA, "Single Panna", 3, "PANNA_SINGLE"),
    (vs.DOUBLE_PANNA, "Double Panna", 3, "PANNA_DOUBLE"),
    (vs.TRIPLE_PANNA, "Triple Panna", 3, "PANNA_TRIPLE"),
    (vs.OPEN, "Open Ank", 1, "NONE"),
    (vs.CLOSE, "Close Ank", 1, "NONE"),
    (vs.OPEN_CLOSE, "Open + Close", 1, "NONE"),
    (vs.HALF_SANGAM, "Half Sangam", 5, "SANGAM_HALF"),
    (vs.FULL_SANGAM, "Full Sangam", 7, "SANGAM_FULL"),
]

CATEGORIES = [
    ("MATKA", "Matka Markets", 1),
    ("STARLINE", "Starline", 2),
    ("GALI_DISAWAR", "Gali – Disawar", 3),
    ("CUSTOM", "Custom Markets", 4),
]

MATKA_GAME_CODES = [
    vs.SINGLE, vs.SINGLE_PANNA, vs.DOUBLE_PANNA, vs.TRIPLE_PANNA,
    vs.JODI, vs.OPEN, vs.CLOSE, vs.HALF_SANGAM, vs.FULL_SANGAM,
]

STARLINE_SLOT_TIMES = [
    ("10:00 AM", time(10, 0), time(9, 55)),
    ("11:00 AM", time(11, 0), time(10, 55)),
    ("12:00 PM", time(12, 0), time(11, 55)),
    ("01:00 PM", time(13, 0), time(12, 55)),
    ("02:00 PM", time(14, 0), time(13, 55)),
    ("03:00 PM", time(15, 0), time(14, 55)),
]
STARLINE_GAME_CODES = [vs.SINGLE, vs.SINGLE_PANNA, vs.DOUBLE_PANNA, vs.TRIPLE_PANNA]

GALI_DISAWAR_MARKETS = [
    ("GALI", "gali", time(23, 10)),
    ("DISAWAR", "disawar", time(4, 30)),
]


def _get_or_create_category(db, slug: str, name: str, order: int) -> MarketCategory:
    cat = db.query(MarketCategory).filter_by(slug=slug).first()
    if cat:
        return cat
    cat = MarketCategory(slug=slug, name=name, display_order=order)
    db.add(cat)
    db.flush()
    print(f"  + category {slug}")
    return cat


def _get_or_create_game_type(db, code: str, name: str, digit_length: int, rule: str, order: int) -> GameType:
    gt = db.query(GameType).filter_by(code=code).first()
    if gt:
        return gt
    gt = GameType(code=code, name=name, digit_length=digit_length, classification_rule=rule, display_order=order)
    db.add(gt)
    db.flush()
    print(f"  + game type {code}")
    return gt


def _get_or_create_market(db, *, category_id: int, name: str, slug: str, status: str,
                           opening_time=None, closing_time=None, result_time=None,
                           display_order: int = 0, description: str = "") -> Market:
    market = db.query(Market).filter_by(slug=slug).first()
    if market:
        return market
    market = Market(
        category_id=category_id, name=name, slug=slug, status=status,
        opening_time=opening_time, closing_time=closing_time, result_time=result_time,
        display_order=display_order, description=description,
    )
    db.add(market)
    db.flush()
    print(f"  + market {slug}")
    return market


def _ensure_game_type_config(db, *, market_id: int, game_type_id: int, slot_id: int | None = None, stage: str | None = None) -> None:
    exists = db.query(GameTypeConfig).filter_by(
        market_id=market_id, slot_id=slot_id, game_type_id=game_type_id, stage=stage,
    ).first()
    if exists:
        return
    db.add(GameTypeConfig(market_id=market_id, slot_id=slot_id, game_type_id=game_type_id, stage=stage))


def _ensure_active_rate(db, *, market_id: int, game_type_id: int, rate: int, slot_id: int | None = None) -> None:
    exists = db.query(Rate).filter_by(
        market_id=market_id, slot_id=slot_id, game_type_id=game_type_id, status="Active",
    ).first()
    if exists:
        return
    db.add(Rate(market_id=market_id, slot_id=slot_id, game_type_id=game_type_id, rate=rate,
                effective_from=date.today(), status="Active"))


def _get_or_create_slot(db, *, market_id: int, slot_name: str, start_time: time, cutoff_time: time, order: int) -> StarlineSlot:
    slot = db.query(StarlineSlot).filter_by(market_id=market_id, slot_name=slot_name).first()
    if slot:
        return slot
    slot = StarlineSlot(market_id=market_id, slot_name=slot_name, start_time=start_time,
                         cutoff_time=cutoff_time, display_order=order)
    db.add(slot)
    db.flush()
    print(f"  + starline slot {slot_name}")
    return slot


def seed_games() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cat_by_slug = {slug: _get_or_create_category(db, slug, name, order) for slug, name, order in CATEGORIES}
        gt = {code: _get_or_create_game_type(db, code, name, dl, rule, i)
              for i, (code, name, dl, rule) in enumerate(GAME_TYPES)}
        db.flush()

        # --- Matka markets ---
        matka_defs = [
            ("MILAN DAY", "milan-day", "OPEN", time(15, 0), time(17, 0), time(17, 5), 1),
            ("RAJDHANI DAY", "rajdhani-day", "CLOSED", time(15, 15), time(17, 15), time(17, 20), 2),
            ("KALYAN NIGHT", "kalyan-night", "UPCOMING", time(21, 20), time(23, 30), time(23, 35), 3),
            ("MILAN NIGHT", "milan-night", "UPCOMING", time(21, 0), time(23, 0), time(23, 5), 4),
        ]
        for name, slug, status, open_t, close_t, result_t, order in matka_defs:
            market = _get_or_create_market(
                db, category_id=cat_by_slug["MATKA"].id, name=name, slug=slug, status=status,
                opening_time=open_t, closing_time=close_t, result_time=result_t, display_order=order,
            )
            for code in MATKA_GAME_CODES:
                if code in (vs.SINGLE, vs.SINGLE_PANNA, vs.DOUBLE_PANNA, vs.TRIPLE_PANNA):
                    _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[code].id, stage="OPEN")
                    _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[code].id, stage="CLOSE")
                elif code == vs.OPEN:
                    _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[code].id, stage="OPEN")
                elif code == vs.CLOSE:
                    _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[code].id, stage="CLOSE")
                else:
                    _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[code].id, stage="BOTH")
                _ensure_active_rate(db, market_id=market.id, game_type_id=gt[code].id, rate=RATE_BY_CODE[code])

        # --- Starline: one umbrella market + 6 daily slots ---
        starline_market = _get_or_create_market(
            db, category_id=cat_by_slug["STARLINE"].id, name="Starline", slug="starline",
            status="OPEN", display_order=1,
        )
        for i, (slot_name, start_t, cutoff_t) in enumerate(STARLINE_SLOT_TIMES):
            slot = _get_or_create_slot(db, market_id=starline_market.id, slot_name=slot_name,
                                        start_time=start_t, cutoff_time=cutoff_t, order=i)
            for code in STARLINE_GAME_CODES:
                _ensure_game_type_config(db, market_id=starline_market.id, slot_id=slot.id, game_type_id=gt[code].id)
                _ensure_active_rate(db, market_id=starline_market.id, slot_id=slot.id,
                                     game_type_id=gt[code].id, rate=RATE_BY_CODE[code])

        # --- Gali-Disawar ---
        for i, (name, slug, close_t) in enumerate(GALI_DISAWAR_MARKETS):
            market = _get_or_create_market(
                db, category_id=cat_by_slug["GALI_DISAWAR"].id, name=name, slug=slug, status="OPEN",
                closing_time=close_t, result_time=close_t, display_order=i + 1,
            )
            _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[vs.SINGLE].id, stage="OPEN")
            _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[vs.SINGLE].id, stage="CLOSE")
            _ensure_game_type_config(db, market_id=market.id, game_type_id=gt[vs.JODI].id, stage="BOTH")
            _ensure_active_rate(db, market_id=market.id, game_type_id=gt[vs.SINGLE].id, rate=RATE_BY_CODE[vs.SINGLE])
            _ensure_active_rate(db, market_id=market.id, game_type_id=gt[vs.JODI].id, rate=RATE_BY_CODE[vs.JODI])

        # --- One Custom-category market so that tab isn't empty ---
        weekend = _get_or_create_market(
            db, category_id=cat_by_slug["CUSTOM"].id, name="WEEKEND SPECIAL", slug="weekend-special",
            status="UPCOMING", description="A limited-time custom market for weekend demos.",
            opening_time=time(18, 0), closing_time=time(20, 0), result_time=time(20, 5), display_order=1,
        )
        _ensure_game_type_config(db, market_id=weekend.id, game_type_id=gt[vs.SINGLE].id, stage="OPEN")
        _ensure_game_type_config(db, market_id=weekend.id, game_type_id=gt[vs.JODI].id, stage="BOTH")
        _ensure_active_rate(db, market_id=weekend.id, game_type_id=gt[vs.JODI].id, rate=RATE_BY_CODE[vs.JODI])

        db.commit()
        print("Game catalog seed complete -- no users, credits, or bets were touched.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_games()
