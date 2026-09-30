from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

from app.services.app_api_service import iso_ist


class SelectionEntry(BaseModel):
    value: str
    credits: int = Field(gt=0, le=1_000_000)
    game_variant: Literal["OPEN_PANNA_CLOSE_ANK", "OPEN_ANK_CLOSE_PANNA"] | None = None


class SimulationCreate(BaseModel):
    market_id: int
    slot_id: int | None = None
    game_type: str
    stage: Literal["OPEN", "CLOSE"] | None = None
    value: str
    credits: int = Field(gt=0, le=1_000_000)
    game_variant: Literal["OPEN_PANNA_CLOSE_ANK", "OPEN_ANK_CLOSE_PANNA"] | None = None


class BulkSimulationCreate(BaseModel):
    market_id: int
    slot_id: int | None = None
    game_type: str
    stage: Literal["OPEN", "CLOSE"] | None = None
    selections: list[SelectionEntry] = Field(min_length=1, max_length=500)


class AdminSimulationCreate(SimulationCreate):
    user_id: int


class AdminBulkSimulationCreate(BulkSimulationCreate):
    user_id: int


class SimulationOverride(BaseModel):
    outcome: Literal["Won", "Lost"]
    reason: str = Field(min_length=1, max_length=500)


class SimulationEdit(BaseModel):
    selection: str = Field(min_length=1, max_length=20)
    credits: int = Field(gt=0, le=1_000_000)


class SimulationEntryOut(BaseModel):
    id: int
    batchId: int
    userId: int
    userName: str | None = None
    marketId: int
    marketName: str | None = None
    slotId: int | None
    gameType: str
    stage: str | None
    selection: str
    gameVariant: str | None
    openPaana: str | None = None
    openDigit: str | None = None
    closePaana: str | None = None
    closeDigit: str | None = None
    simulatedCredits: int
    simulatedRate: int
    simulatedReturn: int
    status: str
    createdAt: datetime
    resolvedAt: datetime | None
    originalStatus: str | None
    overrideStatus: str | None
    overrideReason: str | None
    overriddenByAdminId: int | None
    overriddenAt: datetime | None

    model_config = {"populate_by_name": True}

    @field_serializer("createdAt", "resolvedAt", "overriddenAt")
    def _serialize_ist(self, value: datetime | None) -> str | None:
        return iso_ist(value)


class SimulationBatchOut(BaseModel):
    batchId: int
    entries: list[SimulationEntryOut]
    totalCredits: int
    remainingBalance: int
