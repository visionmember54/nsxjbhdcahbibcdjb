from __future__ import annotations

import pytest

from app.services import validation_service as vs


def test_classify_panna_triple():
    assert vs.classify_panna("111") == vs.TRIPLE_PANNA
    assert vs.classify_panna("000") == vs.TRIPLE_PANNA


def test_classify_panna_double():
    assert vs.classify_panna("112") == vs.DOUBLE_PANNA
    assert vs.classify_panna("122") == vs.DOUBLE_PANNA


def test_classify_panna_single():
    assert vs.classify_panna("123") == vs.SINGLE_PANNA
    assert vs.classify_panna("145") == vs.SINGLE_PANNA


def test_validate_jodi_accepts_00_to_99():
    vs.validate_jodi("00")
    vs.validate_jodi("99")
    vs.validate_jodi("45")


def test_validate_jodi_rejects_wrong_length():
    with pytest.raises(vs.SelectionValidationError):
        vs.validate_jodi("5")
    with pytest.raises(vs.SelectionValidationError):
        vs.validate_jodi("123")


def test_validate_single_panna_rejects_double():
    with pytest.raises(vs.SelectionValidationError):
        vs.validate_single_panna("112")


def test_validate_double_panna_rejects_single():
    with pytest.raises(vs.SelectionValidationError):
        vs.validate_double_panna("123")


def test_validate_triple_panna_rejects_double():
    with pytest.raises(vs.SelectionValidationError):
        vs.validate_triple_panna("112")


def test_validate_selection_dispatches_by_classification_rule():
    vs.validate_selection("SINGLE_PANNA", "PANNA_SINGLE", "123")
    with pytest.raises(vs.SelectionValidationError):
        vs.validate_selection("SINGLE_PANNA", "PANNA_SINGLE", "112")

    vs.validate_selection("JODI", "NONE", "45")
    vs.validate_selection("SINGLE", "NONE", "5")


def test_derive_ank_from_panna():
    assert vs.derive_ank_from_panna("128") == "1"  # 1+2+8=11 -> 1
    assert vs.derive_ank_from_panna("600") == "6"
    assert vs.derive_ank_from_panna("111") == "3"


def test_derive_jodi():
    assert vs.derive_jodi("1", "6") == "16"
    assert vs.derive_jodi("0", "0") == "00"


def test_compute_simulated_return():
    assert vs.compute_simulated_return(100, 95) == 950
    assert vs.compute_simulated_return(100, 950) == 9500
