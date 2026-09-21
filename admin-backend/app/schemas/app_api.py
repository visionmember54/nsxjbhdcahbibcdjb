"""Request shapes for the /api/v1/* mobile-app compatibility layer.

These mirror the payloads the Flutter app's repositories actually send
(config/api_endpoints.dart + repositories/*.dart), not the admin schemas.
Everything here stays within the existing virtual Learning Credits model --
there is deliberately no deposit/withdrawal/bank-detail schema in this file.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class DeviceInfo(BaseModel):
    deviceId: str | None = None
    platform: str | None = None
    osVersion: str | None = None
    model: str | None = None


class AppLoginRequest(BaseModel):
    phone: str
    password: str
    fcmToken: str | None = None
    deviceInfo: DeviceInfo | None = None


class SendRegisterOtpRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=20)


class AppRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=6, max_length=20)
    password: str = Field(min_length=6, max_length=255)
    email: str = ""
    fcmToken: str | None = None
    otpSessionId: str
    otp: str


class ForgotPasswordRequestOtp(BaseModel):
    phone: str = Field(min_length=6, max_length=20)


class ForgotPasswordConfirm(BaseModel):
    otpSessionId: str
    otp: str
    newPassword: str = Field(min_length=6, max_length=255)


class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str = Field(min_length=6, max_length=255)


class StandardBetItemIn(BaseModel):
    number: str
    points: int = Field(gt=0, le=1_000_000)


class StandardBetRequest(BaseModel):
    marketId: str | None = None
    marketName: str | None = None
    # Starline slot to bet on (the `slotId` from /starline/slots). If omitted, a slot time in the
    # market name (e.g. "KALYAN STARLINE 12:00 PM") is used instead.
    slotId: str | None = None
    betType: str
    session: str | None = None
    items: list[StandardBetItemIn] = Field(min_length=1, max_length=500)
    totalPoints: int | None = None

    @model_validator(mode="after")
    def _require_market_reference(self):
        if not self.marketId and not self.marketName and not self.slotId:
            raise ValueError("Either marketId or marketName is required")
        return self


class HalfSangamBetItemIn(BaseModel):
    format: str | None = None
    openPana: str | None = None
    closeDigit: str | None = None
    openDigit: str | None = None
    closePana: str | None = None
    points: int = Field(gt=0, le=1_000_000)


class HalfSangamBetRequest(BaseModel):
    marketId: str | None = None
    marketName: str | None = None
    bets: list[HalfSangamBetItemIn] = Field(min_length=1, max_length=500)
    totalPoints: int | None = None

    @model_validator(mode="after")
    def _require_market_reference(self):
        if not self.marketId and not self.marketName:
            raise ValueError("Either marketId or marketName is required")
        return self


class FullSangamBetItemIn(BaseModel):
    openPana: str
    closePana: str
    points: int = Field(gt=0, le=1_000_000)


class FullSangamBetRequest(BaseModel):
    marketId: str | None = None
    marketName: str | None = None
    bets: list[FullSangamBetItemIn] = Field(min_length=1, max_length=500)
    totalPoints: int | None = None

    @model_validator(mode="after")
    def _require_market_reference(self):
        if not self.marketId and not self.marketName:
            raise ValueError("Either marketId or marketName is required")
        return self


class GaliDesawarBetItemIn(BaseModel):
    number: str
    points: int = Field(gt=0, le=1_000_000)


class GaliDesawarBetRequest(BaseModel):
    gameId: str | None = None
    marketId: str | None = None
    betType: str | None = None
    # Not in the spec doc, but real GALI/DISAWAR data requires it: SINGLE has
    # separate OPEN/CLOSE configs with no BOTH fallback (see report).
    session: str | None = None
    numbers: list[GaliDesawarBetItemIn] = Field(min_length=1, max_length=500)
    totalPoints: int | None = None

    @model_validator(mode="after")
    def _require_market_reference(self):
        if not self.gameId and not self.marketId:
            raise ValueError("Either gameId or marketId is required")
        return self


class SupportChatRequest(BaseModel):
    message: str = Field(min_length=1)
    sessionId: str | None = None
    language: str | None = None


class AppCreditRequestCreate(BaseModel):
    requestType: str = Field(default="Deposit")
    amount: int = Field(gt=0, le=1_000_000)
    utrNumber: str | None = Field(default=None, max_length=100)
    screenshotUrl: str | None = Field(default=None)
    paymentDetails: str | None = Field(default=None)
    reason: str | None = Field(default=None, max_length=500)


class AppDepositRequest(BaseModel):
    requestType: str = Field(default="Deposit")
    amount: int = Field(gt=0, le=1_000_000)
    utrNumber: str | None = Field(default=None, max_length=100)
    paymentDetails: str | None = Field(default=None)
    screenshotUrl: str | None = Field(default=None)
    reason: str | None = Field(default="Deposit via UPI", max_length=500)


class AppWithdrawRequest(BaseModel):
    requestType: str = Field(default="Withdrawal")
    amount: int = Field(gt=0, le=1_000_000)
    payoutMethod: str | None = Field(default=None)
    paymentDetails: str | None = Field(default=None)
    reason: str | None = Field(default=None, max_length=500)
