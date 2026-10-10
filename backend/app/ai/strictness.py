"""Strictness profiles and criterion_marks(). See docs/ai-spec.md section 3. Task: M1.1.

The only place that turns levels into marks. Must stay monotonic (lenient >= ... >= very_strict).
The model classifies levels. This code computes marks.
"""

import math
from dataclasses import dataclass

STRICTNESS_ORDER = ("lenient", "normal", "strict", "very_strict")


@dataclass(frozen=True)
class Profile:
    # Fraction of max_marks for levels 0 to 4.
    level_fraction: tuple[float, float, float, float, float]
    penalty_per_error: float
    penalty_cap: float
    ambiguity_adjust: float


PROFILES: dict[str, Profile] = {
    "lenient": Profile((0.00, 0.45, 0.70, 0.90, 1.00), 0.00, 0.00, 0.05),
    "normal": Profile((0.00, 0.30, 0.55, 0.80, 1.00), 0.02, 0.06, 0.00),
    "strict": Profile((0.00, 0.20, 0.45, 0.70, 1.00), 0.04, 0.12, -0.05),
    "very_strict": Profile((0.00, 0.10, 0.30, 0.55, 1.00), 0.06, 0.20, -0.08),
}


def round_half_up_to_half(x: float) -> float:
    """Round to the nearest 0.5, halves go up. The tiny epsilon absorbs float noise."""
    return math.floor(x * 2 + 0.5 + 1e-9) / 2


def criterion_marks(
    level: int,
    minor_errors: int,
    ambiguous: bool,
    max_marks: float,
    strictness: str,
) -> float:
    """Marks for one criterion: a multiple of 0.5 between 0 and max_marks."""
    if strictness not in PROFILES:
        raise ValueError(f"unknown strictness: {strictness}")
    if not 0 <= level <= 4:
        raise ValueError(f"level must be 0 to 4, got {level}")
    if level == 0:
        return 0.0
    p = PROFILES[strictness]
    f = p.level_fraction[level]
    f -= min(p.penalty_cap, max(0, minor_errors) * p.penalty_per_error)
    if ambiguous:
        f += p.ambiguity_adjust
    f = min(1.0, max(0.0, f))
    return min(max_marks, round_half_up_to_half(f * max_marks))
