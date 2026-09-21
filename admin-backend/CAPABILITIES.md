# Game Capability Matrix

This is the audit required before declaring the Admin Panel complete: every feature
in the simulation platform, whether or not the (separately built, untouched-this-pass)
Flutter student app currently has a screen for it.

**A feature missing from the current Student App is not a feature that does not
exist.** Everything below is fully configurable from the Admin Panel and fully
exposed through the public API today — a future Student App screen is a pure
frontend task against an already-complete backend, never a backend rewrite.

| Game / Feature | Admin Supported | Backend Supported | API Ready | Student UI Present | Student UI Later |
|---|---|---|---|---|---|
| Single / Ank | Y | Y | Y | Y (Single Digit) | — |
| Jodi | Y | Y | Y | Y (Jodi Digit) | — |
| Single Panna | Y | Y | Y | Y (Single Pana) | — |
| Double Panna | Y | Y | Y | Y (Double Pana) | — |
| Triple Panna | Y | Y | Y | Y (Triple Pana) | — |
| Open | Y | Y | Y | Y (session toggle) | — |
| Close | Y | Y | Y | Y (session toggle) | — |
| Open + Close | Y | Y | Y | Partial (per-type toggle, not a combined bet) | Y |
| Starline (slot-based markets) | Y | Y | Y | — | Y |
| Gali | Y | Y | Y | Y (flat market list) | — |
| Disawar | Y | Y | Y | Y (flat market list) | — |
| Bulk Jodi | Y | Y | Y | — | Y |
| Bulk Single Panna | Y | Y | Y | — | Y |
| Bulk Double Panna | Y | Y | Y | — | Y |
| Bulk Triple Panna | Y | Y | Y | — | Y |
| Custom game types (beyond the 8 built-ins) | Y | Y | Y | — | Y |
| Custom market categories (beyond MATKA/STARLINE/GALI_DISAWAR) | Y | Y | Y | — | Y |
| Market status state machine (UPCOMING/OPEN/CLOSED/RESULT_PENDING/RESULT_PUBLISHED/SUSPENDED) | Y | Y | Y | Partial (static labels only) | Y |
| Simulated Rates (time-versioned) | Y | Y | Y | Y (static display) | — |
| Learning Credits (grant/adjust/reset) | Y | Y | Y | Partial (static balance display) | Y |
| Result draft/publish | Y | Y | Y | — | Y |
| Result correction (with payout reversal, mandatory reason) | Y | Y | Y | — | Y |
| Individual simulation outcome override (mandatory reason, distinct from result correction) | Y | Y | Y | — | Y |
| Historical results | Y | Y | Y | Y (static chart) | — |
| Number frequency reports | Y | Y | Y (admin-only) | — | — |
| Simulation/game statistics | Y | Y | Y (admin-only) | — | — |
| Homepage banners / scrolling messages | Y | Y | Y | Y (static banner/marquee) | — |
| Educational content per game type | Y | Y | Y | — | Y |
| FAQ / support contact config | Y | Y | Y | Partial (hardcoded contact) | Y |
| Student registration/login | — | Y | Y | Y (UI only, no backend call) | Y |

## Design notes

- **Data-driven RBAC**: `Role`/`Permission`/`RolePermission` tables (see `app/models/role.py`,
  `app/core/rbac_catalog.py`) replace the old hardcoded `require_roles("super_admin", ...)`
  allowlists. `Admin.role` still stores a plain slug string (no FK) — it's matched against
  `Role.slug` at permission-check time, so assigning a brand-new custom role (created via
  `POST /admin/roles`) to an admin needs zero code changes. `require_permission(code)` in
  `app/core/deps.py` is the gate every admin router now uses; `/admin/auth/me` and `/login`
  return the caller's own resolved permission list so the frontend can gate UI without needing
  `admins.manage` just to introspect its own role.

- **Structured error codes**: privileged/validation failures raise `AppError` (see
  `app/core/errors.py`) instead of a plain-text `HTTPException`, so API consumers get
  `{"success": false, "error": {"code", "message"}}` with a stable machine-readable
  `code` (e.g. `CUTOFF_PASSED`, `INSUFFICIENT_LEARNING_CREDITS`) instead of parsing
  prose. Not every raise site was converted — only the ones the spec names a code for.
- **Cutoff enforcement**: `Market.cutoff_time` (falls back to `closing_time`) and
  `StarlineSlot.cutoff_time` are checked against wall-clock time in the market's own
  `timezone` (stdlib `zoneinfo`) on every submission, on top of the existing admin-toggled
  status/enabled checks. `cutoff_time = None` means "not configured" and never blocks.
- **Mandatory reasons**: credit grant/adjust/reset, result correction, and simulation
  override all require a non-empty reason/note at the schema layer now — this was
  previously optional for credits and entirely absent for corrections.

- **Rate convention**: `Rate.rate` is "win per 10 credits staked" (matches the Student
  App mockup's `10 : 95`-style display). Payout = `(credits * rate) // 10`.
- **Starline slot results** and **Gali-Disawar open/close** both reuse
  `MarketResult.open_panna/open_ank/close_panna/close_ank/jodi` rather than a separate
  `single_result` field, because their resolution mechanics are structurally identical
  to Matka's open-side mechanics (ank derived from a declared panna or digit). This
  keeps one evaluation code path (`result_service.evaluate_pending_entries`) correct
  for every category instead of three separate implementations.
- **Open+Close as a single combined bet type** (spec's `OPEN_CLOSE` game-type code)
  exists in the registry and is enabled/disabled per market like any other type, but
  no dedicated combined-selection validation was needed since Open and Close are
  independently-staged Single/Panna submissions in this engine — `OPEN_CLOSE` is
  available for a future market that wants to label a market "runs both stages" at
  the market-status level rather than the per-bet level.
