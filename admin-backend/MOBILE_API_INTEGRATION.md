# Mobile API Integration

Contract for the Flutter app. Every endpoint lives under **`/api/v1`**. All request and response bodies are JSON. Every example response below was captured from the running API against seeded data (tokens and long values shortened).

All amounts are virtual **Learning Credits** ("points"). Amounts are integers in requests and appear as numbers in responses.

## Contents

1. [Conventions](#0-conventions)
2. [Authentication](#1-authentication) (login, register, forgot password) and [Profile](#16-get-profile-)
3. [Configuration & Home](#2-configuration--home)
4. [Markets & Charts](#3-markets--charts)
5. [Betting](#4-betting)
6. [Starline](#5-starline-markets) and [Gali-Desawar](#6-gali-desawar-markets)
7. [History](#7-history)
8. [Wallet](#8-wallet)
9. [Support](#9-support)
10. [Known limitations](#10-known-limitations)

---

## 0. Conventions

**Base URL:** `https://<api-host>/api/v1`

**Auth:** endpoints marked 🔒 need `Authorization: Bearer <token>`, where the token comes from login or register. Tokens last **8 hours**; after that any 🔒 call returns 401 and the app must log in again.

**Success envelope**

```json
{ "success": true, "statusCode": 200, "message": "Success", "data": { } }
```

`message` is human-readable and may be shown to the user. Create endpoints return `statusCode` 201.

**Error envelope** (every failure, any endpoint)

```json
{
  "success": false,
  "statusCode": 401,
  "error": "UNAUTHORIZED",
  "message": "Invalid credentials",
  "timestamp": "2026-09-21T19:25:59.333929+00:00"
}
```

| HTTP | `error` | Meaning |
|---|---|---|
| 400 | `BAD_REQUEST` or a specific code such as `INVALID_SINGLE` | The request was understood but rejected (bad number format, limits, business rule). Show `message`. |
| 401 | `UNAUTHORIZED` | Missing, invalid, expired or revoked token, or wrong credentials. |
| 403 | `FORBIDDEN` | Not allowed. |
| 404 | `NOT_FOUND` | Market, account or resource not found. |
| 422 | `VALIDATION_ERROR` | Body or query failed validation; `message` lists `field: reason` pairs joined by `; `. |
| 429 | `RATE_LIMITED` | Too many failed logins. Honour the `Retry-After` header (seconds). |
| 500 | `INTERNAL_ERROR` | Server fault. |

**Login lockout:** 5 failed logins for the same phone, or from the same IP, within 15 minutes returns 429 until the window passes. A successful login clears the phone's counter.

**Formats**

- IDs are **strings** (`"id": "1"`), even though they are numeric. Send them as strings; numeric strings and numbers are both accepted where a market id is a request field.
- Times of day are 12-hour labels (`"3:00 PM"`). Every timestamp (`createdAt`, `resolvedAt`, `reviewedAt`, `timestamp`, `placedAt`) is ISO-8601 **with the `+05:30` offset** (`2026-09-22T01:11:00+05:30`), so it parses to the right instant. Date filters and `drawDate` use the **IST calendar day**.
- Results are shown as `OPENPANNA-JODI-CLOSEPANNA`. Unpublished parts are masked with `*` (`"***-**-***"`).
- `payout` / `payoutRatio` strings look like `"10:95"` (10 credits pays 95).

**Session status values** (markets): `UPCOMING`, `OPENING` (open betting still allowed), `CLOSING` (close betting still allowed), `CLOSED_TODAY`.

**Bet status values:** `PENDING`, `WON`, `LOST`, `CANCELLED`.

---

## 1. Authentication

### 1.1 Login

`POST /api/v1/auth/login`

| Field | Type | Required | Notes |
|---|---|---|---|
| `phone` | string | yes | |
| `password` | string | yes | |
| `fcmToken` | string | no | accepted, currently not stored |
| `deviceInfo` | object | no | `deviceId`, `platform`, `osVersion`, `model` (all optional strings); accepted, currently not stored |

```json
{
  "phone": "9000000000",
  "password": "user12345",
  "fcmToken": "fcm-token",
  "deviceInfo": { "deviceId": "d1", "platform": "android", "osVersion": "14", "model": "Pixel 8" }
}
```

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Login successful",
  "data": {
    "token": "<jwt>",
    "user": { "id": "1", "name": "Test User", "phone": "9000000000", "walletBalance": 1000.0, "status": "ACTIVE" }
  }
}
```

**Errors:** 401 `Invalid credentials` (wrong phone or password, same message for both) · 401 `User account is disabled` · 422 missing field (`password: Field required`) · 429 too many attempts.

### 1.2 Register (step 1: send OTP)

`POST /api/v1/auth/register/send-otp`

| Field | Type | Required | Notes |
|---|---|---|---|
| `phone` | string | yes | 6 to 20 characters |

**200**

```json
{
  "success": true, "statusCode": 200,
  "message": "OTP sent to 9111111111 -- check the backend server console (no SMS provider is configured, so it's logged instead of texted)",
  "data": { "otpSessionId": "otp_register_99f0f7c309", "resendCooldownSeconds": 60 }
}
```

The OTP is valid for 10 minutes. See [Known limitations](#10-known-limitations): no SMS is sent yet.

### 1.3 Register (step 2: confirm)

`POST /api/v1/auth/register`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | 1 to 120 |
| `phone` | string | yes | 6 to 20 |
| `password` | string | yes | 6 to 255 |
| `email` | string | no | default `""` |
| `fcmToken` | string | no | |
| `otpSessionId` | string | yes | from step 1 |
| `otp` | string | yes | |

```json
{ "name": "New User", "phone": "9111111111", "password": "secret123", "email": "new@example.com", "otpSessionId": "otp_register_99f0f7c309", "otp": "1234" }
```

**201** (the user is logged in immediately; new accounts start with a balance of 0)

```json
{
  "success": true, "statusCode": 201, "message": "Account created successfully",
  "data": {
    "token": "<jwt>",
    "user": { "id": "2", "name": "New User", "phone": "9111111111", "walletBalance": 0.0, "status": "ACTIVE" }
  }
}
```

**Errors:** 400 `Invalid or expired OTP` · 400 `A user with this phone number already exists` · 422 validation.

### 1.4 Forgot password (step 1: request OTP)

`POST /api/v1/auth/forgot-password/request-otp`

| Field | Type | Required |
|---|---|---|
| `phone` | string (6 to 20) | yes |

**200**

```json
{ "success": true, "statusCode": 200, "message": "Password reset OTP sent -- check the backend server console (no SMS provider is configured)", "data": { "otpSessionId": "otp_reset_5db134eaef" } }
```

**Errors:** 404 `No account found for this phone number`.

### 1.5 Forgot password (step 2: confirm)

`POST /api/v1/auth/forgot-password/confirm`

| Field | Type | Required | Notes |
|---|---|---|---|
| `otpSessionId` | string | yes | |
| `otp` | string | yes | |
| `newPassword` | string | yes | 6 to 255 |

**200**

```json
{ "success": true, "statusCode": 200, "message": "Password reset successfully. Please login.", "data": {} }
```

**Errors:** 400 `Invalid or expired OTP` · 404 `Account not found`.

### 1.6 Get profile 🔒

`GET /api/v1/user/profile`

**200**

```json
{ "success": true, "statusCode": 200, "message": "Success",
  "data": { "id": "1", "name": "Test User", "phone": "9000000000", "walletBalance": 1000.0, "status": "ACTIVE" } }
```

**Errors:** 401 `Missing bearer token` / `Invalid token`.

### 1.7 Change password 🔒

`PUT /api/v1/user/profile/change-password`

| Field | Type | Required | Notes |
|---|---|---|---|
| `oldPassword` | string | yes | |
| `newPassword` | string | yes | 6 to 255 |

**200**

```json
{ "success": true, "statusCode": 200, "message": "Password changed successfully", "data": {} }
```

**Errors:** 401 `Current password is incorrect` (this is a 401, but it does **not** mean the session expired; do not force a re-login on this endpoint).

---

## 2. Configuration & Home

### 2.1 Dashboard 🔒

`GET /api/v1/home/dashboard`

| Query | Values | Default | Notes |
|---|---|---|---|
| `filter` | `ALL`, `LIVE`, `UPCOMING`, `DONE` | `ALL` | Session status. `LIVE` = `OPENING` or `CLOSING`; `DONE` = `CLOSED_TODAY`. Applied within the chosen `marketType`. |
| `marketType` | `REGULAR`, `ALL`, or a category slug: `MATKA`, `CUSTOM`, `GALI_DISAWAR`, `STARLINE` | `REGULAR` | `REGULAR` = every category except Starline and Gali-Disawar (Matka + Custom + any admin-added category). Case-insensitive. Unknown value returns 400. |

**200** (`GET /api/v1/home/dashboard`)

```json
{
  "success": true, "statusCode": 200, "message": "Dashboard loaded",
  "data": {
    "user": { "id": "1", "name": "Test User", "phone": "9000000000", "walletBalance": 1000.0, "status": "ACTIVE", "unreadNotifications": 0 },
    "appConfig": {
      "noticeMarquee": "Play responsibly",
      "supportWhatsApp": "+911234567890",
      "supportTelegram": "https://t.me/example",
      "appShareUrl": "https://example.com/app"
    },
    "banners": [
      { "id": "1", "title": "Welcome", "imageUrl": "https://cdn.example.com/b1.png", "actionType": "", "targetUrl": "https://example.com" }
    ],
    "marketTypes": [
      { "key": "REGULAR", "label": "Regular" },
      { "key": "STARLINE", "label": "Starline" },
      { "key": "GALI_DISAWAR", "label": "Gali – Disawar" }
    ],
    "markets": [
      {
        "id": "1", "name": "TESTGAME", "marketType": "MATKA",
        "openTime": "3:00 PM", "closeTime": "5:00 PM",
        "result": "***-**-***",
        "sessionStatus": "OPENING", "isOpeningLive": true, "isClosingLive": false, "isBiddingAllowed": true,
        "chartUrl": "", "payoutRatio": "10:95"
      }
    ]
  }
}
```

Notes:

- `marketTypes` drives the tabs. Call again with `marketType=<key>` when a tab is selected. `marketType` on each market is its category slug, so an `ALL` response can be grouped client-side.
- `noticeMarquee` is the enabled scrolling messages joined with ` • `; it falls back to a default welcome text.
- `unreadNotifications` is always `0` (there is no notification feature yet). `actionType` is always `""`.
- Starline markets are listed here with market-level fields only; per-slot data comes from [5.1](#51-starline-slots).

**Errors:** 400 `Invalid marketType. Allowed: REGULAR, ALL, MATKA, STARLINE, GALI_DISAWAR` · 401.

### 2.2 Bootstrap config

`GET /api/v1/config/bootstrap` (no auth; call at app start)

| Query | Type | Notes |
|---|---|---|
| `appVersion` | string | optional, currently informational |
| `platform` | string | optional, currently informational |

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Configuration loaded successfully",
  "data": {
    "maintenanceMode": false,
    "maintenanceMessage": "",
    "appUpdate": { "forceUpdate": false, "latestVersion": "", "minVersion": "", "updateUrl": "" },
    "overviewRules": {
      "minimumBid": 10,
      "ratesSummary": [
        { "game": "SINGLE DIGIT", "rate": "10 KA 95" },
        { "game": "JODI DIGIT", "rate": "10 KA 95" },
        { "game": "HALF SANGAM", "rate": "10 KA 1000" }
      ]
    },
    "support": { "whatsapp": "+911234567890", "telegram": "https://t.me/example", "shareUrl": "https://example.com/app" }
  }
}
```

The app should block on `maintenanceMode: true` (show `maintenanceMessage`) and on `appUpdate.forceUpdate: true` (send the user to `updateUrl`). `ratesSummary` lists one row per active game type; the rate is a general figure, the exact per-market rate is in [3.2](#32-game-modes).

### 2.3 Game rates

`GET /api/v1/config/game-rates` (no auth)

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Rates loaded",
  "data": { "rates": [
    { "title": "SINGLE DIGIT", "payout": "10 KA 95", "multiplier": 9.5 },
    { "title": "HALF SANGAM", "payout": "10 KA 1000", "multiplier": 100.0 }
  ] }
}
```

---

## 3. Markets & Charts

### 3.1 Live results

`GET /api/v1/markets/live-results` (no auth; poll to refresh the home screen)

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": {
    "serverTime": "2026-09-22T00:55:59.585748+05:30",
    "markets": [
      { "id": "1", "result": "***-**-***", "sessionStatus": "OPENING", "isOpeningLive": true, "isClosingLive": false, "isBiddingAllowed": true }
    ]
  }
}
```

Returns every market of every category (Starline and Gali-Disawar included), keyed by `id`.

### 3.2 Game modes

`GET /api/v1/markets/{market_id}/game-modes` (no auth)

| Param | Where | Type | Notes |
|---|---|---|---|
| `market_id` | path | integer | |
| `slot_id` | query | integer | optional; for Starline slots |

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": {
    "marketId": "1", "marketName": "TESTGAME",
    "currentSession": "OPEN", "isSessionActive": true,
    "gameModes": [
      { "id": "single_digit", "name": "SINGLE DIGIT", "payout": "10:95", "active": true },
      { "id": "jodi_digit", "name": "JODI DIGIT", "payout": "10:95", "active": true },
      { "id": "half_sangam", "name": "HALF SANGAM", "payout": "10:1000", "active": true }
    ]
  }
}
```

`currentSession` is `OPEN` or `CLOSE` while betting is possible, otherwise the session status. `name` is the value to send as `betType` when placing a bet. Mode ids: `single_digit`, `left_digit`, `right_digit`, `jodi_digit`, `single_pana`, `double_pana`, `triple_pana`, `half_sangam`, `full_sangam`.

**Errors:** 404 `Market not found`.

### 3.3 Chart

`GET /api/v1/markets/{market_id}/chart` (no auth)

| Param | Where | Type | Default | Notes |
|---|---|---|---|---|
| `market_id` | path | string | | id, or the market name |
| `chart_type` | query | string | `PANEL` | echoed back upper-cased |
| `year` | query | integer | all | only results from this year |
| `limit` | query | integer | `52` | number of weeks, newest first |

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Chart loaded",
  "data": {
    "marketId": "1", "marketName": "TESTGAME", "chartUrl": "", "chartType": "PANEL",
    "records": [
      {
        "week": "05/01 to 11/01", "weekStartDate": "2026-01-05", "weekEndDate": "2026-01-11",
        "days": {
          "MON": { "openPana": "500", "jodi": "**", "closePana": "***", "isHoliday": false },
          "TUE": { "openPana": "***", "jodi": "**", "closePana": "***", "isHoliday": true }
        }
      }
    ]
  }
}
```

`days` always has all seven keys `MON` to `SUN` (only two shown). A day with no published result has `isHoliday: true`. Weeks run Monday to Sunday. `jodi` is `**` until both open and close results are published.

**Errors:** 404 `Market not found`.

---

## 4. Betting 🔒

Every bet endpoint deducts the stake immediately and returns the same `data` shape. A bet is placed on a market by **`marketId`** or **`marketName`** (one of the two is required; case-insensitive name). **Starline** is one market with time slots, so a Starline bet must also identify the slot: send `slotId`, or put the slot time in `marketName` (`"KALYAN STARLINE 12:00 PM"`). A Starline bet with neither returns 400 `Starline bets need a slot...`. Limits per number come from the market's game configuration (for example 10 to 10000 credits); at most 500 numbers per request.

**Common success `data`**

| Field | Type | Notes |
|---|---|---|
| `transactionId` | string | `SIM-<batchId>` |
| `placedAt` | string | ISO timestamp, IST |
| `deductedPoints` | integer | total stake taken |
| `remainingWalletBalance` | number | balance after the bet |

**Common errors**

| Status | Example `message` |
|---|---|
| 400 | `Single/Open/Close ank must be exactly 1 digit, got '55'` (code `INVALID_SINGLE`) |
| 400 | `Credits for '5' must be between 10 and 10000` |
| 400 | `Insufficient Learning Credits for this batch` (code `INSUFFICIENT_LEARNING_CREDITS`) |
| 400 | `This game type is not available for this market/slot/stage` (game not enabled for that market or session), `Total points mismatch` (Gali-Desawar only) |
| 404 | `Market 'X' not found` / `Market not found` / `Slot not found` |
| 400 | `Market 'X' cutoff has passed` (`CUTOFF_PASSED`), `Slot 'X' cutoff has passed` (`SLOT_CLOSED`) |
| 422 | `Value error, Either marketId or marketName is required`, empty list, `points` not between 1 and 1,000,000 |

`totalPoints` is optional; when sent it must equal the sum of all `points` or the request is rejected (Gali-Desawar) / ignored (others), so compute it correctly.

**When a market accepts bets** (the same rule the dashboard's `sessionStatus` uses): open-session bets, Jodi and Sangam stop at the market's cutoff time; close-session bets (`session: "CLOSE"`, or `RIGHT DIGIT` on a Matka market) stay open until the closing time. A Starline slot accepts bets until its own cutoff. `isBiddingAllowed: true` means at least one of these is still open.

### 4.1 Standard bet (Single, Jodi, Panna)

`POST /api/v1/bets/place`

| Field | Type | Required | Notes |
|---|---|---|---|
| `marketId` | string | one of these two | |
| `marketName` | string | one of these two | For Starline, a slot time in the name picks the slot: `"KALYAN STARLINE 12:00 PM"`, `"STARLINE 1:00 PM"` |
| `slotId` | string | Starline only | the `slotId` from [5.1](#51-starline-slots); use it instead of a name. |
| `betType` | string | yes | one of: `SINGLE DIGIT`, `LEFT DIGIT` (open ank), `RIGHT DIGIT` (close ank), `JODI DIGIT`, `SINGLE PANA`, `DOUBLE PANA`, `TRIPLE PANA` (case-insensitive) |
| `session` | string | no | `OPEN` or `CLOSE`. Required when the game is configured per session (typically single digit, left/right digit and pana); games configured for both sessions (typically jodi) don't need it |
| `items` | array | yes | 1 to 500 of `{ "number": string, "points": int }` |
| `totalPoints` | integer | no | |

```json
{
  "marketId": "1", "betType": "SINGLE DIGIT", "session": "OPEN",
  "items": [ { "number": "5", "points": 100 }, { "number": "7", "points": 50 } ],
  "totalPoints": 150
}
```

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Bet placed successfully for 2 numbers!",
  "data": { "transactionId": "SIM-1", "placedAt": "2026-09-22T00:55:59.604588+05:30", "deductedPoints": 150, "remainingWalletBalance": 850.0 }
}
```

### 4.2 Half Sangam

`POST /api/v1/bets/place/half-sangam`

| Field | Type | Required | Notes |
|---|---|---|---|
| `marketId` / `marketName` | string | one of | |
| `bets` | array | yes | 1 to 500 items |
| `bets[].openPana` + `bets[].closeDigit` | string | pair A | open pana with a close digit |
| `bets[].closePana` + `bets[].openDigit` | string | pair B | close pana with an open digit |
| `bets[].points` | integer | yes | |
| `bets[].format` | string | no | accepted, unused |
| `totalPoints` | integer | no | |

Each item must supply **pair A or pair B**.

```json
{ "marketId": "1", "bets": [ { "openPana": "128", "closeDigit": "6", "points": 10 } ], "totalPoints": 10 }
```

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Half Sangam bet placed successfully for 1 pair!",
  "data": { "transactionId": "SIM-3", "placedAt": "2026-09-22T00:55:59.625981+05:30", "deductedPoints": 10, "remainingWalletBalance": 740.0 }
}
```

**Extra error:** 400 `Half Sangam bet needs either (openPana + closeDigit) or (openDigit + closePana)`.

### 4.3 Full Sangam

`POST /api/v1/bets/place/full-sangam`

| Field | Type | Required |
|---|---|---|
| `marketId` / `marketName` | string | one of |
| `bets` | array of `{ "openPana": string, "closePana": string, "points": int }` | yes (1 to 500) |
| `totalPoints` | integer | no |

```json
{ "marketId": "1", "bets": [ { "openPana": "128", "closePana": "600", "points": 10 } ], "totalPoints": 10 }
```

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Full Sangam bet placed successfully for 1 pair!",
  "data": { "transactionId": "SIM-4", "placedAt": "2026-09-22T00:55:59.634562+05:30", "deductedPoints": 10, "remainingWalletBalance": 730.0 }
}
```

**Result timing:** once the admin publishes the result, winning bets are paid into the wallet automatically and a `Payout` row appears in the [wallet statement](#83-wallet-statement). The bet's `status` in [history](#7-history) changes from `PENDING` to `WON` or `LOST`. A Jodi (and Sangam) bet stays `PENDING` until both open and close results are published.

---

## 5. Starline Markets

### 5.1 Starline slots

`GET /api/v1/starline/slots` (no auth)

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": {
    "marketName": "STARLINE", "payoutRatio": "10:95", "drawDate": "2026-09-22",
    "slots": [
      { "slotId": "1", "timeLabel": "10:00 AM", "result": "***-*", "status": "OPEN", "isBiddingOpen": true, "closesInSeconds": 79440 }
    ]
  }
}
```

Only enabled slots are listed. `result` is `PANNA-ANK` (`***-*` until published). `status` is `OPEN` or `CLOSED`; `closesInSeconds` counts down to the slot's cutoff (0 when closed).

### 5.2 Starline charts

`GET /api/v1/starline/charts` (no auth)

| Query | Type | Default | Range |
|---|---|---|---|
| `days` | integer | `15` | 1 to 90 |

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": { "records": [ { "date": "2026-01-05", "results": { "10:00 AM": "500-5", "11:00 AM": "128-1" } } ] }
}
```

Newest date first; `results` maps slot label to `PANNA-ANK`. `records` is `[]` when no results are published.

---

## 6. Gali-Desawar Markets

### 6.1 Gali-Desawar markets

`GET /api/v1/gali-desawar/markets` (no auth)

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": { "markets": [ { "id": "3", "name": "DISAWAR", "openTime": "1:00 AM", "closeTime": "11:59 PM", "result": "**", "isOpen": true } ] }
}
```

`result` is the latest published two-digit result, `**` if none. `isOpen` says whether betting is allowed right now.

### 6.2 Gali-Desawar bet 🔒

`POST /api/v1/gali-desawar/bets`

| Field | Type | Required | Notes |
|---|---|---|---|
| `marketId` | string | one of these two | |
| `gameId` | string | one of these two | treated as the market id |
| `betType` | string | no | `LEFT DIGIT`, `RIGHT DIGIT`, `JODI DIGIT` or `SINGLE DIGIT`. If omitted, 2-digit numbers are treated as Jodi and others as Single |
| `session` | string | no | only used for `SINGLE DIGIT`. `LEFT DIGIT` and `RIGHT DIGIT` decide the session themselves (left = open side, right = close side) and ignore a conflicting `session`; `JODI DIGIT` needs none |
| `numbers` | array | yes | 1 to 500 of `{ "number": string, "points": int }` |
| `totalPoints` | integer | no | if sent and different from the real total, 400 `Total points mismatch` |

```json
{ "marketId": "3", "betType": "JODI DIGIT", "numbers": [ { "number": "45", "points": 20 } ], "totalPoints": 20 }
```

**200** (`transactionId` is `SIM-<id>` or, if several game types were mixed, `SIM-<id>-<id>`)

```json
{
  "success": true, "statusCode": 200, "message": "Bet placed successfully",
  "data": { "transactionId": "SIM-5", "placedAt": "2026-09-22T00:55:59.658007+05:30", "deductedPoints": 20, "remainingWalletBalance": 710.0 }
}
```

Errors are the same as [section 4](#4-betting).

---

## 7. History 🔒

Both endpoints return 20 items per page, newest first. Each item has the same shape:

| Field | Type | Notes |
|---|---|---|
| `id` | string | bet entry id |
| `batchId` | string | the request it was placed in (`SIM-<batchId>`) |
| `marketId` | string | |
| `gameType` | string | `SINGLE`, `OPEN`, `CLOSE`, `JODI`, `SINGLE_PANNA`, `DOUBLE_PANNA`, `TRIPLE_PANNA`, `HALF_SANGAM`, `FULL_SANGAM` |
| `stage` | string or null | `OPEN` / `CLOSE`, or null |
| `selection` | string | the number(s) played, e.g. `"128-600"` |
| `gameVariant` | string or null | Half Sangam: `OPEN_PANNA_CLOSE_ANK` or `OPEN_ANK_CLOSE_PANNA` |
| `simulatedCredits` | integer | stake |
| `simulatedRate` | integer | payout per 10 credits |
| `simulatedReturn` | integer | credits paid if it wins |
| `status` | string | `PENDING`, `WON`, `LOST`, `CANCELLED` |
| `createdAt` / `resolvedAt` | string / null | ISO timestamps |

### 7.1 Bids history

`GET /api/v1/history/bids`

| Query | Type | Default | Notes |
|---|---|---|---|
| `market_type` | string | all | omit or `ALL` for every bid (Starline and Gali-Disawar included). `REGULAR` = Matka + Custom; `STARLINE`; `GALI_DISAWAR` (the old spelling `GALI_DESAWAR` also works); or any category slug |
| `date` | string | all | `DD-MM-YYYY`, an **IST** calendar day, matched against the time the bet was placed |
| `page` | integer | `1` | |

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": { "bids": [
    { "id": "6", "batchId": "5", "marketId": "3", "gameType": "JODI", "stage": null, "selection": "45", "gameVariant": null,
      "simulatedCredits": 20, "simulatedRate": 95, "simulatedReturn": 190, "status": "PENDING",
      "createdAt": "2026-09-21T19:25:59.657585", "resolvedAt": null }
  ] }
}
```

**Errors:** 400 `date must be in DD-MM-YYYY format`.

### 7.2 Wins history

`GET /api/v1/history/wins`

| Query | Type | Default |
|---|---|---|
| `market_type` | string | all (same values as 7.1) |
| `page` | integer | `1` |

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": { "wins": [
    { "id": "1", "batchId": "1", "marketId": "1", "gameType": "SINGLE", "stage": "OPEN", "selection": "5", "gameVariant": null,
      "simulatedCredits": 100, "simulatedRate": 95, "simulatedReturn": 950, "status": "WON",
      "createdAt": "2026-09-21T19:25:59.602121", "resolvedAt": "2026-09-21T19:25:59.664765" }
  ] }
}
```

Only `WON` entries are returned.

---

## 8. Wallet

### 8.1 Payment config

`GET /api/v1/wallet/payment-config` (no auth)

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Payment configuration loaded",
  "data": {
    "upiId": "kalyanmerchant@icici",
    "merchantName": "Kalyan Milan",
    "upiUri": "upi://pay?pa=kalyanmerchant@icici&pn=Kalyan%20Milan&cu=INR",
    "qrCodeUrl": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi%3A//pay%3F...",
    "minDeposit": 300,
    "maxDeposit": 100000,
    "minWithdrawal": 1000,
    "instructions": "1. Pay using UPI to the UPI ID or scan QR.\n2. Note down the 12-digit UTR number.\n3. Enter amount and UTR below."
  }
}
```

Values come from admin site settings; the limits are the ones enforced by 8.4 to 8.6.

### 8.2 Wallet balance 🔒

`GET /api/v1/wallet/balance`

**200**

```json
{ "success": true, "statusCode": 200, "message": "Success",
  "data": { "userId": "1", "balance": 1660.0, "formattedBalance": "1660 Credits" } }
```

### 8.3 Wallet statement 🔒

`GET /api/v1/wallet/statement`

The statement is live: a row exists the moment the action happens. Placing a bet adds one row **per number played** immediately; a win adds its row when the admin publishes the result; a deposit or withdrawal request appears as soon as it is submitted.

| Query | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | 20 rows per page, newest first |
| `transaction_type` | string | all | `CREDIT` or `DEBIT` |
| `from_date` | string | none | `YYYY-MM-DD` (IST day), inclusive |
| `to_date` | string | none | `YYYY-MM-DD` (IST day), inclusive |
| `marketType` | string | `ALL` | `ALL`, `REGULAR` (Matka + Custom), `GALI_DISAWAR`, `STARLINE`. A specific type returns only market-linked rows (bets, wins, result corrections, overrides); deposits, withdrawals and admin grants appear only under `ALL`. Unknown value returns 400. |

**200** (a user who requested a deposit, placed two bets of which one won, and requested a withdrawal)

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": {
    "currentBalance": 800.0,
    "transactions": [
      { "id": "4", "kind": "WITHDRAWAL_HOLD", "title": "Withdrawal Requested", "description": "Withdrawal hold",
        "type": "DEBIT", "amount": 1000, "balanceAfter": 800, "status": "PENDING",
        "transactionId": null, "market": null, "gameType": null, "bets": [],
        "timestamp": "2026-09-21T19:41:17.028165" },
      { "id": "3", "kind": "BET_WON", "title": "Bet Won", "description": "Single Digit 5 won on TESTGAME",
        "type": "CREDIT", "amount": 950, "balanceAfter": 1800, "status": "SUCCESS",
        "transactionId": "SIM-1", "market": { "id": "1", "name": "TESTGAME", "marketType": "MATKA" }, "gameType": "SINGLE",
        "bets": [ { "number": "5", "points": 100, "status": "WON" } ],
        "timestamp": "2026-09-21T19:41:17.013902" },
      { "id": "2", "kind": "BET_PLACED", "title": "Bet Placed", "description": "Single Digit: 7 (50) on TESTGAME",
        "type": "DEBIT", "amount": 50, "balanceAfter": 850, "status": "SUCCESS",
        "transactionId": "SIM-1", "market": { "id": "1", "name": "TESTGAME", "marketType": "MATKA" }, "gameType": "SINGLE",
        "bets": [ { "number": "7", "points": 50, "status": "LOST" } ],
        "timestamp": "2026-09-21T19:41:16.840891" },
      { "id": "1", "kind": "BET_PLACED", "title": "Bet Placed", "description": "Single Digit: 5 (100) on TESTGAME",
        "type": "DEBIT", "amount": 100, "balanceAfter": 900, "status": "SUCCESS",
        "transactionId": "SIM-1", "market": { "id": "1", "name": "TESTGAME", "marketType": "MATKA" }, "gameType": "SINGLE",
        "bets": [ { "number": "5", "points": 100, "status": "WON" } ],
        "timestamp": "2026-09-21T19:41:16.840891" },
      { "id": "REQ_1", "kind": "DEPOSIT_PENDING", "title": "Deposit Pending", "description": "Deposit via UPI",
        "type": "CREDIT", "amount": 500, "balanceAfter": null, "status": "PENDING",
        "transactionId": null, "market": null, "gameType": null, "bets": [],
        "timestamp": "2026-09-21T19:41:16.814381" }
    ]
  }
}
```

**Row fields**

| Field | Type | Notes |
|---|---|---|
| `id` | string | ledger id; `REQ_<n>` for a pending/rejected deposit request (not yet a ledger row) |
| `kind` | string | machine key, see the table below |
| `title` / `description` | string | ready to display |
| `type` | string | `CREDIT` or `DEBIT`; `amount` is always positive |
| `amount` | integer | credits |
| `balanceAfter` | integer or null | running wallet balance after this row; `null` for pending/rejected deposit requests (no money moved) |
| `status` | string | `SUCCESS`, `PENDING`, `REJECTED`, `REFUNDED` (see below) |
| `transactionId` | string or null | `SIM-<batchId>`: rows from the same bet request share it |
| `market` | object or null | `{ id, name, marketType }` |
| `gameType` | string or null | e.g. `SINGLE`, `JODI` |
| `bets` | array | `[{ number, points, status }]`; status is `PENDING`, `WON` or `LOST`, and updates when the result is published |
| `timestamp` | string | ISO timestamp |

**`kind` values**

| `kind` | Title | When |
|---|---|---|
| `BET_PLACED` | Bet Placed | a number is bet on (one row per number, all debits) |
| `BET_WON` | Bet Won | result published and the bet won (credit) |
| `RESULT_CORRECTION` | Result Correction | admin corrected a published result and a payout was reversed (debit) |
| `OUTCOME_OVERRIDE` | Outcome Override | admin overrode a bet's outcome |
| `DEPOSIT_PENDING` | Deposit Pending | deposit request submitted, `status: PENDING`, balance unchanged |
| `DEPOSIT_REJECTED` | Deposit Rejected | admin rejected it, `status: REJECTED` |
| `DEPOSIT_APPROVED` | Deposit Approved | admin approved it; credits added. Replaces the pending row |
| `WITHDRAWAL_HOLD` | Withdrawal Requested | amount held immediately. `status` is `PENDING`, then `SUCCESS` (approved) or `REFUNDED` (rejected) |
| `WITHDRAWAL_REFUND` | Withdrawal Refunded | admin rejected the withdrawal; credits returned |
| `CREDITS_ADDED` | Credits Added | admin grant |
| `OTHER` | title-cased type | any other adjustment or reset |

Bets placed before this release have a single row per bet request (with all its numbers in `bets`); newer bets have one row per number.

**Errors:** 400 `Invalid marketType. Allowed: ...`.

### 8.4 Deposit request 🔒

`POST /api/v1/wallet/deposit/initiate`

| Field | Type | Required | Notes |
|---|---|---|---|
| `amount` | integer | yes | 1 to 1,000,000, and within the min/max deposit from 8.1 |
| `requestType` | string | no | default `Deposit` |
| `utrNumber` | string | no | up to 100 chars |
| `paymentDetails` | string | no | |
| `screenshotUrl` | string | no | |
| `reason` | string | no | up to 500; default `Deposit via UPI` |

```json
{ "requestType": "Deposit", "amount": 500, "utrNumber": "123456789012", "paymentDetails": "UPI", "screenshotUrl": "https://cdn.example.com/s.png", "reason": "Deposit via UPI" }
```

**201**

```json
{
  "success": true, "statusCode": 201, "message": "Deposit request submitted -- an admin will review it shortly.",
  "data": { "id": "DEP_1", "requestedAmount": 500, "reason": "Deposit via UPI", "status": "Pending", "createdAt": "2026-09-21T19:25:59.702843" }
}
```

The balance does **not** change until an admin approves the request. **Errors:** 400 `Minimum deposit amount is 300` / `Maximum deposit amount is 100000`.

### 8.5 Withdrawal request 🔒

`POST /api/v1/wallet/withdraw/request`

| Field | Type | Required | Notes |
|---|---|---|---|
| `amount` | integer | yes | 1 to 1,000,000, at least the minimum withdrawal |
| `requestType` | string | no | default `Withdrawal` |
| `payoutMethod` | string | no | accepted, not stored |
| `paymentDetails` | string | no | e.g. a UPI id |
| `reason` | string | no | up to 500 |

```json
{ "amount": 1000, "payoutMethod": "UPI", "paymentDetails": "me@upi", "reason": "Withdraw" }
```

**201**

```json
{
  "success": true, "statusCode": 201, "message": "Withdrawal request submitted -- an admin will review it shortly.",
  "data": { "id": "WIT_2", "requestedAmount": 1000, "reason": "Withdraw", "status": "Pending", "createdAt": "2026-09-21T19:25:59.713065" }
}
```

The requested amount is **held immediately** (deducted from the balance, shown as a `WITHDRAWAL_HOLD` row) while the request is pending. If the admin rejects the request the amount is refunded (a `WITHDRAWAL_REFUND` row); if approved the hold becomes final. **Errors:** 400 `Minimum withdrawal amount is 1000` · 400 `Insufficient balance for withdrawal`.

### 8.6 Create credit request 🔒

`POST /api/v1/wallet/credit-requests`

Same fields as 8.4 (`requestType`, `amount`, `utrNumber`, `screenshotUrl`, `paymentDetails`, `reason`). If `requestType` is `Withdrawal` (case-insensitive) the withdrawal rules and balance hold of 8.5 apply; anything else follows the deposit rules of 8.4.

```json
{ "requestType": "Deposit", "amount": 400, "utrNumber": "999", "reason": "More credits please" }
```

**201**

```json
{
  "success": true, "statusCode": 201, "message": "Credit request submitted -- an admin will review it shortly.",
  "data": { "id": "3", "requestedAmount": 400, "reason": "More credits please", "status": "Pending", "createdAt": "2026-09-21T19:25:59.721481" }
}
```

Note that `id` here is the bare id (`"3"`), while 8.4 / 8.5 return prefixed ids (`DEP_1`, `WIT_2`). All three create the same kind of record; strip the prefix if you need to match them against 8.7.

**Errors:** as 8.4 / 8.5.

### 8.7 My credit requests 🔒

`GET /api/v1/wallet/credit-requests`

Returns the latest 50 requests (deposit and withdrawal), newest first.

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": { "requests": [
    { "id": "3", "requestType": "Deposit", "requestedAmount": 400, "utrNumber": "999", "screenshotUrl": null,
      "paymentDetails": null, "reason": "More credits please", "status": "Pending", "adminNote": null,
      "createdAt": "2026-09-21T19:25:59.721481", "reviewedAt": null }
  ] }
}
```

`status` is `Pending`, then set by the admin when reviewed (`adminNote` and `reviewedAt` are filled in at that point).

---

## 9. Support

### 9.1 Support chat 🔒

`POST /api/v1/support/chat`

| Field | Type | Required | Notes |
|---|---|---|---|
| `message` | string | yes | at least 1 character |
| `sessionId` | string | no | omit to start a new conversation; send the returned `sessionId` to continue it |
| `language` | string | no | accepted, unused |

```json
{ "message": "I need help", "language": "en" }
```

**200**

```json
{
  "success": true, "statusCode": 200, "message": "Success",
  "data": {
    "sessionId": "1", "sender": "BOT",
    "reply": "Thanks for reaching out — our support team will get back to you shortly.",
    "quickReplies": [], "actionLink": "",
    "timestamp": "2026-09-22T00:55:59.729407+05:30"
  }
}
```

The message is saved as a support ticket the admin team answers in the admin panel. The `reply` is an automatic acknowledgement; admin replies are not delivered through this endpoint yet.

---

## 10. Known limitations

These describe current behaviour so the app is built against reality; they are not the intended final contract.

1. **OTP is a development stand-in.** No SMS is sent. The code is always `1234`, and `otpSessionId: "otp_reg_direct"` skips verification on register. Anyone can therefore register any phone number or reset any user's password. Treat OTP-based flows as untrusted until an SMS provider is integrated.
2. **`market_type` spelling.** Prefer `GALI_DISAWAR` everywhere; history also accepts the older `GALI_DESAWAR`.
3. **Withdrawal holds are settled by an admin**, not automatically: a pending request keeps the amount deducted until an admin approves or rejects it (rejection refunds).
4. **`fcmToken` and `deviceInfo`** are accepted on login/register but not stored, so push notifications are not wired up.
5. **Support replies** from admins are not returned to the app (see 9.1).
6. **Credit request ids** are formatted differently across 8.4, 8.5 and 8.6.
7. **Rates in bootstrap / game-rates** are one representative rate per game type; use game-modes (3.2) for the exact rate of a market.
