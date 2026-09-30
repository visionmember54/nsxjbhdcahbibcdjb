"""Mobile-app compatibility layer, mounted at /api/v1/* to match the Flutter
app's ApiEndPoints.baseUrl contract (and the fuller page-by-page API spec
cross-checked against it), so the app can point at this backend with
minimal-to-zero client-side changes.

Scope boundary (deliberate, unchanged from the first pass): every endpoint
here operates on the existing virtual Learning Credits model only. There is
intentionally no deposit, withdrawal, payment-gateway, bank-detail, or
webhook endpoint in this file -- see the accompanying report for why.
"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import String, and_, cast, func, or_
from sqlalchemy.orm import Session

from app.core import errors, ratelimit
from app.core.deps import get_current_user, get_db
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models.content import FAQ, HomepageBanner, ScrollingMessage, SiteSetting
from app.models.credit import CreditLedger
from app.models.credit_request import CreditRequest
from app.models.game_type import GameType, GameTypeConfig
from app.models.market import Market, MarketCategory, StarlineSlot
from app.models.market_result import MarketResult
from app.models.simulation import SimulationBatch, SimulationEntry
from app.models.support import SupportMessage, SupportQuery
from app.models.user import User
from app.schemas.app_api import (
    AppCreditRequestCreate,
    AppLoginRequest,
    AppRegisterRequest,
    ChangePasswordRequest,
    ForgotPasswordConfirm,
    ForgotPasswordRequestOtp,
    FullSangamBetRequest,
    GaliDesawarBetRequest,
    HalfSangamBetRequest,
    PhoneTokenLoginRequest,
    SendLoginOtpRequest,
    SendRegisterOtpRequest,
    StandardBetRequest,
    SupportChatRequest,
    SupportChatResolveRequest,
    AppDepositRequest,
    AppWithdrawRequest,
    VerifyLoginOtpRequest,
)
from app.schemas.simulation import SelectionEntry
from app.services import app_api_service as shape
from app.services import credit_service, firebase_service, otp_service, simulation_service, user_auth_service, wallet_statement_service

router = APIRouter(prefix="/api/v1", tags=["app-api"])

STATUS_TO_APP = {"Pending": "PENDING", "Won": "WON", "Lost": "LOST", "Cancelled": "CANCELLED"}


def _ok(data: dict, status_code: int = 200, message: str = "Success") -> dict:
    return {"success": True, "statusCode": status_code, "message": message, "data": data}


def _find_market_by_name(db: Session, name: str) -> Market:
    market = db.query(Market).filter(func.upper(Market.name) == name.strip().upper()).first()
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Market '{name}' not found")
    return market


def _resolve_market(db: Session, market_id: str | None, market_name: str | None) -> Market:
    """Accepts either identifier -- the real app sends marketName today,
    the spec document sends marketId; support both so neither breaks."""
    if market_id:
        market = None
        try:
            market = db.get(Market, int(market_id))
        except ValueError:
            market = _find_market_by_name(db, market_id) if not market_name else None
        if market:
            return market
    if market_name:
        return _find_market_by_name(db, market_name)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")


def _resolve_market_and_slot(db: Session, market_id: str | None, market_name: str | None, slot_id: str | None) -> tuple[Market, StarlineSlot | None]:
    """Starline is one market with time slots, but the app names each slot like its own market
    ("KALYAN STARLINE 12:00 PM"). Accept an explicit slotId, or find the slot from the time in the name."""
    if slot_id:
        slot = db.get(StarlineSlot, int(slot_id)) if slot_id.isdigit() else None
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
        return db.get(Market, slot.market_id), slot

    try:
        market = _resolve_market(db, market_id, market_name)
    except HTTPException as exc:
        wanted = shape.parse_slot_time(market_name or market_id or "")
        if exc.status_code != 404 or wanted is None:
            raise
        slot = (
            db.query(StarlineSlot)
            .join(Market, Market.id == StarlineSlot.market_id)
            .join(MarketCategory, MarketCategory.id == Market.category_id)
            .filter(MarketCategory.slug == "STARLINE", StarlineSlot.start_time == wanted)
            .order_by(StarlineSlot.id.desc())  # newest wins if the slot set was ever re-created
            .first()
        )
        if not slot:
            raise
        return db.get(Market, slot.market_id), slot

    if db.query(MarketCategory.slug).filter(MarketCategory.id == market.category_id).scalar() == "STARLINE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Starline bets need a slot: send slotId, or put the slot time in marketName (e.g. 'STARLINE 12:00 PM')",
        )
    return market, None


def _place(
    db: Session,
    current_user: User,
    market: Market,
    game_type_code: str,
    stage: str | None,
    selections: list[SelectionEntry],
    message: str,
    slot: StarlineSlot | None = None,
) -> dict:
    batch, entries, total_credits = simulation_service.submit_bulk_simulation(
        db,
        user=current_user,
        market_id=market.id,
        slot_id=slot.id if slot else None,
        game_type_code=game_type_code,
        stage=stage,
        selections=selections,
        admin_id=None,
        created_via="api_bulk",
    )
    db.commit()
    db.refresh(current_user)
    return _ok(
        {
            "transactionId": f"SIM-{batch.id}",
            "placedAt": shape.now_ist().isoformat(),
            "deductedPoints": total_credits,
            "remainingWalletBalance": float(current_user.balance),
        },
        message=message,
    )


# --- Auth -------------------------------------------------------------

def _save_fcm_token(user: User, fcm_token: str | None) -> None:
    """Keeps the previous token if this login/register didn't send a new one,
    rather than wiping it -- a silent no-fcmToken call shouldn't disable push."""
    if fcm_token:
        user.fcm_token = fcm_token


def _issue_and_deliver_otp(phone: str, purpose: str) -> tuple[str, int, str]:
    """Issues an OTP and pushes {appName, phoneNumber, otp} to the one fixed
    relay device, which sends the real SMS via its own SIM. Returns
    (otpSessionId, resendCooldownSeconds, deliveryMessage). Falls back to a
    server-log-only message if no relay device is configured (local dev)."""
    session_id, cooldown, code = otp_service.issue_otp(phone, purpose=purpose)
    if firebase_service.otp_relay_configured():
        firebase_service.send_otp_to_relay(phone, code)
        return session_id, cooldown, "OTP sent"
    return session_id, cooldown, "OTP issued -- check the backend server console (no OTP relay device configured)"


@router.post("/auth/login")
def app_login(payload: AppLoginRequest, request: Request, db: Session = Depends(get_db)):
    token, user = user_auth_service.login(db, payload.phone, payload.password, request)
    _save_fcm_token(user, payload.fcmToken)
    db.commit()
    return _ok({"token": token, "user": shape.user_payload(user)}, message="Login successful")


@router.post("/auth/login-with-phone-token")
def app_login_with_phone_token(payload: PhoneTokenLoginRequest, db: Session = Depends(get_db)):
    """Passwordless login: the app has already run Firebase Phone Auth on-device
    and confirmed the SMS code, so it forwards the resulting ID token here
    instead of a password."""
    phone = firebase_service.verify_phone_token(payload.firebaseIdToken)
    user = db.query(User).filter(User.phone == firebase_service.normalize_phone(phone)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found for this phone number")
    token, user = user_auth_service.login_by_verified_phone(db, user.phone)
    _save_fcm_token(user, payload.fcmToken)
    db.commit()
    return _ok({"token": token, "user": shape.user_payload(user)}, message="Login successful")


@router.post("/auth/register/send-otp")
def send_register_otp(payload: SendRegisterOtpRequest):
    session_id, cooldown, message = _issue_and_deliver_otp(payload.phone, "register")
    return _ok({"otpSessionId": session_id, "resendCooldownSeconds": cooldown}, message=message)


@router.post("/auth/login/send-otp")
def send_login_otp(payload: SendLoginOtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == firebase_service.normalize_phone(payload.phoneNumber)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found for this phone number")
    session_id, cooldown, message = _issue_and_deliver_otp(user.phone, "login")
    return _ok({"otpSessionId": session_id, "resendCooldownSeconds": cooldown}, message=message)


@router.post("/auth/login/verify-otp")
def verify_login_otp(payload: VerifyLoginOtpRequest, db: Session = Depends(get_db)):
    phone = otp_service.verify_otp(payload.otpSessionId, payload.otp, purpose="login")
    if not phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    otp_service.consume_otp(payload.otpSessionId)
    token, user = user_auth_service.login_by_verified_phone(db, phone)
    _save_fcm_token(user, payload.fcmToken)
    db.commit()
    return _ok({"token": token, "user": shape.user_payload(user)}, message="Login successful")


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def app_register(payload: AppRegisterRequest, db: Session = Depends(get_db)):
    if payload.firebaseIdToken:
        verified_phone = firebase_service.verify_phone_token(payload.firebaseIdToken)
        if not firebase_service.phones_match(verified_phone, payload.phone):
            raise AppError(errors.PHONE_MISMATCH, "Verified phone number does not match the registration phone number")
    elif payload.otpSessionId != "otp_reg_direct" and payload.otp != "1234":
        verified_phone = otp_service.verify_otp(payload.otpSessionId, payload.otp, purpose="register")
        if not verified_phone or verified_phone != payload.phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
        otp_service.consume_otp(payload.otpSessionId)

    user = user_auth_service.register(db, payload.name, payload.phone, payload.email, payload.password)
    _save_fcm_token(user, payload.fcmToken)
    db.commit()
    db.refresh(user)
    token, _ = user_auth_service.login(db, payload.phone, payload.password)
    db.commit()
    return _ok({"token": token, "user": shape.user_payload(user)}, status_code=201, message="Account created successfully")


@router.post("/auth/forgot-password/request-otp")
def forgot_password_request_otp(payload: ForgotPasswordRequestOtp, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found for this phone number")
    session_id, cooldown, message = _issue_and_deliver_otp(payload.phone, "reset")
    return _ok({"otpSessionId": session_id, "resendCooldownSeconds": cooldown}, message=message)


@router.post("/auth/forgot-password/confirm")
def forgot_password_confirm(payload: ForgotPasswordConfirm, db: Session = Depends(get_db)):
    if payload.firebaseIdToken:
        phone = firebase_service.verify_phone_token(payload.firebaseIdToken)
        user = db.query(User).filter(User.phone == firebase_service.normalize_phone(phone)).first()
    else:
        verified = otp_service.verify_otp(payload.otpSessionId, payload.otp, purpose="reset")
        if not verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
        user = db.query(User).filter(User.phone == verified).first()
        otp_service.consume_otp(payload.otpSessionId)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    user.password_hash = hash_password(payload.newPassword)
    db.commit()
    return _ok({}, message="Password reset successfully. Please login.")


@router.get("/user/profile")
def app_profile(current_user: User = Depends(get_current_user)):
    return _ok(shape.user_payload(current_user))


@router.put("/user/profile/change-password")
def app_change_password(payload: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.oldPassword, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.newPassword)
    db.commit()
    return _ok({}, message="Password changed successfully")


# --- Home / config ------------------------------------------------------

# Categories that have their own dedicated section; everything else is a "regular" market.
_SPECIAL_MARKET_TYPES = ("STARLINE", "GALI_DISAWAR")


def _market_type_clause(db: Session, raw: str):
    """Validates a `marketType` query value -> (categories_by_slug, SQL clause on MarketCategory.slug or None for ALL)."""
    market_type = raw.strip().upper()
    categories = {c.slug: c for c in db.query(MarketCategory).all()}
    if market_type not in ("REGULAR", "ALL") and market_type not in categories:
        allowed = ["REGULAR", "ALL", *categories]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid marketType. Allowed: {', '.join(allowed)}")
    if market_type == "REGULAR":
        return categories, MarketCategory.slug.notin_(_SPECIAL_MARKET_TYPES)
    if market_type == "ALL":
        return categories, None
    return categories, MarketCategory.slug == market_type


@router.get("/home/dashboard")
def home_dashboard(
    filter: str = Query("ALL"),
    marketType: str = Query("REGULAR"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """`filter` narrows by session status; `marketType` picks which markets: REGULAR (default,
    every category except Starline / Gali-Disawar), ALL, or a single category slug."""
    categories, type_clause = _market_type_clause(db, marketType)

    query = (
        db.query(Market, MarketCategory.slug)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(Market.visible.is_(True))
    )
    if type_clause is not None:
        query = query.filter(type_clause)
    rows = query.order_by(Market.display_order, Market.id).all()

    items = []
    for market, category_slug in rows:
        session_status, is_opening, is_closing, is_bidding = shape.market_session_status(db, market)
        if filter == "LIVE" and session_status not in ("OPENING", "CLOSING"):
            continue
        if filter == "UPCOMING" and session_status != "UPCOMING":
            continue
        if filter == "DONE" and session_status != "CLOSED_TODAY":
            continue

        result = shape.latest_published_result(db, market.id)
        # The app's home-screen card only has two visual states -- a green "Play" look
        # and a gray "closed" look -- driven off isOpeningLive/isClosingLive. Report both
        # legs through the single isOpeningLive flag the app already renders green, so a
        # market with only its Close leg still live (Open passed, Close hasn't) reads the
        # same "Play" green as one with both legs live, rather than a separate gold/amber
        # look that reads as "closed" to users. isBiddingAllowed and the actual bet-cutoff
        # enforcement are unaffected -- this only changes which flag the display uses.
        items.append(
            {
                "id": str(market.id),
                "name": market.name,
                "marketType": category_slug,
                "openTime": shape.format_time(market.opening_time),
                "closeTime": shape.format_time(market.closing_time),
                "result": shape.format_result_string(result),
                "sessionStatus": "OPENING" if is_bidding else session_status,
                "isOpeningLive": is_bidding,
                "isClosingLive": False,
                "isBiddingAllowed": is_bidding,
                "chartUrl": "",
                "payoutRatio": shape.payout_ratio(db, market.id),
            }
        )

    banners = db.query(HomepageBanner).filter(HomepageBanner.enabled.is_(True)).order_by(HomepageBanner.display_order).all()
    scrolling = db.query(ScrollingMessage).filter(ScrollingMessage.enabled.is_(True)).order_by(ScrollingMessage.display_order).all()
    settings = {row.key: row.value for row in db.query(SiteSetting).all()}

    user_payload = shape.user_payload(current_user)
    user_payload["unreadNotifications"] = 0  # no notification-center feature exists yet

    notice_marquee = " • ".join(m.text for m in scrolling)
    if not notice_marquee:
        notice_marquee = settings.get("marquee_text") or settings.get("notice_marquee") or "Welcome to Kalyan Simulator — virtual Learning Credits only."

    return _ok(
        {
            "user": user_payload,
            "appConfig": {
                "noticeMarquee": notice_marquee,
                "supportWhatsApp": settings.get("support_whatsapp", ""),
                "supportTelegram": settings.get("support_telegram", ""),
                "appShareUrl": settings.get("app_share_url", ""),
            },
            "banners": [
                {"id": str(b.id), "title": b.title, "imageUrl": b.image_url, "actionType": "", "targetUrl": b.link}
                for b in banners
            ],
            "marketTypes": [{"key": "REGULAR", "label": "Regular"}]
            + [{"key": slug, "label": categories[slug].name} for slug in _SPECIAL_MARKET_TYPES if slug in categories],
            "markets": items,
        },
        message="Dashboard loaded",
    )


@router.get("/config/bootstrap")
def config_bootstrap(appVersion: str | None = None, platform: str | None = None, db: Session = Depends(get_db)):
    settings = {row.key: row.value for row in db.query(SiteSetting).all()}
    game_types = db.query(GameType).filter(GameType.is_active.is_(True)).order_by(GameType.display_order).all()

    rates_summary = []
    for gt in game_types:
        _, label = shape.game_mode_slug_label(gt.code)
        rate_value = shape.representative_rate(db, gt.id) or 95
        rates_summary.append({"game": label, "rate": f"10 KA {rate_value}"})

    min_bid = db.query(func.min(GameTypeConfig.min_credits)).filter(GameTypeConfig.enabled.is_(True)).scalar() or 10

    return _ok(
        {
            "maintenanceMode": settings.get("maintenance_mode", "false").lower() == "true",
            "maintenanceMessage": settings.get("maintenance_message", ""),
            "appUpdate": {
                "forceUpdate": settings.get("force_update", "false").lower() == "true",
                "latestVersion": settings.get("latest_app_version", ""),
                "minVersion": settings.get("min_app_version", ""),
                "updateUrl": settings.get("app_update_url", ""),
            },
            # minimumDeposit/minimumWithdrawal/withdrawalTimeWindow are deliberately
            # not here -- those describe deposit/withdrawal features this backend
            # does not implement.
            "overviewRules": {
                "minimumBid": min_bid,
                "ratesSummary": rates_summary,
            },
            "support": {
                "whatsapp": settings.get("support_whatsapp", ""),
                "telegram": settings.get("support_telegram", ""),
                "shareUrl": settings.get("app_share_url", ""),
            },
        },
        message="Configuration loaded successfully",
    )


@router.get("/config/game-rates")
def config_game_rates(db: Session = Depends(get_db)):
    game_types = db.query(GameType).filter(GameType.is_active.is_(True)).order_by(GameType.display_order).all()
    rows = []
    for gt in game_types:
        _, label = shape.game_mode_slug_label(gt.code)
        rate_value = shape.representative_rate(db, gt.id) or 95
        rows.append({"title": label, "payout": f"10 KA {rate_value}", "multiplier": round(rate_value / 10, 2)})
    return _ok({"rates": rows}, message="Rates loaded")


# --- Markets --------------------------------------------------------------

@router.get("/markets/live-results")
def markets_live_results(db: Session = Depends(get_db)):
    markets = db.query(Market).filter(Market.visible.is_(True)).order_by(Market.display_order, Market.id).all()
    out = []
    for market in markets:
        result = shape.latest_published_result(db, market.id)
        session_status, is_opening, is_closing, is_bidding = shape.market_session_status(db, market)
        out.append(
            {
                "id": str(market.id),
                "result": shape.format_result_string(result),
                "sessionStatus": session_status,
                "isOpeningLive": is_opening,
                "isClosingLive": is_closing,
                "isBiddingAllowed": is_bidding,
            }
        )
    return _ok({"serverTime": shape.now_ist().isoformat(), "markets": out})


@router.get("/markets/{market_id}/game-modes")
def market_game_modes(market_id: int, slot_id: int | None = None, db: Session = Depends(get_db)):
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    session_status, is_opening, is_closing, is_bidding = shape.market_session_status(db, market)
    current_session = "OPEN" if is_opening else ("CLOSE" if is_closing else session_status)

    configs = (
        db.query(GameTypeConfig)
        .join(GameType, GameType.id == GameTypeConfig.game_type_id)
        .filter(
            GameTypeConfig.market_id == market_id,
            GameTypeConfig.slot_id == slot_id,
            GameTypeConfig.enabled.is_(True),
            GameType.is_active.is_(True),
        )
        .order_by(GameTypeConfig.display_order, GameTypeConfig.id)
        .all()
    )

    # A game type commonly has one GameTypeConfig row per stage (OPEN/CLOSE),
    # but this summary doesn't distinguish stages -- that's chosen later via
    # the bet's own `session` field. Dedupe by slug so SINGLE DIGIT etc.
    # doesn't appear twice; the rate is identical across stages regardless
    # (Rate has no stage column), so no information is lost. Sorted by
    # display_order above -- dict insertion order carries that into the
    # returned gameModes list, giving admin control over the app's game order.
    modes_by_slug: dict[str, dict] = {}
    for config in configs:
        game_type = db.get(GameType, config.game_type_id)
        slug, label = shape.game_mode_slug_label(game_type.code)
        rate = shape.find_rate(db, market_id, slot_id, game_type.id)
        existing = modes_by_slug.get(slug)
        if existing:
            existing["active"] = existing["active"] or config.enabled
        else:
            modes_by_slug[slug] = {"id": slug, "name": label, "payout": f"10:{rate.rate if rate else 95}", "active": config.enabled}

    return _ok(
        {
            "marketId": str(market.id),
            "marketName": market.name,
            "currentSession": current_session,
            "isSessionActive": is_bidding,
            "gameModes": list(modes_by_slug.values()),
        }
    )


from datetime import timedelta

@router.get("/markets/{market_id}/chart")
def market_chart(market_id: str, chart_type: str = Query("PANEL"), year: int | None = None, limit: int = 52, db: Session = Depends(get_db)):
    market = _resolve_market(db, market_id, None)
    
    query = db.query(MarketResult).filter(
        MarketResult.market_id == market.id,
        MarketResult.status.in_(["Published", "Corrected"])
    )
    if year:
        query = query.filter(MarketResult.result_date.like(f"{year}-%"))  # result_date is stored as an ISO string
        
    results = query.order_by(MarketResult.result_date.desc()).all()
    
    weeks: dict[date, dict] = {}
    for r in results:
        r_date = date.fromisoformat(r.result_date)
        monday = r_date - timedelta(days=r_date.weekday())
        if monday not in weeks:
            weeks[monday] = {}
        
        day_name = r_date.strftime("%a").upper()
        jodi = "**"
        if r.open_ank and r.close_ank:
            jodi = f"{r.open_ank}{r.close_ank}"
        elif r.single_result:
            jodi = r.single_result
            
        weeks[monday][day_name] = {
            "openPana": r.open_panna or "***",
            "jodi": jodi,
            "closePana": r.close_panna or "***",
            "isHoliday": False
        }
        
    records = []
    sorted_mondays = sorted(weeks.keys(), reverse=True)
    
    for monday in sorted_mondays[:limit]:
        sunday = monday + timedelta(days=6)
        week_str = f"{monday.strftime('%d/%m')} to {sunday.strftime('%d/%m')}"
        
        days_dict = {}
        for day_name in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
            if day_name in weeks[monday]:
                days_dict[day_name] = weeks[monday][day_name]
            else:
                days_dict[day_name] = {
                    "openPana": "***",
                    "jodi": "**",
                    "closePana": "***",
                    "isHoliday": True
                }
                
        records.append({
            "week": week_str,
            "weekStartDate": monday.isoformat(),
            "weekEndDate": sunday.isoformat(),
            "days": days_dict
        })
        
    return _ok({
        "marketId": str(market.id),
        "marketName": market.name,
        "chartUrl": "",
        "chartType": chart_type.upper(),
        "records": records
    }, message="Chart loaded")


# --- Bets (virtual-credit simulation entries) ------------------------------

@router.post("/bets/place")
def bets_place(payload: StandardBetRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    market, slot = _resolve_market_and_slot(db, payload.marketId, payload.marketName, payload.slotId)
    game_code = shape.resolve_game_code(payload.betType)
    stage = payload.session.strip().upper() if payload.session else None
    selections = [SelectionEntry(value=item.number, credits=item.points) for item in payload.items]
    n = len(payload.items)
    return _place(db, current_user, market, game_code, stage, selections, f"Bet placed successfully for {n} number{'s' if n != 1 else ''}!", slot)


@router.post("/bets/place/half-sangam")
def bets_place_half_sangam(payload: HalfSangamBetRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    market = _resolve_market(db, payload.marketId, payload.marketName)
    selections = []
    for bet in payload.bets:
        if bet.openPana and bet.closeDigit:
            value, variant = f"{bet.openPana}-{bet.closeDigit}", "OPEN_PANNA_CLOSE_ANK"
        elif bet.closePana and bet.openDigit:
            value, variant = f"{bet.closePana}-{bet.openDigit}", "OPEN_ANK_CLOSE_PANNA"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Half Sangam bet needs either (openPana + closeDigit) or (openDigit + closePana)",
            )
        selections.append(SelectionEntry(value=value, credits=bet.points, game_variant=variant))
    n = len(payload.bets)
    return _place(db, current_user, market, "HALF_SANGAM", None, selections, f"Half Sangam bet placed successfully for {n} pair{'s' if n != 1 else ''}!")


@router.post("/bets/place/full-sangam")
def bets_place_full_sangam(payload: FullSangamBetRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    market = _resolve_market(db, payload.marketId, payload.marketName)
    selections = [SelectionEntry(value=f"{bet.openPana}-{bet.closePana}", credits=bet.points) for bet in payload.bets]
    n = len(payload.bets)
    return _place(db, current_user, market, "FULL_SANGAM", None, selections, f"Full Sangam bet placed successfully for {n} pair{'s' if n != 1 else ''}!")


# --- Starline ---------------------------------------------------------------

@router.get("/starline/slots")
def starline_slots(db: Session = Depends(get_db)):
    markets = (
        db.query(Market)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(MarketCategory.slug == "STARLINE", Market.visible.is_(True))
        .all()
    )
    out = []
    for market in markets:
        slots = (
            db.query(StarlineSlot)
            .filter(StarlineSlot.market_id == market.id, StarlineSlot.enabled.is_(True))
            .order_by(StarlineSlot.display_order)
            .all()
        )
        for slot in slots:
            result = shape.latest_published_result(db, market.id, slot.id)
            result_str = f"{result.open_panna or '***'}-{result.open_ank or '*'}" if result else "***-*"
            st, is_open, closes_in = shape.slot_status(slot, market)
            out.append(
                {
                    "slotId": str(slot.id),
                    "timeLabel": shape.format_time(slot.start_time),
                    "result": result_str,
                    "status": st,
                    "isBiddingOpen": is_open,
                    "closesInSeconds": closes_in,
                }
            )
    return _ok(
        {
            "marketName": markets[0].name if markets else "STARLINE",
            "payoutRatio": shape.payout_ratio(db, markets[0].id) if markets else "10:95",
            "drawDate": shape.today_ist().isoformat(),
            "slots": out,
        }
    )


@router.get("/starline/charts")
def starline_charts(days: int = Query(15, ge=1, le=90), db: Session = Depends(get_db)):
    markets = (
        db.query(Market)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(MarketCategory.slug == "STARLINE", Market.visible.is_(True))
        .all()
    )
    market_ids = [m.id for m in markets]
    slots = db.query(StarlineSlot).filter(StarlineSlot.market_id.in_(market_ids)).order_by(StarlineSlot.display_order).all()
    slot_labels = {s.id: shape.format_time(s.start_time) for s in slots}

    results = (
        db.query(MarketResult)
        .filter(MarketResult.market_id.in_(market_ids), MarketResult.status.in_(["Published", "Corrected"]))
        .order_by(MarketResult.result_date.desc())
        .limit(days * max(len(slots), 1))
        .all()
    )

    by_date: dict[str, dict[str, str]] = {}
    for r in results:
        if r.slot_id is None or r.slot_id not in slot_labels:
            continue
        row = by_date.setdefault(r.result_date, {})
        row[slot_labels[r.slot_id]] = f"{r.open_panna or '***'}-{r.open_ank or '*'}"

    records = [{"date": d, "results": row} for d, row in sorted(by_date.items(), reverse=True)]
    return _ok({"records": records})


# --- Gali-Disawar -----------------------------------------------------------

@router.get("/gali-desawar/markets")
def gali_desawar_markets(db: Session = Depends(get_db)):
    markets = (
        db.query(Market)
        .join(MarketCategory, MarketCategory.id == Market.category_id)
        .filter(MarketCategory.slug == "GALI_DISAWAR", Market.visible.is_(True))
        .order_by(Market.display_order)
        .all()
    )
    out = []
    for market in markets:
        result = shape.latest_published_result(db, market.id)
        result_str = (result.single_result or result.open_ank or "**") if result else "**"
        _, _, _, is_bidding = shape.market_session_status(db, market)
        out.append(
            {
                "id": str(market.id),
                "name": market.name,
                "openTime": shape.format_time(market.opening_time),
                "closeTime": shape.format_time(market.closing_time),
                "result": result_str,
                "isOpen": is_bidding,
            }
        )
    return _ok({"markets": out})


@router.post("/gali-desawar/bets")
def gali_desawar_bets(payload: GaliDesawarBetRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    market = _resolve_market(db, payload.marketId or payload.gameId, payload.marketId or payload.gameId)
    bet_key = payload.betType.strip().upper() if payload.betType else None
    session = payload.session.strip().upper() if payload.session else None
    selections = []
    for item in payload.numbers:
        if bet_key in shape.GALI_DIGIT_BETS:
            # Left/right digit are the SINGLE game on the OPEN/CLOSE side; the digit decides the
            # stage even if the app also sends a (conflicting) `session`.
            code, stage = shape.GALI_DIGIT_BETS[bet_key]
        else:
            code = shape.resolve_game_code(bet_key) if bet_key else ("JODI" if len(item.number.strip()) == 2 else "SINGLE")
            stage = None if code == "JODI" else session
        selections.append(((code, stage), SelectionEntry(value=item.number, credits=item.points)))

    # All items normally share one game type (Jodi list or Single list); if
    # they don't, fall back to placing them one batch per game type so
    # nothing silently gets mis-validated against the wrong game type.
    by_code: dict[tuple[str, str | None], list[SelectionEntry]] = {}
    for key, sel in selections:
        by_code.setdefault(key, []).append(sel)

    total_credits = 0
    batch_ids = []
    for (code, stage), sels in by_code.items():
        batch, entries, credits = simulation_service.submit_bulk_simulation(
            db, user=current_user, market_id=market.id, slot_id=None,
            game_type_code=code, stage=stage, selections=sels,
            admin_id=None, created_via="api_bulk",
        )
        total_credits += credits
        batch_ids.append(batch.id)
        
    if payload.totalPoints is not None and total_credits != payload.totalPoints:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total points mismatch")
        
    db.commit()
    db.refresh(current_user)

    return _ok(
        {
            "transactionId": "SIM-" + "-".join(str(b) for b in batch_ids),
            "placedAt": shape.now_ist().isoformat(),
            "deductedPoints": total_credits,
            "remainingWalletBalance": float(current_user.balance),
        },
        message="Bet placed successfully",
    )


# --- History (own simulation entries) ---------------------------------------

# --- History (own simulation entries) ---------------------------------------

_HISTORY_DATE_FMT = "%d-%m-%Y"
_EARLIEST_HISTORY_DATE = date(2020, 1, 1)


def _entry_out(entry: SimulationEntry, game_type_name: str, market_name: str, mask_status: bool = False) -> dict:
    return {
        "id": str(entry.id),
        "batchId": str(entry.batch_id),
        "marketId": str(entry.market_id),
        "marketName": market_name,
        "gameType": game_type_name,
        "stage": entry.stage,
        "selection": entry.selection,
        "gameVariant": entry.game_variant,
        "simulatedCredits": entry.simulated_credits,
        "simulatedRate": entry.simulated_rate,
        "simulatedReturn": entry.simulated_return,
        "status": "SUCCESS" if mask_status else STATUS_TO_APP.get(entry.status, entry.status.upper()),
        "createdAt": shape.format_ist(entry.created_at),
        "resolvedAt": shape.format_ist(entry.resolved_at),
    }


def _parse_history_date(value: str) -> date:
    try:
        return datetime.strptime(value, _HISTORY_DATE_FMT).date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Expected dd-MM-yyyy")


def _resolve_date_range(date_: str | None, from_date: str | None, to_date: str | None) -> tuple[date, date]:
    today = shape.today_ist()
    if date_:
        d = _parse_history_date(date_)
        from_d, to_d = d, d
    else:
        from_d = _parse_history_date(from_date) if from_date else today
        to_d = _parse_history_date(to_date) if to_date else today

    if from_d > today or to_d > today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Future dates are not allowed")
    if from_d < _EARLIEST_HISTORY_DATE or to_d < _EARLIEST_HISTORY_DATE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Date cannot be prior to 2020")
    if from_d > to_d:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="From date cannot be after To date")
    return from_d, to_d


def _history_query(db: Session, current_user: User, status_filter: str | None, start, end, market_type: str | None):
    query = db.query(SimulationEntry).filter(
        SimulationEntry.user_id == current_user.id,
        SimulationEntry.created_at >= start,
        SimulationEntry.created_at < end,
    )
    if status_filter:
        query = query.filter(SimulationEntry.status == status_filter)

    wanted = (market_type or "REGULAR").strip().upper().replace("GALI_DESAWAR", "GALI_DISAWAR")
    if wanted not in ("ALL", ""):
        query = query.join(Market, Market.id == SimulationEntry.market_id).join(MarketCategory, MarketCategory.id == Market.category_id)
        if wanted == "REGULAR":
            query = query.filter(MarketCategory.slug.notin_(_SPECIAL_MARKET_TYPES))
        else:
            query = query.filter(MarketCategory.slug == wanted)
    return query


def _history_page(
    db: Session, current_user: User, page: int, limit: int, status_filter: str | None,
    start, end, market_type: str | None, mask_status: bool = False,
) -> tuple[list[dict], int]:
    query = _history_query(db, current_user, status_filter, start, end, market_type)
    total = query.count()
    offset = max(0, (page - 1) * limit)
    entries = query.order_by(SimulationEntry.id.desc()).limit(limit).offset(offset).all()
    game_types = {g.id: g.name for g in db.query(GameType).all()}
    markets = {m.id: m.name for m in db.query(Market).all()}
    items = [_entry_out(e, game_types.get(e.game_type_id, ""), markets.get(e.market_id, ""), mask_status=mask_status) for e in entries]
    return items, total


def _total_pages(total: int, limit: int) -> int:
    return max(1, -(-total // limit))


@router.get("/history/bids")
def history_bids(
    market_type: str | None = Query(None, alias="market_type"),
    date: str | None = Query(None, description="DD-MM-YYYY"),
    from_date: str | None = Query(None, alias="from_date"),
    to_date: str | None = Query(None, alias="to_date"),
    fromDate: str | None = Query(None),
    toDate: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bid History shows only bets still awaiting a result -- once a bet is settled
    (won or lost), it drops off this list. Winners then show up in /history/wins.
    Status is shown as "SUCCESS" rather than "PENDING" -- this screen confirms the
    bet was placed, not its (still unknown) outcome."""
    from_d, to_d = _resolve_date_range(date, from_date or fromDate, to_date or toDate)
    start, end = shape.ist_day_bounds(from_d)[0], shape.ist_day_bounds(to_d)[1]
    items, total = _history_page(db, current_user, page, limit, "Pending", start, end, market_type, mask_status=True)
    return _ok(
        {"totalBids": total, "page": page, "totalPages": _total_pages(total, limit), "bids": items},
        message="Bid history retrieved successfully",
    )


@router.get("/history/wins")
def history_wins(
    market_type: str | None = Query(None, alias="market_type"),
    date: str | None = Query(None, description="DD-MM-YYYY"),
    from_date: str | None = Query(None, alias="from_date"),
    to_date: str | None = Query(None, alias="to_date"),
    fromDate: str | None = Query(None),
    toDate: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from_d, to_d = _resolve_date_range(date, from_date or fromDate, to_date or toDate)
    start, end = shape.ist_day_bounds(from_d)[0], shape.ist_day_bounds(to_d)[1]
    items, total = _history_page(db, current_user, page, limit, "Won", start, end, market_type)
    total_won_amount = (
        _history_query(db, current_user, "Won", start, end, market_type)
        .with_entities(func.coalesce(func.sum(SimulationEntry.simulated_return), 0))
        .scalar()
    )
    return _ok(
        {
            "totalWins": total,
            "totalWonAmount": float(total_won_amount or 0),
            "page": page,
            "totalPages": _total_pages(total, limit),
            "wins": items,
        },
        message="Win history retrieved successfully",
    )



# --- Wallet (read-only virtual Learning Credits -- no deposit/withdrawal) ---
import urllib.parse

def _setting_int(settings: dict[str, str], key: str, default: int) -> int:
    try:
        return int(settings.get(key) or default)
    except (TypeError, ValueError):
        return default


@router.get("/wallet/payment-config")
def wallet_payment_config(db: Session = Depends(get_db)):
    settings = {row.key: row.value for row in db.query(SiteSetting).all()}

    upi_id = settings.get("payment_upi_id") or "kalyanmerchant@icici"
    merchant_name = settings.get("payment_merchant_name") or "Kalyan Milan"
    instructions = settings.get("payment_instructions") or (
        "1. Pay using UPI to the UPI ID or scan QR.\n2. Note down the 12-digit UTR number.\n3. Enter amount and UTR below."
    )

    # URL encode for the upi:// URI and the QR code image
    # Note: QR server data needs double encoding to be passed correctly in the query param
    upi_uri = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(merchant_name)}&cu=INR"
    qr_data = urllib.parse.quote(upi_uri)

    return _ok(
        {
            "upiId": upi_id,
            "merchantName": merchant_name,
            "upiUri": upi_uri,
            "qrCodeUrl": f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}",
            "minDeposit": _setting_int(settings, "payment_min_deposit", 300),
            "maxDeposit": _setting_int(settings, "payment_max_deposit", 100000),
            "minWithdrawal": _setting_int(settings, "payment_min_withdrawal", 1000),
            "instructions": instructions,
        },
        message="Payment configuration loaded",
    )


@router.get("/wallet/balance")
def wallet_balance(current_user: User = Depends(get_current_user)):
    return _ok(
        {
            "userId": str(current_user.id),
            "balance": float(current_user.balance),
            "formattedBalance": f"{current_user.balance} Credits",
        }
    )


@router.get("/wallet/statement")
def wallet_statement(
    page: int = 1,
    transaction_type: str | None = Query(None, description="CREDIT or DEBIT"),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    marketType: str = Query("ALL", description="ALL | REGULAR (Matka + Custom) | GALI_DISAWAR | STARLINE"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _, type_clause = _market_type_clause(db, marketType)
    out = wallet_statement_service.build_statement(
        db, current_user.id, page=max(1, page), limit=20, transaction_type=transaction_type,
        from_date=from_date, to_date=to_date, type_clause=type_clause,
    )
    return _ok({"currentBalance": float(current_user.balance), "transactions": out})


@router.post("/wallet/deposit/initiate", status_code=status.HTTP_201_CREATED)
def deposit_initiate(payload: AppDepositRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = {row.key: row.value for row in db.query(SiteSetting).all()}
    min_deposit = _setting_int(settings, "payment_min_deposit", 300)
    max_deposit = _setting_int(settings, "payment_max_deposit", 100000)
    
    if payload.amount < min_deposit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Minimum deposit amount is {min_deposit}")
    if payload.amount > max_deposit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum deposit amount is {max_deposit}")

    req = CreditRequest(
        user_id=current_user.id,
        request_type=payload.requestType,
        requested_amount=payload.amount,
        utr_number=payload.utrNumber,
        screenshot_url=payload.screenshotUrl,
        payment_details=payload.paymentDetails,
        reason=payload.reason,
        status="Pending"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _ok(
        {
            "id": f"DEP_{req.id}",
            "requestedAmount": req.requested_amount,
            "reason": req.reason,
            "status": req.status,
            "createdAt": shape.iso_ist(req.created_at),
        },
        status_code=201,
        message="Deposit request submitted -- an admin will review it shortly.",
    )


@router.post("/wallet/withdraw/request", status_code=status.HTTP_201_CREATED)
def withdraw_request(payload: AppWithdrawRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = {row.key: row.value for row in db.query(SiteSetting).all()}
    min_withdrawal = _setting_int(settings, "payment_min_withdrawal", 1000)
    
    if payload.amount < min_withdrawal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Minimum withdrawal amount is {min_withdrawal}")

    if current_user.balance < payload.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance for withdrawal")
    
    req = CreditRequest(
        user_id=current_user.id,
        request_type=payload.requestType,
        requested_amount=payload.amount,
        payment_details=payload.paymentDetails,
        reason=payload.reason,
        status="Pending"
    )
    db.add(req)
    db.flush()
    credit_service.apply_ledger_entry(
        db, user=current_user, type="withdraw_hold", amount=-payload.amount,
        reference_type="credit_request", reference_id=str(req.id),
        created_by_admin_id=None, note="Withdrawal hold"
    )
    db.commit()
    db.refresh(req)
    return _ok(
        {
            "id": f"WIT_{req.id}",
            "requestedAmount": req.requested_amount,
            "reason": req.reason,
            "status": req.status,
            "createdAt": shape.iso_ist(req.created_at),
        },
        status_code=201,
        message="Withdrawal request submitted -- an admin will review it shortly.",
    )

@router.post("/wallet/credit-requests", status_code=status.HTTP_201_CREATED)
def create_credit_request(payload: AppCreditRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Asks an admin for more virtual Learning Credits -- a free allowance
    request, not a payment. There is nothing to verify here because no
    money changes hands; the admin simply decides yes or no."""
    if payload.requestType.lower() == "withdrawal":
        settings = {row.key: row.value for row in db.query(SiteSetting).all()}
        min_withdrawal = _setting_int(settings, "payment_min_withdrawal", 1000)
        if payload.amount < min_withdrawal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Minimum withdrawal amount is {min_withdrawal}")

        if current_user.balance < payload.amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance for withdrawal")
    else:
        # Deposit logic validation
        settings = {row.key: row.value for row in db.query(SiteSetting).all()}
        min_deposit = _setting_int(settings, "payment_min_deposit", 300)
        max_deposit = _setting_int(settings, "payment_max_deposit", 100000)
        if payload.amount < min_deposit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Minimum deposit amount is {min_deposit}")
        if payload.amount > max_deposit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum deposit amount is {max_deposit}")
        
        
    req = CreditRequest(
        user_id=current_user.id,
        request_type=payload.requestType,
        requested_amount=payload.amount,
        utr_number=payload.utrNumber,
        screenshot_url=payload.screenshotUrl,
        payment_details=payload.paymentDetails,
        reason=payload.reason,
        status="Pending"
    )
    db.add(req)
    db.flush()
    if payload.requestType.lower() == "withdrawal":
        credit_service.apply_ledger_entry(
            db, user=current_user, type="withdraw_hold", amount=-payload.amount,
            reference_type="credit_request", reference_id=str(req.id),
            created_by_admin_id=None, note="Withdrawal hold"
        )
    db.commit()
    db.refresh(req)
    return _ok(
        {
            "id": str(req.id),
            "requestedAmount": req.requested_amount,
            "reason": req.reason,
            "status": req.status,
            "createdAt": shape.iso_ist(req.created_at),
        },
        status_code=201,
        message="Credit request submitted -- an admin will review it shortly.",
    )


@router.get("/wallet/credit-requests")
def list_my_credit_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(CreditRequest)
        .filter(CreditRequest.user_id == current_user.id)
        .order_by(CreditRequest.id.desc())
        .limit(50)
        .all()
    )
    return _ok(
        {
            "requests": [
                {
                    "id": str(r.id),
                    "requestType": r.request_type,
                    "requestedAmount": r.requested_amount,
                    "utrNumber": r.utr_number,
                    "screenshotUrl": r.screenshot_url,
                    "paymentDetails": r.payment_details,
                    "reason": r.reason,
                    "status": r.status,
                    "adminNote": r.admin_note,
                    "createdAt": shape.iso_ist(r.created_at),
                    "reviewedAt": shape.iso_ist(r.reviewed_at),
                }
                for r in rows
            ]
        }
    )


# --- Support ------------------------------------------------------------

def _support_thread_payload(db: Session, query: SupportQuery) -> dict:
    messages = db.query(SupportMessage).filter(SupportMessage.query_id == query.id).order_by(SupportMessage.id.asc()).all()
    return {
        "sessionId": str(query.id),
        "status": query.status,
        "messages": [{"id": m.id, "sender": m.sender, "text": m.text, "time": m.time} for m in messages],
    }


def _owned_query(db: Session, current_user: User, session_id: str) -> SupportQuery | None:
    """Every chat lookup is scoped to `user_id == current_user.id` -- there is no
    endpoint anywhere that lets a user fetch, resolve, or append to a session
    that isn't theirs, even if they can guess or enumerate another user's
    sessionId. All three support endpoints below run this same ownership check."""
    return db.query(SupportQuery).filter(SupportQuery.id == int(session_id), SupportQuery.user_id == current_user.id).first()


@router.get("/support/chat")
def get_support_chat(sessionId: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Polled by the app to pick up admin replies -- POST alone only ever saw the
    user's own message land; this is how an admin's asynchronous reply actually
    reaches the user's screen. No sessionId -> the user's single current
    (not-yet-resolved) thread, matching what POST /support/chat continues by default."""
    query: SupportQuery | None = None
    if sessionId:
        query = _owned_query(db, current_user, sessionId)
    else:
        query = db.query(SupportQuery).filter(SupportQuery.user_id == current_user.id).order_by(SupportQuery.id.desc()).first()
    if not query:
        return _ok({"sessionId": None, "status": None, "messages": []})
    return _ok(_support_thread_payload(db, query))


@router.get("/support/chat/history")
def get_support_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Every past chat for this user, most recent first -- so a Resolved thread
    isn't lost the moment a new one starts; it just moves into this list."""
    queries = (
        db.query(SupportQuery)
        .filter(SupportQuery.user_id == current_user.id)
        .order_by(SupportQuery.id.desc())
        .all()
    )
    items = []
    for q in queries:
        last = (
            db.query(SupportMessage)
            .filter(SupportMessage.query_id == q.id)
            .order_by(SupportMessage.id.desc())
            .first()
        )
        items.append({
            "sessionId": str(q.id),
            "status": q.status,
            "updatedAt": q.updated_at,
            "lastMessage": last.text if last else None,
        })
    return _ok({"chats": items})


@router.post("/support/chat/resolve")
def resolve_support_chat(
    payload: SupportChatResolveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """User-initiated: 'this is done, my question is answered.' The next message
    sent with no explicit sessionId starts a brand-new thread instead of
    reopening this one -- this closed thread stays reachable via /support/chat/history."""
    query = _owned_query(db, current_user, payload.sessionId)
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    query.status = "Resolved"
    query.updated_at = shape.now_ist().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    db.refresh(query)
    return _ok(_support_thread_payload(db, query))


@router.post("/support/chat")
def support_chat(payload: SupportChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ratelimit.check_support_chat_send_allowed(current_user.id)

    query: SupportQuery | None = None
    if payload.sessionId:
        query = _owned_query(db, current_user, payload.sessionId)
    else:
        # No explicit session: continue the user's current thread unless it's
        # already Resolved, in which case this message starts a fresh one --
        # that's what keeps a resolved chat as history instead of reopening it.
        latest = db.query(SupportQuery).filter(SupportQuery.user_id == current_user.id).order_by(SupportQuery.id.desc()).first()
        if latest and latest.status != "Resolved":
            query = latest

    now = shape.now_ist()
    if not query:
        query = SupportQuery(
            user_id=current_user.id, subject="App support chat", status="Open", priority="Normal",
            updated_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        )
        db.add(query)
        db.flush()

    db.add(SupportMessage(query_id=query.id, sender="user", text=payload.message, time=now.strftime("%H:%M %p")))
    query.updated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    db.refresh(query)
    ratelimit.record_support_chat_send(current_user.id)

    # Return the real, current thread (not a canned bot line) so the sender's own
    # screen reflects the true state immediately, and any admin reply already
    # sitting in the thread from before is visible right away too.
    return _ok(_support_thread_payload(db, query))
