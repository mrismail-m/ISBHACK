"""Strictness mapping tests from docs/ai-spec.md section 3."""

import itertools

import pytest

from app.ai.strictness import (
    PROFILES,
    STRICTNESS_ORDER,
    criterion_marks,
    round_half_up_to_half,
)


def test_marks_never_increase_as_strictness_rises() -> None:
    for level, errors, ambiguous, max_marks in itertools.product(
        range(5), range(6), (False, True), (5, 10)
    ):
        marks = [criterion_marks(level, errors, ambiguous, max_marks, s) for s in STRICTNESS_ORDER]
        assert marks == sorted(marks, reverse=True), (level, errors, ambiguous, max_marks, marks)


def test_marks_are_halves_and_within_bounds() -> None:
    for level, errors, ambiguous, max_marks, strictness in itertools.product(
        range(5), range(6), (False, True), (5, 10), STRICTNESS_ORDER
    ):
        m = criterion_marks(level, errors, ambiguous, max_marks, strictness)
        assert m * 2 == int(m * 2)
        assert 0 <= m <= max_marks


def test_worked_example_totals() -> None:
    levels = [3, 2, 3, 4]
    errors = [1, 0, 3, 0]
    expected = {"lenient": 17.5, "normal": 15.5, "strict": 14.0, "very_strict": 11.0}
    for strictness, total in expected.items():
        pairs = zip(levels, errors, strict=True)
        got = sum(criterion_marks(lv, er, False, 5, strictness) for lv, er in pairs)
        assert got == total, strictness


def test_level_zero_is_always_zero_even_when_ambiguous() -> None:
    for s in STRICTNESS_ORDER:
        assert criterion_marks(0, 0, True, 10, s) == 0.0


def test_level_is_monotonic_within_a_strictness() -> None:
    for s in STRICTNESS_ORDER:
        marks = [criterion_marks(level, 0, False, 10, s) for level in range(5)]
        assert marks == sorted(marks)
    assert all(p.level_fraction[4] == 1.0 for p in PROFILES.values())


def test_full_level_without_errors_gets_full_marks() -> None:
    for s in STRICTNESS_ORDER:
        assert criterion_marks(4, 0, False, 5, s) == 5.0


def test_rounding_halves_go_up() -> None:
    assert round_half_up_to_half(2.75) == 3.0
    assert round_half_up_to_half(2.25) == 2.5
    assert round_half_up_to_half(2.24) == 2.0


def test_bad_inputs_raise() -> None:
    with pytest.raises(ValueError):
        criterion_marks(2, 0, False, 5, "harsh")
    with pytest.raises(ValueError):
        criterion_marks(5, 0, False, 5, "normal")
