"""MAE, quadratic weighted kappa, consistency range.

See docs/evaluation.md section 2. Task: M4.1. Pure Python, no scikit-learn needed.
"""

from collections.abc import Sequence


def mae(a: Sequence[float], b: Sequence[float]) -> float:
    """Mean absolute error between two equal-length lists."""
    if len(a) != len(b) or not a:
        raise ValueError("mae needs two non-empty lists of the same length")
    return sum(abs(x - y) for x, y in zip(a, b, strict=True)) / len(a)


def qwk(a: Sequence[int], b: Sequence[int], levels: int = 5) -> float:
    """Quadratic weighted kappa for integer ratings 0..levels-1.

    Matches sklearn's cohen_kappa_score(a, b, weights="quadratic"). If both raters give one
    constant rating, there is no variance to measure: return 1.0 when they agree, else 0.0.
    """
    if len(a) != len(b) or not a:
        raise ValueError("qwk needs two non-empty lists of the same length")
    n = len(a)
    observed = [[0.0] * levels for _ in range(levels)]
    for x, y in zip(a, b, strict=True):
        observed[x][y] += 1
    row = [sum(observed[i]) for i in range(levels)]
    col = [sum(observed[i][j] for i in range(levels)) for j in range(levels)]
    num = den = 0.0
    for i in range(levels):
        for j in range(levels):
            weight = (i - j) ** 2 / (levels - 1) ** 2
            num += weight * observed[i][j]
            den += weight * row[i] * col[j] / n
    if den == 0:
        return 1.0 if list(a) == list(b) else 0.0
    return 1.0 - num / den


def range_stats(runs_per_item: Sequence[Sequence[float]]) -> tuple[float, float]:
    """Mean and max of (max - min) across repeated runs, one inner list per item."""
    if not runs_per_item:
        raise ValueError("range_stats needs at least one item")
    ranges = [max(runs) - min(runs) for runs in runs_per_item]
    return sum(ranges) / len(ranges), max(ranges)


def share_identical(runs_per_item: Sequence[Sequence[Sequence[int]]]) -> float:
    """Share of (item, criterion) pairs whose level is the same in every run.

    `runs_per_item[i][r]` is the list of criterion levels for item i in run r.
    """
    same = total = 0
    for runs in runs_per_item:
        for column in zip(*runs, strict=True):
            total += 1
            same += len(set(column)) == 1
    return same / total if total else 0.0


def abs_delta_stats(before: Sequence[float], after: Sequence[float]) -> tuple[float, float]:
    """Mean and max absolute change between paired totals."""
    deltas = [abs(y - x) for x, y in zip(before, after, strict=True)]
    return sum(deltas) / len(deltas), max(deltas)


def signed_mean_delta(before: Sequence[float], after: Sequence[float]) -> float:
    return sum(y - x for x, y in zip(before, after, strict=True)) / len(before)
