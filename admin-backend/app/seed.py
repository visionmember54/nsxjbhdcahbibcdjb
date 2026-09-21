"""Explicit demo-data seeding. Run with `python -m app.seed`.

Wipes and reseeds every table with a realistic slice of activity -- not just
empty config -- so the admin panel shows real numbers on first load: users
with varied balances, resolved (Won/Lost) and Pending simulations, published
historical results, and populated content/reports. Never runs automatically
on app startup.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from app.core.rbac_catalog import PERMISSIONS, ROLE_NAMES, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.db.base import Base, SessionLocal, engine
from app.models.admin import Admin
from app.models.content import EducationalContent, FAQ, HomepageBanner, ScrollingMessage, SiteSetting
from app.models.credit import CreditLedger
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, MarketCategory, StarlineSlot
from app.models.market_result import MarketResult
from app.models.rate import Rate
from app.models.role import Permission, Role, RolePermission
from app.models.simulation import SimulationBatch, SimulationEntry
from app.models.support import SupportMessage, SupportQuery
from app.models.user import User
from app.services import credit_service, result_service
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


def _place_bet(db, *, user, market, game_type, slot=None, stage=None, selection, credits, rate):
    batch = SimulationBatch(
        user_id=user.id, market_id=market.id, slot_id=slot.id if slot else None,
        game_type_id=game_type.id, stage=stage, created_via="admin_manual",
    )
    db.add(batch)
    db.flush()
    entry = SimulationEntry(
        batch_id=batch.id, user_id=user.id, market_id=market.id, slot_id=slot.id if slot else None,
        game_type_id=game_type.id, stage=stage, selection=selection,
        simulated_credits=credits, simulated_rate=rate,
        simulated_return=vs.compute_simulated_return(credits, rate), status="Pending",
    )
    db.add(entry)
    db.flush()
    credit_service.apply_ledger_entry(
        db, user=user, type="stake", amount=-credits, reference_type="simulation_batch",
        reference_id=str(batch.id), note=f"{game_type.code} {selection} on {market.name}",
    )
    return entry


def _publish_result(db, *, market, admin_id, slot=None, days_ago=0, open_panna=None, open_ank=None,
                     close_panna=None, close_ank=None):
    result_date = (date.today() - timedelta(days=days_ago)).isoformat()
    result = MarketResult(market_id=market.id, slot_id=slot.id if slot else None, result_date=result_date, status="Draft")

    if open_panna:
        result.open_panna = open_panna
        result.open_ank = vs.derive_ank_from_panna(open_panna)
    elif open_ank:
        result.open_ank = open_ank

    if close_panna:
        result.close_panna = close_panna
        result.close_ank = vs.derive_ank_from_panna(close_panna)
    elif close_ank:
        result.close_ank = close_ank

    if result.open_ank and result.close_ank:
        result.jodi = vs.derive_jodi(result.open_ank, result.close_ank)

    result.status = "Published"
    result.published_by_admin_id = admin_id
    result.published_at = datetime.now(timezone.utc)
    db.add(result)
    db.flush()

    result_service.evaluate_pending_entries(db, result)
    return result


def wipe_and_reseed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for model in [
            RolePermission,
            Permission,
            Role,
            FAQ,
            EducationalContent,
            ScrollingMessage,
            HomepageBanner,
            SiteSetting,
            SupportMessage,
            SupportQuery,
            SimulationEntry,
            SimulationBatch,
            MarketResult,
            Rate,
            GameTypeConfig,
            StarlineSlot,
            Market,
            GameType,
            MarketCategory,
            CreditLedger,
            User,
            Admin,
        ]:
            db.query(model).delete()
        db.commit()

        admin = Admin(
            name="Super Admin", email="admin@kalyan.com",
            password_hash=hash_password("admin123"), role="super_admin", status="active",
        )
        db.add(admin)
        db.flush()

        permissions = [Permission(code=code, description=desc) for code, desc in PERMISSIONS]
        db.add_all(permissions)
        db.flush()
        perm_by_code = {p.code: p for p in permissions}

        roles = [Role(slug=slug, name=ROLE_NAMES[slug]) for slug in ROLE_PERMISSIONS]
        db.add_all(roles)
        db.flush()
        for role in roles:
            db.add_all(
                RolePermission(role_id=role.id, permission_id=perm_by_code[code].id)
                for code in ROLE_PERMISSIONS[role.slug]
            )
        db.flush()

        categories = [
            MarketCategory(slug="MATKA", name="Matka Markets", display_order=1),
            MarketCategory(slug="STARLINE", name="Starline", display_order=2),
            MarketCategory(slug="GALI_DISAWAR", name="Gali – Disawar", display_order=3),
            MarketCategory(slug="CUSTOM", name="Custom Markets", display_order=4),
        ]
        db.add_all(categories)
        db.flush()
        cat_by_slug = {c.slug: c for c in categories}

        game_types = [
            GameType(code=code, name=name, digit_length=dl, classification_rule=rule, display_order=i)
            for i, (code, name, dl, rule) in enumerate(GAME_TYPES)
        ]
        db.add_all(game_types)
        db.flush()
        gt = {g.code: g for g in game_types}

        today = date.today()

        # --- Matka markets ---
        matka_markets = [
            Market(category_id=cat_by_slug["MATKA"].id, name="MILAN DAY", slug="milan-day", status="OPEN",
                   opening_time=time(15, 0), closing_time=time(17, 0), result_time=time(17, 5), display_order=1),
            Market(category_id=cat_by_slug["MATKA"].id, name="RAJDHANI DAY", slug="rajdhani-day", status="CLOSED",
                   opening_time=time(15, 15), closing_time=time(17, 15), result_time=time(17, 20), display_order=2),
            Market(category_id=cat_by_slug["MATKA"].id, name="KALYAN NIGHT", slug="kalyan-night", status="UPCOMING",
                   opening_time=time(21, 20), closing_time=time(23, 30), result_time=time(23, 35), display_order=3),
            Market(category_id=cat_by_slug["MATKA"].id, name="MILAN NIGHT", slug="milan-night", status="UPCOMING",
                   opening_time=time(21, 0), closing_time=time(23, 0), result_time=time(23, 5), display_order=4),
        ]
        db.add_all(matka_markets)
        db.flush()
        milan_day, rajdhani_day, kalyan_night, milan_night = matka_markets

        for market in matka_markets:
            configs = [
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.SINGLE].id, stage="OPEN"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.SINGLE].id, stage="CLOSE"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.SINGLE_PANNA].id, stage="OPEN"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.SINGLE_PANNA].id, stage="CLOSE"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.DOUBLE_PANNA].id, stage="OPEN"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.DOUBLE_PANNA].id, stage="CLOSE"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.TRIPLE_PANNA].id, stage="OPEN"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.TRIPLE_PANNA].id, stage="CLOSE"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.JODI].id, stage="BOTH"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.OPEN].id, stage="OPEN"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.CLOSE].id, stage="CLOSE"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.HALF_SANGAM].id, stage="BOTH"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.FULL_SANGAM].id, stage="BOTH"),
            ]
            db.add_all(configs)
            for code in [vs.SINGLE, vs.SINGLE_PANNA, vs.DOUBLE_PANNA, vs.TRIPLE_PANNA, vs.JODI, vs.OPEN, vs.CLOSE, vs.HALF_SANGAM, vs.FULL_SANGAM]:
                db.add(Rate(market_id=market.id, game_type_id=gt[code].id,
                            rate=RATE_BY_CODE[code], effective_from=today, status="Active"))
        db.flush()

        # --- Starline market + slots ---
        starline_market = Market(category_id=cat_by_slug["STARLINE"].id, name="Starline", slug="starline",
                                  status="OPEN", display_order=1)
        db.add(starline_market)
        db.flush()

        slot_times = [
            ("10:00 AM", time(10, 0), time(9, 55)),
            ("11:00 AM", time(11, 0), time(10, 55)),
            ("12:00 PM", time(12, 0), time(11, 55)),
            ("01:00 PM", time(13, 0), time(12, 55)),
            ("02:00 PM", time(14, 0), time(13, 55)),
            ("03:00 PM", time(15, 0), time(14, 55)),
        ]
        slots = [
            StarlineSlot(market_id=starline_market.id, slot_name=name, start_time=start,
                         cutoff_time=cutoff, display_order=i)
            for i, (name, start, cutoff) in enumerate(slot_times)
        ]
        db.add_all(slots)
        db.flush()

        for slot in slots:
            for code in [vs.SINGLE, vs.SINGLE_PANNA, vs.DOUBLE_PANNA, vs.TRIPLE_PANNA]:
                db.add(GameTypeConfig(market_id=starline_market.id, slot_id=slot.id, game_type_id=gt[code].id))
                db.add(Rate(market_id=starline_market.id, slot_id=slot.id, game_type_id=gt[code].id,
                            rate=RATE_BY_CODE[code], effective_from=today, status="Active"))
        db.flush()

        # --- Gali-Disawar markets ---
        gali_disawar_markets = [
            Market(category_id=cat_by_slug["GALI_DISAWAR"].id, name="GALI", slug="gali", status="OPEN",
                   closing_time=time(23, 10), result_time=time(23, 10), display_order=1),
            Market(category_id=cat_by_slug["GALI_DISAWAR"].id, name="DISAWAR", slug="disawar", status="OPEN",
                   closing_time=time(4, 30), result_time=time(4, 30), display_order=2),
        ]
        db.add_all(gali_disawar_markets)
        db.flush()
        gali, disawar = gali_disawar_markets

        for market in gali_disawar_markets:
            db.add_all([
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.SINGLE].id, stage="OPEN"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.SINGLE].id, stage="CLOSE"),
                GameTypeConfig(market_id=market.id, game_type_id=gt[vs.JODI].id, stage="BOTH"),
            ])
            db.add(Rate(market_id=market.id, game_type_id=gt[vs.SINGLE].id,
                        rate=RATE_BY_CODE[vs.SINGLE], effective_from=today, status="Active"))
            db.add(Rate(market_id=market.id, game_type_id=gt[vs.JODI].id,
                        rate=RATE_BY_CODE[vs.JODI], effective_from=today, status="Active"))
        db.flush()

        # --- A Custom-category market, so "Custom Markets" isn't empty ---
        weekend_special = Market(category_id=cat_by_slug["CUSTOM"].id, name="WEEKEND SPECIAL", slug="weekend-special",
                                  status="UPCOMING", description="A limited-time custom market for weekend demos.",
                                  opening_time=time(18, 0), closing_time=time(20, 0), result_time=time(20, 5), display_order=1)
        db.add(weekend_special)
        db.flush()
        db.add_all([
            GameTypeConfig(market_id=weekend_special.id, game_type_id=gt[vs.SINGLE].id, stage="OPEN"),
            GameTypeConfig(market_id=weekend_special.id, game_type_id=gt[vs.JODI].id, stage="BOTH"),
        ])
        db.add(Rate(market_id=weekend_special.id, game_type_id=gt[vs.JODI].id, rate=950, effective_from=today, status="Active"))
        db.flush()

        # --- Users (learners) ---
        user_specs = [
            ("Aman Jha", "8076580694", "aman@example.com", 10_000, "active"),
            ("Vijendra Mewada", "8815306802", "vj@example.com", 5_000, "active"),
            ("Priya Sharma", "9812345678", "priya@example.com", 7_500, "active"),
            ("Rohan Verma", "9900112233", "rohan@example.com", 3_200, "active"),
            ("Sneha Patel", "9123456780", "sneha@example.com", 12_000, "active"),
            ("Karan Singh", "9988776655", "karan@example.com", 500, "disabled"),
            ("Anita Desai", "9871234560", "anita@example.com", 4_500, "active"),
            ("Vikram Rao", "9090909090", "vikram@example.com", 8_800, "active"),
        ]
        users = [
            User(name=name, phone=phone, email=email, password_hash=hash_password("user12345"),
                 status=status_, balance=balance)
            for name, phone, email, balance, status_ in user_specs
        ]
        db.add_all(users)
        db.flush()
        u = {name.split()[0].lower(): user for (name, *_), user in zip(user_specs, users)}
        for user in users:
            db.add(CreditLedger(user_id=user.id, type="grant", amount=user.balance,
                                 balance_after=user.balance, reference_type="seed", note="Initial learning credits"))
        db.flush()

        # --- Simulation history: MILAN DAY, 2 days ago (resolved) ---
        _place_bet(db, user=u["aman"], market=milan_day, game_type=gt[vs.SINGLE], stage="OPEN", selection="8", credits=50, rate=RATE_BY_CODE[vs.SINGLE])
        _place_bet(db, user=u["priya"], market=milan_day, game_type=gt[vs.SINGLE_PANNA], stage="OPEN", selection="459", credits=30, rate=RATE_BY_CODE[vs.SINGLE_PANNA])
        _place_bet(db, user=u["rohan"], market=milan_day, game_type=gt[vs.JODI], selection="89", credits=100, rate=RATE_BY_CODE[vs.JODI])
        _place_bet(db, user=u["sneha"], market=milan_day, game_type=gt[vs.JODI], selection="12", credits=80, rate=RATE_BY_CODE[vs.JODI])
        _place_bet(db, user=u["vikram"], market=milan_day, game_type=gt[vs.DOUBLE_PANNA], stage="OPEN", selection="224", credits=40, rate=RATE_BY_CODE[vs.DOUBLE_PANNA])
        _place_bet(db, user=u["anita"], market=milan_day, game_type=gt[vs.SINGLE], stage="CLOSE", selection="9", credits=60, rate=RATE_BY_CODE[vs.SINGLE])
        _publish_result(db, market=milan_day, admin_id=admin.id, days_ago=2, open_panna="459", close_panna="234")

        # --- MILAN DAY, yesterday (resolved) ---
        _place_bet(db, user=u["aman"], market=milan_day, game_type=gt[vs.JODI], selection="16", credits=100, rate=RATE_BY_CODE[vs.JODI])
        _place_bet(db, user=u["vijendra"], market=milan_day, game_type=gt[vs.SINGLE_PANNA], stage="OPEN", selection="123", credits=50, rate=RATE_BY_CODE[vs.SINGLE_PANNA])
        _place_bet(db, user=u["priya"], market=milan_day, game_type=gt[vs.SINGLE], stage="OPEN", selection="1", credits=40, rate=RATE_BY_CODE[vs.SINGLE])
        _place_bet(db, user=u["sneha"], market=milan_day, game_type=gt[vs.TRIPLE_PANNA], stage="CLOSE", selection="666", credits=20, rate=RATE_BY_CODE[vs.TRIPLE_PANNA])
        _place_bet(db, user=u["vikram"], market=milan_day, game_type=gt[vs.SINGLE], stage="CLOSE", selection="6", credits=70, rate=RATE_BY_CODE[vs.SINGLE])
        _place_bet(db, user=u["anita"], market=milan_day, game_type=gt[vs.DOUBLE_PANNA], stage="OPEN", selection="112", credits=25, rate=RATE_BY_CODE[vs.DOUBLE_PANNA])
        _publish_result(db, market=milan_day, admin_id=admin.id, days_ago=1, open_panna="128", close_panna="600")

        # --- MILAN DAY, today (still Pending -- market is OPEN, no result yet) ---
        _place_bet(db, user=u["aman"], market=milan_day, game_type=gt[vs.SINGLE], stage="OPEN", selection="5", credits=50, rate=RATE_BY_CODE[vs.SINGLE])
        _place_bet(db, user=u["vijendra"], market=milan_day, game_type=gt[vs.JODI], selection="27", credits=100, rate=RATE_BY_CODE[vs.JODI])
        _place_bet(db, user=u["priya"], market=milan_day, game_type=gt[vs.DOUBLE_PANNA], stage="OPEN", selection="225", credits=40, rate=RATE_BY_CODE[vs.DOUBLE_PANNA])

        # --- RAJDHANI DAY, yesterday (resolved, market now CLOSED) ---
        _place_bet(db, user=u["rohan"], market=rajdhani_day, game_type=gt[vs.JODI], selection="43", credits=60, rate=RATE_BY_CODE[vs.JODI])
        _place_bet(db, user=u["aman"], market=rajdhani_day, game_type=gt[vs.SINGLE], stage="OPEN", selection="4", credits=30, rate=RATE_BY_CODE[vs.SINGLE])
        _place_bet(db, user=u["priya"], market=rajdhani_day, game_type=gt[vs.SINGLE_PANNA], stage="CLOSE", selection="111", credits=45, rate=RATE_BY_CODE[vs.SINGLE_PANNA])
        _publish_result(db, market=rajdhani_day, admin_id=admin.id, days_ago=1, open_panna="257", close_panna="111")

        # --- GALI, yesterday (resolved -- Gali/Disawar use direct ank, no panna) ---
        _place_bet(db, user=u["anita"], market=gali, game_type=gt[vs.JODI], selection="48", credits=90, rate=RATE_BY_CODE[vs.JODI])
        _place_bet(db, user=u["vikram"], market=gali, game_type=gt[vs.SINGLE], stage="OPEN", selection="4", credits=35, rate=RATE_BY_CODE[vs.SINGLE])
        _place_bet(db, user=u["sneha"], market=gali, game_type=gt[vs.SINGLE], stage="CLOSE", selection="8", credits=55, rate=RATE_BY_CODE[vs.SINGLE])
        _place_bet(db, user=u["rohan"], market=gali, game_type=gt[vs.JODI], selection="99", credits=20, rate=RATE_BY_CODE[vs.JODI])
        _publish_result(db, market=gali, admin_id=admin.id, days_ago=1, open_ank="4", close_ank="8")

        # --- Starline slot: one pending bet, no result declared yet ---
        _place_bet(db, user=u["sneha"], market=starline_market, slot=slots[0], game_type=gt[vs.SINGLE_PANNA],
                   selection="234", credits=25, rate=RATE_BY_CODE[vs.SINGLE_PANNA])

        # --- A couple of manual admin credit adjustments, for ledger variety ---
        credit_service.adjust_credits(db, u["karan"], -200, admin.id, "Correction: duplicate grant reversed")
        credit_service.grant_credits(db, u["rohan"], 500, admin.id, "Bonus for referring a friend")

        # --- Content ---
        db.add_all([
            SiteSetting(key="support_phone", value="+91 7000000000"),
            SiteSetting(key="support_whatsapp", value="+91 7000000000"),
            SiteSetting(key="support_email", value="support@example.com"),
            SiteSetting(key="hero_image_url", value=""),
            SiteSetting(key="payment_upi_id", value="kalyanmerchant@icici"),
            SiteSetting(key="payment_merchant_name", value="Kalyan Milan"),
            SiteSetting(key="payment_min_deposit", value="300"),
            SiteSetting(key="payment_max_deposit", value="100000"),
            SiteSetting(key="payment_min_withdrawal", value="1000"),
            SiteSetting(
                key="payment_instructions",
                value="1. Pay using UPI to the UPI ID or scan QR.\n2. Note down the 12-digit UTR number.\n3. Enter amount and UTR below.",
            ),
        ])
        db.add_all([
            HomepageBanner(image_url="", title="Welcome to the simulator", display_order=1),
            HomepageBanner(image_url="", title="New: Starline slots now live", link="/dashboard/markets/starline", display_order=2),
        ])
        db.add_all([
            ScrollingMessage(text="This is an educational simulator using virtual Learning Credits only.", display_order=1),
            ScrollingMessage(text="No real money is ever deposited, withdrawn, or wagered on this platform.", display_order=2),
        ])
        db.add_all([
            FAQ(question="Is real money involved?",
                answer="No. This platform uses simulated Learning Credits for educational purposes only.", display_order=1),
            FAQ(question="How do I get more Learning Credits?",
                answer="An admin can grant, adjust, or reset your balance from the Users section.", display_order=2),
            FAQ(question="What happens if a result is corrected?",
                answer="Any payout already made is reversed and every affected selection is re-evaluated against the new result.", display_order=3),
        ])
        db.add_all([
            EducationalContent(
                game_type_id=gt[vs.SINGLE_PANNA].id, title="Single Panna",
                description="A three-digit panel with three different digits.", example="123",
                probability_explanation="All three digits are distinct.",
            ),
            EducationalContent(
                game_type_id=gt[vs.DOUBLE_PANNA].id, title="Double Panna",
                description="A three-digit panel containing two identical digits.", example="112",
                probability_explanation="Two digits are identical while the third digit is different.",
            ),
            EducationalContent(
                game_type_id=gt[vs.TRIPLE_PANNA].id, title="Triple Panna",
                description="A three-digit panel where all three digits are identical.", example="777",
                probability_explanation="All three digits match -- the rarest and highest-paying panel.",
            ),
            EducationalContent(
                game_type_id=gt[vs.JODI].id, title="Jodi",
                description="A two-digit pair formed by combining the Open Ank and Close Ank.", example="16",
                probability_explanation="Only resolves once both Open and Close results are published.",
            ),
        ])

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    wipe_and_reseed()
