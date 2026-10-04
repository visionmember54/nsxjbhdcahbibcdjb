from __future__ import annotations

import re
from datetime import date, datetime, time

import pytest

from app.models.credit import CreditLedger
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, MarketCategory, StarlineSlot
from app.models.rate import Rate
from app.models.simulation import SimulationEntry
from app.tests.conftest import TestingSessionLocal


@pytest.fixture(autouse=True)
def _starline_and_gali():
    db = TestingSessionLocal()
    star = MarketCategory(slug="STARLINE", name="Starline", display_order=2)
    gali = MarketCategory(slug="GALI_DISAWAR", name="Gali – Disawar", display_order=3)
    db.add_all([star, gali])
    db.flush()
    gt = {g.code: g for g in db.query(GameType).all()}

    sm = Market(category_id=star.id, name="Starline", slug="starline", status="OPEN", display_order=5)
    gm = Market(category_id=gali.id, name="DISAWAR", slug="disawar", status="OPEN", display_order=6, closing_time=time(23, 59, 59))
    db.add_all([sm, gm])
    db.flush()

    open_slot = StarlineSlot(market_id=sm.id, slot_name="12:00 PM", start_time=time(12, 0), cutoff_time=time(23, 59, 59), display_order=1)
    late_slot = StarlineSlot(market_id=sm.id, slot_name="1:00 PM", start_time=time(13, 0), cutoff_time=time(0, 0, 1), display_order=2)
    db.add_all([open_slot, late_slot])
    db.flush()
    for slot in (open_slot, late_slot):
        db.add(GameTypeConfig(market_id=sm.id, slot_id=slot.id, game_type_id=gt["SINGLE"].id))
        db.add(Rate(market_id=sm.id, slot_id=slot.id, game_type_id=gt["SINGLE"].id, rate=95, effective_from=date(2020, 1, 1), status="Active"))

    for stage in ("OPEN", "CLOSE"):
        db.add(GameTypeConfig(market_id=gm.id, game_type_id=gt["SINGLE"].id, stage=stage))
    db.add(GameTypeConfig(market_id=gm.id, game_type_id=gt["JODI"].id, stage="BOTH"))
    for code in ("SINGLE", "JODI"):
        db.add(Rate(market_id=gm.id, game_type_id=gt[code].id, rate=95, effective_from=date(2020, 1, 1), status="Active"))
    db.commit()
    db.close()


def _bet(client, headers, path="/api/v1/bets/place", **body):
    return client.post(path, headers=headers, json=body)


def _matka_id(client, auth_headers):
    return next(m["id"] for m in client.get("/admin/markets?limit=10", headers=auth_headers).json()["items"] if m["name"] == "TESTGAME")


def _bids(client, headers, **params):
    resp = client.get("/api/v1/history/bids", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["bids"]


# ---- Starline ---------------------------------------------------------------

def test_starline_bet_by_slot_time_in_market_name(client, user_headers):
    """Exactly what the app sent."""
    resp = _bet(client, user_headers, marketName="KALYAN STARLINE 12:00 PM", betType="SINGLE DIGIT", session="OPEN",
                items=[{"number": "1", "points": 50}, {"number": "2", "points": 50}], totalPoints=100)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["deductedPoints"] == 100


def test_starline_bet_by_slot_id_and_variant_time_formats(client, user_headers):
    db = TestingSessionLocal()
    slot_id = db.query(StarlineSlot).filter_by(slot_name="12:00 PM").one().id
    db.close()
    assert _bet(client, user_headers, slotId=str(slot_id), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "3", "points": 10}]).status_code == 200
    assert _bet(client, user_headers, marketName="STARLINE 12:00 pm", betType="SINGLE DIGIT", session="OPEN", items=[{"number": "4", "points": 10}]).status_code == 200


def test_starline_slots_carry_their_own_market_name_when_multiple_exist(client):
    """With only one Starline market, the old top-level marketName happened
    to be right for every slot by coincidence. With a second Starline market
    (a second 'game'), each slot in the flat list must say which market it's
    actually from -- not silently inherit the first market's name."""
    db = TestingSessionLocal()
    star = db.query(MarketCategory).filter_by(slug="STARLINE").one()
    second = Market(category_id=star.id, name="MADHUR STARLINE", slug="madhur-starline", status="OPEN", display_order=7)
    db.add(second)
    db.flush()
    second_slot = StarlineSlot(market_id=second.id, slot_name="2:00 PM", start_time=time(14, 0), cutoff_time=time(23, 59, 59), display_order=1)
    db.add(second_slot)
    db.commit()
    db.close()

    resp = client.get("/api/v1/starline/slots")
    assert resp.status_code == 200, resp.text
    slots = resp.json()["data"]["slots"]

    by_time = {s["timeLabel"]: s for s in slots}
    assert by_time["12:00 PM"]["marketName"] == "Starline"
    assert by_time["2:00 PM"]["marketName"] == "MADHUR STARLINE"
    assert by_time["12:00 PM"]["marketId"] != by_time["2:00 PM"]["marketId"]


def test_starline_bet_is_stored_on_the_slot_and_shows_in_history(client, user_headers):
    _bet(client, user_headers, marketName="KALYAN STARLINE 12:00 PM", betType="SINGLE DIGIT", session="OPEN", items=[{"number": "1", "points": 50}])
    assert _bids(client, user_headers) == []  # no market_type defaults to REGULAR, which excludes Starline
    assert len(_bids(client, user_headers, market_type="STARLINE")) == 1
    assert _bids(client, user_headers, market_type="REGULAR") == []
    assert len(_bids(client, user_headers, market_type="ALL")) == 1


def test_starline_market_without_slot_is_a_clear_400(client, user_headers):
    resp = _bet(client, user_headers, marketName="Starline", betType="SINGLE DIGIT", session="OPEN", items=[{"number": "1", "points": 10}])
    assert resp.status_code == 400 and "slot" in resp.json()["message"].lower()


def test_starline_slot_past_cutoff_is_rejected(client, user_headers):
    resp = _bet(client, user_headers, marketName="STARLINE 1:00 PM", betType="SINGLE DIGIT", session="OPEN", items=[{"number": "1", "points": 10}])
    assert resp.status_code == 400 and resp.json()["error"] == "SLOT_CLOSED"


def test_starline_left_right_jodi_digit_bids_show_distinct_admin_editable_names(client, user_headers):
    """Unlike Gali-Disawar, Starline's LEFT/RIGHT/JODI DIGIT bets each already
    map to their own GameType (OPEN/CLOSE/JODI, distinct from the shared
    SINGLE used for SINGLE DIGIT) -- so they show up as distinct, separately
    admin-renameable names in bid history without any special-casing."""
    db = TestingSessionLocal()
    slot_id = db.query(StarlineSlot).filter_by(slot_name="12:00 PM").one().id
    market_id = db.query(StarlineSlot).filter_by(id=slot_id).one().market_id
    gt = {g.code: g.id for g in db.query(GameType).all()}
    # OPEN/CLOSE aren't in the base test seed (only SINGLE/JODI/panna types
    # are) -- same as _enable_sangam below, add them here rather than assume
    # they exist.
    for code, name in (("OPEN", "Open Ank"), ("CLOSE", "Close Ank")):
        if code not in gt:
            new_gt = GameType(code=code, name=name, digit_length=1, classification_rule="NONE")
            db.add(new_gt)
            db.flush()
            gt[code] = new_gt.id
    for code in ("OPEN", "CLOSE", "JODI"):
        db.add(GameTypeConfig(market_id=market_id, slot_id=slot_id, game_type_id=gt[code]))
        db.add(Rate(market_id=market_id, slot_id=slot_id, game_type_id=gt[code], rate=95, effective_from=date(2020, 1, 1), status="Active"))
    db.commit()
    db.close()

    assert _bet(client, user_headers, slotId=str(slot_id), betType="LEFT DIGIT", session="OPEN", items=[{"number": "1", "points": 10}]).status_code == 200
    assert _bet(client, user_headers, slotId=str(slot_id), betType="RIGHT DIGIT", session="CLOSE", items=[{"number": "2", "points": 10}]).status_code == 200
    assert _bet(client, user_headers, slotId=str(slot_id), betType="JODI DIGIT", items=[{"number": "34", "points": 10}]).status_code == 200
    assert _bet(client, user_headers, slotId=str(slot_id), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "5", "points": 10}]).status_code == 200

    bids = {b["selection"]: b["gameType"] for b in _bids(client, user_headers, market_type="STARLINE")}
    assert bids == {"1": "Open Ank", "2": "Close Ank", "34": "Jodi", "5": "Single"}


def test_unknown_market_name_still_404(client, user_headers):
    resp = _bet(client, user_headers, marketName="NO SUCH MARKET", betType="SINGLE DIGIT", session="OPEN", items=[{"number": "1", "points": 10}])
    assert resp.status_code == 404


# ---- Gali-Desawar -----------------------------------------------------------

def test_gali_right_digit_with_open_session_from_the_app(client, user_headers):
    """Exactly what the app sent: RIGHT DIGIT + session OPEN returned GAME_DISABLED before."""
    resp = _bet(client, user_headers, path="/api/v1/gali-desawar/bets", gameId="DISAWAR", marketId="DISAWAR", betType="RIGHT DIGIT",
                session="OPEN", numbers=[{"number": "7", "points": 50}, {"number": "8", "points": 50}], totalPoints=100)
    assert resp.status_code == 200, resp.text
    bid = _bids(client, user_headers, market_type="GALI_DESAWAR")[0]
    assert (bid["gameType"], bid["stage"]) == ("Right Digit", "CLOSE")


def test_gali_left_digit_and_jodi(client, user_headers):
    left = _bet(client, user_headers, path="/api/v1/gali-desawar/bets", marketId="DISAWAR", betType="LEFT DIGIT", numbers=[{"number": "3", "points": 10}])
    jodi = _bet(client, user_headers, path="/api/v1/gali-desawar/bets", marketId="DISAWAR", betType="JODI DIGIT", session="OPEN", numbers=[{"number": "45", "points": 10}])
    assert left.status_code == 200 and jodi.status_code == 200, (left.text, jodi.text)
    stages = {(b["gameType"], b["stage"]) for b in _bids(client, user_headers, market_type="GALI_DISAWAR")}
    assert stages == {("Left Digit", "OPEN"), ("Jodi Digit", None)}


# ---- Open/closed rules match the app's session states ---------------------------

def _set_window(client, auth_headers, mid):
    # cutoff already passed, close still ahead: the app shows this market as CLOSING / bettable
    client.patch(f"/admin/markets/{mid}", headers=auth_headers, json={"cutoff_time": "00:00:01", "closing_time": "23:59:59"})


def test_close_session_bet_allowed_between_cutoff_and_close(client, auth_headers, user_headers):
    mid = _matka_id(client, auth_headers)
    _set_window(client, auth_headers, mid)
    close = _bet(client, user_headers, marketId=str(mid), betType="SINGLE DIGIT", session="CLOSE", items=[{"number": "5", "points": 10}])
    assert close.status_code == 200, close.text


def test_open_and_jodi_bets_stop_at_cutoff(client, auth_headers, user_headers):
    mid = _matka_id(client, auth_headers)
    _set_window(client, auth_headers, mid)
    open_ = _bet(client, user_headers, marketId=str(mid), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "5", "points": 10}])
    jodi_claiming_close = _bet(client, user_headers, marketId=str(mid), betType="JODI DIGIT", session="CLOSE", items=[{"number": "16", "points": 10}])
    for resp in (open_, jodi_claiming_close):  # a jodi cannot dodge the cutoff by claiming the CLOSE session
        assert resp.status_code == 400 and resp.json()["error"] == "CUTOFF_PASSED"


# ---- IST dates and timestamps ---------------------------------------------------

def _backdate_last_bet(utc_when: datetime):
    db = TestingSessionLocal()
    for e in db.query(SimulationEntry).all():
        e.created_at = utc_when
    for row in db.query(CreditLedger).filter(CreditLedger.type == "stake"):
        row.created_at = utc_when
    db.commit()
    db.close()


def test_history_date_is_an_ist_day(client, auth_headers, user_headers):
    """The bet in the app's log: placed 19:41 UTC on the 21st = 01:11 IST on the 22nd."""
    mid = _matka_id(client, auth_headers)
    _bet(client, user_headers, marketId=str(mid), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "5", "points": 10}])
    _backdate_last_bet(datetime(2026, 9, 21, 19, 41))
    assert len(_bids(client, user_headers, date="22-09-2026")) == 1
    assert _bids(client, user_headers, date="21-09-2026") == []


def test_statement_date_filter_is_an_ist_day(client, auth_headers, user_headers):
    mid = _matka_id(client, auth_headers)
    _bet(client, user_headers, marketId=str(mid), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "5", "points": 10}])
    _backdate_last_bet(datetime(2026, 9, 21, 19, 41))

    def rows(**p):
        return client.get("/api/v1/wallet/statement", params=p, headers=user_headers).json()["data"]["transactions"]

    assert len(rows(from_date="2026-09-22", to_date="2026-09-22")) == 1
    assert rows(from_date="2026-09-21", to_date="2026-09-21") == []
    assert rows(from_date="2026-09-22")[0]["timestamp"] == "2026-09-22T01:11:00+05:30"


def test_bid_history_timestamps_are_formatted_ist(client, auth_headers, user_headers):
    """Bid/Win History renders createdAt/resolvedAt as "dd-MM-yyyy hh:mm a" in IST,
    not a raw ISO timestamp -- see app_api_service.format_ist."""
    mid = _matka_id(client, auth_headers)
    _bet(client, user_headers, marketId=str(mid), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "5", "points": 10}])
    bid = _bids(client, user_headers)[0]
    assert re.fullmatch(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2} (AM|PM)", bid["createdAt"])
    assert bid["resolvedAt"] is None
    assert bid["marketName"]


def test_app_timestamps_carry_the_ist_offset(client, auth_headers, user_headers):
    client.post("/api/v1/wallet/deposit/initiate", headers=user_headers, json={"amount": 500})
    assert client.get("/api/v1/wallet/credit-requests", headers=user_headers).json()["data"]["requests"][0]["createdAt"].endswith("+05:30")


def test_bid_history_shows_success_not_pending(client, auth_headers, user_headers):
    """Bid History confirms a bet was placed -- it never reveals Won/Lost, so a
    still-unresolved bet shows "SUCCESS", not the real "Pending" status."""
    mid = _matka_id(client, auth_headers)
    _bet(client, user_headers, marketId=str(mid), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "5", "points": 10}])
    bid = _bids(client, user_headers)[0]
    assert bid["status"] == "SUCCESS"

    # Once it resolves, it drops out of Bid History entirely (masking doesn't change that)...
    db = TestingSessionLocal()
    entry = db.query(SimulationEntry).order_by(SimulationEntry.id.desc()).first()
    entry.status = "Won"
    db.commit()
    db.close()
    assert _bids(client, user_headers) == []

    # ...and Win History still shows the real, unmasked "WON" status.
    wins = client.get("/api/v1/history/wins", headers=user_headers).json()["data"]["wins"]
    assert wins and wins[0]["status"] == "WON"


def test_history_gametype_is_the_display_name_not_the_code(client, auth_headers, user_headers):
    """Bid/Win History send the admin-editable display name (e.g. "Single"), not
    the internal code ("SINGLE") -- so renaming a game type in admin is reflected
    in the app without a client-side release."""
    mid = _matka_id(client, auth_headers)
    _bet(client, user_headers, marketId=str(mid), betType="SINGLE DIGIT", session="OPEN", items=[{"number": "5", "points": 10}])
    bid = _bids(client, user_headers)[0]
    assert bid["gameType"] == "Single"


def test_history_market_type_spellings(client, auth_headers, user_headers):
    _bet(client, user_headers, path="/api/v1/gali-desawar/bets", marketId="DISAWAR", betType="JODI DIGIT", numbers=[{"number": "45", "points": 10}])
    assert len(_bids(client, user_headers, market_type="GALI_DESAWAR")) == 1
    assert len(_bids(client, user_headers, market_type="GALI_DISAWAR")) == 1
    assert _bids(client, user_headers, market_type="REGULAR") == []
    assert len(_bids(client, user_headers, market_type="ALL")) == 1
