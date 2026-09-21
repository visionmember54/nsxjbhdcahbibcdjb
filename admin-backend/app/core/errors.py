"""Machine-readable error codes: {"success": false, "error": {"code", "message"}}."""
from __future__ import annotations

from fastapi import HTTPException, status

INVALID_SINGLE = "INVALID_SINGLE"
INVALID_JODI = "INVALID_JODI"
INVALID_PANNA = "INVALID_PANNA"
INVALID_SINGLE_PANNA = "INVALID_SINGLE_PANNA"
INVALID_DOUBLE_PANNA = "INVALID_DOUBLE_PANNA"
INVALID_TRIPLE_PANNA = "INVALID_TRIPLE_PANNA"
MARKET_CLOSED = "MARKET_CLOSED"
CUTOFF_PASSED = "CUTOFF_PASSED"
SLOT_CLOSED = "SLOT_CLOSED"
GAME_DISABLED = "GAME_DISABLED"
DUPLICATE_SELECTION = "DUPLICATE_SELECTION"
INSUFFICIENT_LEARNING_CREDITS = "INSUFFICIENT_LEARNING_CREDITS"
INVALID_RESULT = "INVALID_RESULT"
UNAUTHORIZED_OVERRIDE = "UNAUTHORIZED_OVERRIDE"


class AppError(HTTPException):
    """An HTTPException carrying a machine-readable `code` alongside the message."""

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        super().__init__(status_code=status_code, detail=message)
