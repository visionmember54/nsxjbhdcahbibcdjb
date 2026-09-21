from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
