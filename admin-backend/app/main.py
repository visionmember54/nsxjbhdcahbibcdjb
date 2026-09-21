from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
request_logger = logging.getLogger("app.requests")
from app.routers.admin import admins, audit_logs, auth, content, credit_requests, credits, dashboard, game_type_configs, game_types, market_categories, markets, rates, reports, results, roles, simulations, starline, support, users
from app.routers.public import content as public_content
from app.routers.public import gali_disawar as public_gali_disawar
from app.routers.public import game_types as public_game_types
from app.routers.public import markets as public_markets
from app.routers.public import results as public_results
from app.routers.public import simulations as public_simulations
from app.routers.public import starline as public_starline
from app.routers.public import user_auth
from app.routers.public import app_api

settings = get_settings()

TAGS_METADATA = [
    {"name": "dashboard", "description": "Aggregate stats for the admin Overview page."},
    {"name": "reports", "description": "Simulation/game statistics, number frequency -- computed live, never stored."},
    {"name": "admin-auth", "description": "Admin login and session identity. Login is rate-limited to deter brute force."},
    {"name": "admins", "description": "Admin-account management (super_admin only): list, create, enable/disable, change role."},
    {"name": "roles", "description": "Data-driven roles and permissions: list/create roles, view the permission catalog, set a role's permission set."},
    {"name": "users", "description": "Admin management of user (learner) accounts."},
    {"name": "user-auth", "description": "Public user registration/login for the (separately built) simulator app."},
    {"name": "markets", "description": "Admin CRUD for market categories and markets, including the OPEN/CLOSED/... status state machine."},
    {"name": "public-markets", "description": "Public read-only market listing -- the contract a future app consumes."},
    {"name": "game-types", "description": "The central game-type registry (Single, Jodi, Panna variants, Open/Close, ...)."},
    {"name": "game-type-configs", "description": "Per-market/slot game-type enablement + bulk-mode configuration."},
    {"name": "starline", "description": "Admin CRUD for Starline daily time slots."},
    {"name": "rates", "description": "Simulated payout rate configuration, time-versioned via effective_from."},
    {"name": "credits", "description": "The Learning Credits ledger: grant/adjust/reset, no deposit/withdrawal/payment concepts."},
    {"name": "simulations", "description": "Admin manual entry / bulk-on-behalf-of-user simulation submission."},
    {"name": "public-simulations", "description": "The generic BulkSelectionEngine: single + bulk selection submission for a JWT-authenticated user."},
    {"name": "results", "description": "Draft/publish/correct workflow. Server-side ank/jodi derivation and payout evaluation. Deletion is per-record only."},
    {"name": "public-results", "description": "Public read-only published results + historical chart-ready data."},
    {"name": "public-starline", "description": "Public Starline market/slot listing."},
    {"name": "public-gali-disawar", "description": "Public Gali-Disawar market listing."},
    {"name": "public-game-types", "description": "Public game-type registry + per-type rules."},
    {"name": "support", "description": "Support ticket queries and admin replies."},
    {"name": "audit", "description": "Append-only log of admin actions."},
    {"name": "content", "description": "Admin CMS: homepage banners, scrolling messages, educational content, FAQ, site settings."},
    {"name": "public-content", "description": "Public homepage/support/educational content."},
]

app = FastAPI(
    title="Kalyan Simulator Admin API",
    version="4.0.0",
    description=(
        "Configuration engine for an educational number-game simulator. All monetary-looking "
        "values are virtual Learning Credits -- there is no real-money deposit, withdrawal, "
        "payment gateway, or cash settlement anywhere in this system. Admin endpoints live under "
        "`/admin/*` (protected); public endpoints (`/markets`, `/simulations`, ...) are the "
        "contract a future app consumes."
    ),
    openapi_tags=TAGS_METADATA,
    # Interactive docs enumerate every endpoint; keep them off in production.
    docs_url=None if settings.APP_ENV == "production" else "/docs",
    redoc_url=None if settings.APP_ENV == "production" else "/redoc",
    openapi_url=None if settings.APP_ENV == "production" else "/openapi.json",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store"
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    client = request.client.host if request.client else "?"
    request_logger.info(f"--> {request.method} {request.url.path} from {client}")
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.monotonic() - start) * 1000
        request_logger.exception(f"<-- {request.method} {request.url.path} RAISED after {elapsed_ms:.0f}ms")
        raise
    elapsed_ms = (time.monotonic() - start) * 1000
    request_logger.info(f"<-- {request.method} {request.url.path} {response.status_code} in {elapsed_ms:.0f}ms")
    return response


_STATUS_TO_ERROR_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def _error_envelope(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "statusCode": status_code,
            "error": error_code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return _error_envelope(exc.status_code, exc.code, exc.detail)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    code = _STATUS_TO_ERROR_CODE.get(exc.status_code, "ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_envelope(exc.status_code, code, message)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err.get("loc", []) if p != "body")
        parts.append(f"{field}: {err.get('msg')}" if field else err.get("msg", "Invalid request"))
    message = "; ".join(parts) or "Invalid request"
    return _error_envelope(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", message)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# --- Admin (protected, /admin/*) ---
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admins.router)
app.include_router(roles.router)
app.include_router(roles.permissions_router)
app.include_router(users.router)
app.include_router(market_categories.router)
app.include_router(game_types.router)
app.include_router(markets.router)
app.include_router(game_type_configs.router)
app.include_router(starline.router)
app.include_router(rates.router)
app.include_router(credits.router)
app.include_router(credits.global_router)
app.include_router(credit_requests.router)
app.include_router(simulations.router)
app.include_router(results.router)
app.include_router(reports.router)
app.include_router(support.router)
app.include_router(content.router)
app.include_router(audit_logs.router)

# --- Public (bare paths, future app contract) ---
app.include_router(user_auth.router)
app.include_router(public_markets.router)
app.include_router(public_starline.router)
app.include_router(public_gali_disawar.router)
app.include_router(public_game_types.router)
app.include_router(public_simulations.router)
app.include_router(public_results.router)
app.include_router(public_content.router)

# --- Mobile-app compatibility layer (/api/v1/*, matches the Flutter app's
# ApiEndPoints.baseUrl contract). Virtual Learning Credits only -- no
# deposit/withdrawal/payment endpoints live here by design.
app.include_router(app_api.router)


@app.get("/")
async def root():
    return {"message": "Kalyan Simulator Admin API is running"}
