from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.services.app_api_service import iso_ist


class ResultUpsert(BaseModel):
    market_id: int
    slot_id: int | None = None
    date: str
    open_panna: str | None = None
    open_ank: str | None = None
    close_panna: str | None = None
    close_ank: str | None = None
    single_result: str | None = None
    publish: bool = False
    selection_overrides: list["ResultSelectionOverride"] = Field(default_factory=list)


class ResultCorrection(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    open_panna: str | None = None
    open_ank: str | None = None
    close_panna: str | None = None
    close_ank: str | None = None
    single_result: str | None = None


class ResultPreviewRequest(BaseModel):
    market_id: int
    slot_id: int | None = None
    open_panna: str | None = None
    open_ank: str | None = None
    close_panna: str | None = None
    close_ank: str | None = None
    selection_overrides: list["ResultSelectionOverride"] = Field(default_factory=list)


class ResultSelectionOverride(BaseModel):
    entry_id: int
    selection: str = Field(min_length=1, max_length=10)


class ResultPreviewWinner(BaseModel):
    entryId: int
    userId: int
    userName: str
    userPhone: str
    gameType: str
    stage: str | None
    selection: str
    gameVariant: str | None
    credits: int
    simulatedRate: int
    potentialPayout: int


class ResultPreviewReviewRow(ResultPreviewWinner):
    isWinner: bool


class ResultPreviewOut(BaseModel):
    openPanna: str | None
    openAnk: str | None
    closePanna: str | None
    closeAnk: str | None
    jodi: str | None
    totalPendingEntries: int
    resolvableEntries: int
    unresolvedEntries: int
    winnersCount: int
    losersCount: int
    totalStakeAtRisk: int
    totalPotentialPayout: int
    winners: list[ResultPreviewWinner]
    reviewRows: list[ResultPreviewReviewRow]


class MarketResultOut(BaseModel):
    id: int
    marketId: int
    slotId: int | None
    date: str
    openPanna: str | None
    openAnk: str | None
    closePanna: str | None
    closeAnk: str | None
    jodi: str | None
    singleResult: str | None
    status: str
    publishedAt: datetime | None
    correctedFromId: int | None
    correctionReason: str | None

    model_config = {"populate_by_name": True}

    @field_serializer("publishedAt")
    def _serialize_ist(self, value: datetime | None) -> str | None:
        return iso_ist(value)
