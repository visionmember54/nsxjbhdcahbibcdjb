"""The single source of truth for selection validation and classification."""
from __future__ import annotations

from collections import Counter

from app.core import errors

# GameType codes -- the 8 built-in registry entries.
SINGLE = "SINGLE"
JODI = "JODI"
SINGLE_PANNA = "SINGLE_PANNA"
DOUBLE_PANNA = "DOUBLE_PANNA"
TRIPLE_PANNA = "TRIPLE_PANNA"
OPEN = "OPEN"
CLOSE = "CLOSE"
OPEN_CLOSE = "OPEN_CLOSE"
HALF_SANGAM = "HALF_SANGAM"
FULL_SANGAM = "FULL_SANGAM"

PANNA_CODES = {SINGLE_PANNA, DOUBLE_PANNA, TRIPLE_PANNA}

# classification_rule values stored on GameType, used by the generic dispatcher.
NONE_RULE = "NONE"
PANNA_SINGLE_RULE = "PANNA_SINGLE"
PANNA_DOUBLE_RULE = "PANNA_DOUBLE"
PANNA_TRIPLE_RULE = "PANNA_TRIPLE"
SANGAM_HALF_RULE = "SANGAM_HALF"
SANGAM_FULL_RULE = "SANGAM_FULL"

_CLASSIFICATION_TO_CODE = {
    PANNA_SINGLE_RULE: SINGLE_PANNA,
    PANNA_DOUBLE_RULE: DOUBLE_PANNA,
    PANNA_TRIPLE_RULE: TRIPLE_PANNA,
}


class SelectionValidationError(ValueError):
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.code = code


def classify_panna(value: str) -> str:
    """Classic Matka panna classification: single = 3 distinct digits,
    double = exactly two equal, triple = all three equal."""
    counts = Counter(value)
    if len(counts) == 1:
        return TRIPLE_PANNA
    if len(counts) == 2:
        return DOUBLE_PANNA
    return SINGLE_PANNA


_PANNA_CODE_TO_ERROR = {
    SINGLE_PANNA: errors.INVALID_SINGLE_PANNA,
    DOUBLE_PANNA: errors.INVALID_DOUBLE_PANNA,
    TRIPLE_PANNA: errors.INVALID_TRIPLE_PANNA,
}


def validate_single(value: str) -> None:
    value = value.strip()
    if not (len(value) == 1 and value.isdigit()):
        raise SelectionValidationError(f"Single/Open/Close ank must be exactly 1 digit, got '{value}'", code=errors.INVALID_SINGLE)


def validate_jodi(value: str) -> None:
    value = value.strip()
    if not (len(value) == 2 and value.isdigit()):
        raise SelectionValidationError(f"Jodi must be exactly 2 digits (00-99), got '{value}'", code=errors.INVALID_JODI)


def validate_panna(value: str, expected_classification: str) -> None:
    code = _PANNA_CODE_TO_ERROR.get(expected_classification, errors.INVALID_PANNA)
    value = value.strip()
    if not (len(value) == 3 and value.isdigit()):
        raise SelectionValidationError(
            f"{expected_classification.replace('_', ' ').title()} must be exactly 3 digits, got '{value}'", code=code
        )
    actual = classify_panna(value)
    if actual != expected_classification:
        raise SelectionValidationError(
            f"'{value}' is a {actual.replace('_', ' ').lower()}, not a {expected_classification.replace('_', ' ').lower()}", code=code
        )


def validate_single_panna(value: str) -> None:
    validate_panna(value, SINGLE_PANNA)


def validate_double_panna(value: str) -> None:
    validate_panna(value, DOUBLE_PANNA)


def validate_triple_panna(value: str) -> None:
    validate_panna(value, TRIPLE_PANNA)


def validate_panna_shape(value: str) -> None:
    """Shape-only check for admin RESULT entry: a winning panna can be any
    classification (single/double/triple), unlike a user's SELECTION which
    must match the exact bet-type classification."""
    value = value.strip()
    if not (len(value) == 3 and value.isdigit()):
        raise SelectionValidationError(f"Panna must be exactly 3 digits, got '{value}'")


def validate_half_sangam(value: str, variant: str | None) -> None:
    """A Half Sangam is a panna and ank joined by one hyphen.

    The variant is stored independently because ``128-4`` has two possible
    result directions and must never be inferred after submission.
    """
    if variant not in {"OPEN_PANNA_CLOSE_ANK", "OPEN_ANK_CLOSE_PANNA"}:
        raise SelectionValidationError("Half Sangam requires a valid game_variant", code=errors.INVALID_PANNA)
    parts = value.strip().split("-")
    if len(parts) != 2:
        raise SelectionValidationError("Half Sangam must use PANNA-ANK format (for example 128-4)", code=errors.INVALID_PANNA)
    try:
        validate_panna_shape(parts[0])
        validate_single(parts[1])
    except SelectionValidationError as exc:
        raise SelectionValidationError(str(exc), code=errors.INVALID_PANNA) from exc


def validate_full_sangam(value: str) -> None:
    """A Full Sangam is open panna and close panna: ``128-470``."""
    parts = value.strip().split("-")
    if len(parts) != 2:
        raise SelectionValidationError("Full Sangam must use PANNA-PANNA format (for example 128-470)", code=errors.INVALID_PANNA)
    try:
        validate_panna_shape(parts[0])
        validate_panna_shape(parts[1])
    except SelectionValidationError as exc:
        raise SelectionValidationError(str(exc), code=errors.INVALID_PANNA) from exc


def validate_selection(game_type_code: str, classification_rule: str, value: str, game_variant: str | None = None) -> None:
    """Generic dispatcher: validates `value` against whichever shape the game
    type's registry row declares, so a future custom GameType (not one of the
    8 built-ins) still gets shape validation driven purely by its config."""
    if classification_rule == SANGAM_HALF_RULE:
        validate_half_sangam(value, game_variant)
        return
    if classification_rule == SANGAM_FULL_RULE:
        validate_full_sangam(value)
        return
    if classification_rule in _CLASSIFICATION_TO_CODE:
        validate_panna(value, _CLASSIFICATION_TO_CODE[classification_rule])
        return

    if game_type_code == JODI:
        validate_jodi(value)
        return

    # SINGLE, OPEN, CLOSE, OPEN_CLOSE, and any custom 1-digit type
    validate_single(value)


def derive_ank_from_panna(panna: str) -> str:
    """Standard Matka rule: ank = last digit of the panna's digit sum."""
    digit_sum = sum(int(d) for d in panna)
    return str(digit_sum % 10)


def derive_jodi(open_ank: str, close_ank: str) -> str:
    return f"{open_ank}{close_ank}"


def compute_simulated_return(credits: int, rate: int) -> int:
    return (credits * rate) // 10
