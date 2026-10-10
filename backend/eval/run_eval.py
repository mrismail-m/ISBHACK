# ruff: noqa: E501  (long report text lines)
"""Trust report runner. See docs/evaluation.md. Task: M4.1.

Usage (from backend/):
  python -m eval.run_eval --quick          accuracy + strictness + signals (uses the LLM cache)
  python -m eval.run_eval --all --yes      everything (about 145 LLM calls)
  python -m eval.run_eval --accuracy | --consistency | --probes | --strictness | --signals

Any run that would make more than 20 real LLM calls needs --yes. Raw per-answer results are
saved to eval/reports/raw_results.json so sections can be recomputed without new calls.
"""

import argparse
import json
import os
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, TypeVar

from app.ai.grader import run_grader
from app.ai.strictness import STRICTNESS_ORDER, criterion_marks
from app.config import FIXTURES_DIR, get_settings
from app.llm import client as llm
from app.llm.client import LLMError
from app.schemas.grading import Rubric
from eval import metrics, probes
from eval.data import (
    Answer,
    Assessment,
    load_answers,
    load_assessment,
    load_author_levels,
    load_human_scores,
)

REPORTS_DIR = Path(__file__).parent / "reports"
REPORT_JSON = REPORTS_DIR / "trust_report.json"
REPORT_MD = REPORTS_DIR / "trust_report.md"
RAW_JSON = REPORTS_DIR / "raw_results.json"
DEMO_SESSIONS = FIXTURES_DIR / "activity" / "demo_sessions.json"

CONSISTENCY_IDS = ["e02", "e05", "e08", "e11", "e14"]
CONSISTENCY_RUNS = 5
WORKERS = 3  # at most 3 LLM calls at a time (docs/ai-spec.md section 8)
CONFIRM_ABOVE_CALLS = 20
DEFAULT_MAX_CALLS = 170
GRADER_PROMPT_VERSION = "grader-v1"


class BudgetExceeded(RuntimeError):
    pass


# ---- context and small helpers ---------------------------------------------------------


@dataclass
class Context:
    assessment: Assessment
    answers: list[Answer]
    raw: dict[str, Any]
    start_requests: int = 0
    max_calls: int = DEFAULT_MAX_CALLS
    failures: list[str] = field(default_factory=list)

    @property
    def rubric(self) -> Rubric:
        return self.assessment.rubric

    @property
    def crit_ids(self) -> list[str]:
        return [c.id for c in self.rubric.criteria]

    @property
    def style_ids(self) -> set[str]:
        """Criteria that judge writing style. Style probes leave these out on purpose."""
        return {c.id for c in self.rubric.criteria if c.topic == "communication"}

    def calls_used(self) -> int:
        return llm.request_count() - self.start_requests


def say(message: str) -> None:
    print(message, flush=True)


T = TypeVar("T")
R = TypeVar("R")


def pmap(ctx: Context, label: str, fn: Callable[[T], R], items: list[T]) -> list[R | None]:
    """Run fn over items, at most WORKERS at a time. A failed item becomes None."""
    results: list[R | None] = [None] * len(items)
    done = 0

    def work(i: int) -> None:
        nonlocal done
        if ctx.calls_used() > ctx.max_calls:
            raise BudgetExceeded(f"more than {ctx.max_calls} LLM requests; stopping")
        try:
            results[i] = fn(items[i])
        except LLMError as exc:
            ctx.failures.append(f"{label} item {i}: {exc}")
        done += 1
        say(f"  [{label}] {done}/{len(items)} done, {ctx.calls_used()} requests so far")

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(work, range(len(items))))
    return results


def grade_record(ctx: Context, text: str, rubric: Rubric | None = None) -> dict[str, Any]:
    """Grade one text and keep what later steps need, keyed by criterion id."""
    res = run_grader(
        content_md=text,
        title=ctx.assessment.title,
        instructions_md=ctx.assessment.instructions_md,
        model_answer_md=None,
        rubric=rubric or ctx.rubric,
    )
    return {
        "criteria": {c.criterion_id: [c.level, c.minor_errors, c.ambiguous] for c in res.criteria},
        "flags": list(res.flags),
        "model_id": res.model_id,
    }


def total(
    rubric: Rubric,
    record: dict[str, Any],
    strictness: str = "normal",
    include: set[str] | None = None,
    minor_errors: bool = True,
) -> float:
    """Total marks for a record. `minor_errors=False` counts levels only (what humans give)."""
    marks = 0.0
    for c in rubric.criteria:
        if include is not None and c.id not in include:
            continue
        level, minor, ambiguous = record["criteria"][c.id]
        marks += criterion_marks(
            level,
            minor if minor_errors else 0,
            ambiguous if minor_errors else False,
            c.max_marks,
            strictness,
        )
    return marks


def levels_total(rubric: Rubric, levels: list[int], strictness: str = "normal") -> float:
    return sum(
        criterion_marks(level, 0, False, c.max_marks, strictness)
        for c, level in zip(rubric.criteria, levels, strict=True)
    )


def round2(x: float) -> float:
    return round(x, 2)


# ---- accuracy and strictness (one grading pass over all answers) -----------------------


def ensure_accuracy_records(ctx: Context) -> dict[str, dict[str, Any]]:
    """Grade every answer at normal strictness, reusing saved results when present."""
    saved: dict[str, dict[str, Any]] = ctx.raw.setdefault("accuracy", {})
    todo = [a for a in ctx.answers if a.answer_id not in saved]
    if todo:
        say(f"Grading {len(todo)} answers...")
        out = pmap(ctx, "accuracy", lambda a: grade_record(ctx, a.text), todo)
        for answer, record in zip(todo, out, strict=True):
            if record is not None:
                saved[answer.answer_id] = record
    return saved


def accuracy_section(ctx: Context) -> dict[str, Any]:
    records = ensure_accuracy_records(ctx)
    rubric = ctx.rubric
    ids = [a.answer_id for a in ctx.answers if a.answer_id in records]
    ai_levels = {i: [records[i]["criteria"][c][0] for c in ctx.crit_ids] for i in ids}
    ai_totals = {i: levels_total(rubric, ai_levels[i]) for i in ids}

    author = load_author_levels()
    both = [i for i in ids if i in author]
    author_totals = [levels_total(rubric, author[i]) for i in both]
    a_flat = [lv for i in both for lv in ai_levels[i]]
    h_flat = [lv for i in both for lv in author[i]]
    by_criterion = {}
    for k, cid in enumerate(ctx.crit_ids):
        ai_k = [ai_levels[i][k] for i in both]
        au_k = [author[i][k] for i in both]
        by_criterion[cid] = {
            "mean_signed_levels": round2(
                sum(a - b for a, b in zip(ai_k, au_k, strict=True)) / len(both)
            ),
            "exact_match_pct": round(
                100 * sum(a == b for a, b in zip(ai_k, au_k, strict=True)) / len(both), 1
            ),
        }
    author_block = {
        "n": len(both),
        "mae_marks": round2(metrics.mae([ai_totals[i] for i in both], author_totals)),
        "qwk": round2(metrics.qwk(a_flat, h_flat)),
        "mean_signed_marks": round2(
            metrics.signed_mean_delta(author_totals, [ai_totals[i] for i in both])
        ),
        "by_criterion": by_criterion,
    }

    humans = load_human_scores(ctx.crit_ids)
    raters = sorted(humans)
    ai_h_mae: float | None = None
    ai_h_qwk: float | None = None
    hh_mae: float | None = None
    hh_qwk: float | None = None
    if raters:
        maes, a_all, h_all = [], [], []
        for r in raters:
            common = [i for i in ids if i in humans[r]]
            if not common:
                continue
            maes.append(
                metrics.mae(
                    [ai_totals[i] for i in common],
                    [levels_total(rubric, humans[r][i]) for i in common],
                )
            )
            a_all += [lv for i in common for lv in ai_levels[i]]
            h_all += [lv for i in common for lv in humans[r][i]]
        if maes:
            ai_h_mae, ai_h_qwk = round2(sum(maes) / len(maes)), round2(metrics.qwk(a_all, h_all))
    if len(raters) >= 2:
        r1, r2 = raters[0], raters[1]
        common = [i for i in humans[r1] if i in humans[r2]]
        if common:
            hh_mae = round2(
                metrics.mae(
                    [levels_total(rubric, humans[r1][i]) for i in common],
                    [levels_total(rubric, humans[r2][i]) for i in common],
                )
            )
            hh_qwk = round2(
                metrics.qwk(
                    [lv for i in common for lv in humans[r1][i]],
                    [lv for i in common for lv in humans[r2][i]],
                )
            )
    return {
        "ai_vs_human_mae": ai_h_mae,
        "human_vs_human_mae": hh_mae,
        "ai_vs_human_qwk": ai_h_qwk,
        "human_vs_human_qwk": hh_qwk,
        "author_labels": author_block,
        "n_raters": len(raters),
    }


def strictness_section(ctx: Context) -> dict[str, Any]:
    records = ensure_accuracy_records(ctx)
    violations = 0
    spreads = []
    for record in records.values():
        totals = [total(ctx.rubric, record, s) for s in STRICTNESS_ORDER]
        if any(later > earlier for earlier, later in zip(totals, totals[1:], strict=False)):
            violations += 1
        spreads.append(totals[0] - totals[-1])
    return {
        "passed": violations == 0,
        "violations": violations,
        "n": len(records),
        "mean_spread_marks": round2(sum(spreads) / len(spreads)) if spreads else 0.0,
    }


# ---- consistency -----------------------------------------------------------------------


def consistency_section(ctx: Context) -> dict[str, Any]:
    ids = [i for i in CONSISTENCY_IDS if any(a.answer_id == i for a in ctx.answers)]
    text_of = {a.answer_id: a.text for a in ctx.answers}
    tasks = [(i, r) for i in ids for r in range(CONSISTENCY_RUNS)]
    say(f"Grading {len(ids)} answers x {CONSISTENCY_RUNS} runs (cache off)...")
    out = pmap(ctx, "consistency", lambda t: grade_record(ctx, text_of[t[0]]), tasks)
    saved: dict[str, list[dict[str, Any]]] = {i: [] for i in ids}
    for (i, _), record in zip(tasks, out, strict=True):
        if record is not None:
            saved[i].append(record)
    ctx.raw["consistency"] = saved
    usable = {i: runs for i, runs in saved.items() if len(runs) >= 2}
    if not usable:
        raise LLMError("No answer had two or more successful runs.")
    totals = [[total(ctx.rubric, r) for r in runs] for runs in usable.values()]
    mean_range, max_range = metrics.range_stats(totals)
    level_runs = [
        [[r["criteria"][c][0] for c in ctx.crit_ids] for r in runs] for runs in usable.values()
    ]
    return {
        "runs": CONSISTENCY_RUNS,
        "mean_range_marks": round2(mean_range),
        "max_range_marks": round2(max_range),
        "n_answers": len(usable),
        "identical_level_pct": round(100 * metrics.share_identical(level_runs), 1),
    }


# ---- bias probes -----------------------------------------------------------------------


def probes_section(ctx: Context) -> list[dict[str, Any]]:
    baseline = ensure_accuracy_records(ctx)
    rubric = ctx.rubric
    max_marks = ctx.assessment.max_marks
    mean_limit = max_marks * probes.MEAN_LIMIT_PCT / 100
    max_limit = max_marks * probes.MAX_LIMIT_PCT / 100
    answers = [a for a in ctx.answers if a.answer_id in baseline]
    saved: dict[str, dict[str, dict[str, Any]]] = ctx.raw.setdefault("probes", {})
    results: list[dict[str, Any]] = []

    for spec in probes.PROBES:
        say(f"Probe {spec.name}: {spec.description}")
        include = (set(ctx.crit_ids) - ctx.style_ids) if spec.skip_style_criteria else None
        variants: list[tuple[Answer, str, Rubric]] = []
        if spec.name == "ai_polish":
            polished = pmap(ctx, "polish", lambda a: probes.ai_polish(a.text), answers)
            variants = [(a, p, rubric) for a, p in zip(answers, polished, strict=True) if p]
        else:
            for idx, a in enumerate(answers):
                if spec.name == "identity_swap":
                    variants.append((a, probes.identity_swap(a.answer_id, a.text, idx), rubric))
                elif spec.name == "typos_nonnative":
                    variants.append((a, probes.add_typos(a.answer_id, a.text), rubric))
                elif spec.name == "padding":
                    variants.append((a, probes.pad(a.text), rubric))
                elif spec.name == "rubric_shuffle":
                    variants.append((a, a.text, probes.shuffled_rubric(a.answer_id, rubric)))
                elif spec.name == "prompt_injection":
                    variants.append((a, probes.inject(a.text), rubric))
        graded = pmap(ctx, spec.name, lambda v: grade_record(ctx, v[1], v[2]), variants)
        pairs = [(v[0].answer_id, g) for v, g in zip(variants, graded, strict=True) if g]
        saved[spec.name] = {aid: g for aid, g in pairs}
        if not pairs:
            continue
        before = [total(rubric, baseline[aid], include=include) for aid, _ in pairs]
        after = [total(rubric, g, include=include) for _, g in pairs]
        mean_abs, max_abs = metrics.abs_delta_stats(before, after)
        entry: dict[str, Any] = {
            "name": spec.name,
            "n": len(pairs),
            "mean_abs_delta_marks": round2(mean_abs),
            "max_abs_delta_marks": round2(max_abs),
            "threshold_marks": round2(mean_limit),
            "passed": mean_abs <= mean_limit and max_abs <= max_limit,
            "mean_signed_delta_marks": round2(metrics.signed_mean_delta(before, after)),
            "description": spec.description,
        }
        if include is not None:
            entry["excluded_criteria"] = sorted(ctx.style_ids)
        if spec.needs_flag:
            rate = sum("injection_attempt" in g["flags"] for _, g in pairs) / len(pairs)
            entry["injection_flag_rate"] = round2(rate)
            entry["passed"] = bool(entry["passed"]) and rate == 1.0
        results.append(entry)
    return results


# ---- editor signals --------------------------------------------------------------------


def signals_section() -> dict[str, Any]:
    """Run the paste rule on Majid's recorded demo sessions (typed, pasted, retyped)."""
    from app.schemas.activity import ActivityEvents
    from app.services.activity_summary import summarize_activity
    from app.services.flags import compute_flags

    data = json.loads(DEMO_SESSIONS.read_text(encoding="utf-8"))
    flagged = {"typed": 0, "pasted": 0, "retyped": 0}
    seen = {"typed": 0, "pasted": 0, "retyped": 0}
    for s in data["sessions"]:
        events = ActivityEvents.model_validate(s["activity"])
        summary = summarize_activity(s["submission_id"], events, s.get("paste_flag_chars", 500))
        flags = compute_flags(SimpleNamespace(viva_enabled=False), None, None, summary)  # type: ignore[arg-type]
        seen[s["name"]] += 1
        flagged[s["name"]] += "paste_heavy" in flags
    return {
        "samples": sum(seen.values()),
        "typed_flagged": flagged["typed"],
        "pasted_flagged": flagged["pasted"],
        "retyped_flagged": flagged["retyped"],
    }


# ---- report ----------------------------------------------------------------------------

EMPTY_REPORT: dict[str, Any] = {
    "generated_at": None,
    "model_id": None,
    "prompt_version": GRADER_PROMPT_VERSION,
    "dataset": None,
    "accuracy": None,
    "consistency": None,
    "bias_probes": None,
    "strictness_ordering": None,
    "editor_signals": None,
    "limitations": [],
}


def models_seen(raw: dict[str, Any]) -> list[str]:
    seen: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "model_id" in node and isinstance(node["model_id"], str):
                seen.add(node["model_id"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(raw)
    return sorted(seen)


def limitations(report: dict[str, Any]) -> list[str]:
    items = [
        f"{report['dataset']['n_answers']} answers is a pilot, not proof.",
        "One assignment, one rubric and one model family: results may not carry over.",
        "Answers were written by the team to cover strong, average, weak and off-topic work.",
        "Totals compare level marks only: raters give levels, not minor-error counts.",
        "Strictness values are starting values and were not tuned on this data.",
        "Retyping AI text by hand evades paste detection. The viva is the answer to that gap.",
        "Editor signals come from 3 automated sessions (1 per class), not from human participants.",
        "Provider fallback can mix models inside one run (see model_id).",
    ]
    if report["dataset"]["n_raters"] < 2:
        items.insert(
            0,
            "Human ratings are pending: AI-versus-human agreement is not measured yet. "
            "'author_labels' compares the AI with the levels the answer author aimed for, "
            "which is a design check and not an independent human rating.",
        )
    return items


def build_report(ctx: Context, updates: dict[str, Any]) -> dict[str, Any]:
    report = dict(EMPTY_REPORT)
    if REPORT_JSON.exists():
        report.update(json.loads(REPORT_JSON.read_text(encoding="utf-8")))
    report.update(updates)
    accuracy = report.get("accuracy") or {}
    n_raters = accuracy.get("n_raters", (report.get("dataset") or {}).get("n_raters", 0))
    report["generated_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report["model_id"] = ", ".join(models_seen(ctx.raw)) or "unknown"
    report["dataset"] = {
        "assignment": ctx.assessment.title,
        "n_answers": len(ctx.answers),
        "n_raters": n_raters,
    }
    if isinstance(report.get("accuracy"), dict):
        report["accuracy"].pop("n_raters", None)
    report["limitations"] = limitations(report)
    return report


def fmt(value: Any, suffix: str = "") -> str:
    return "pending" if value is None else f"{value}{suffix}"


def write_markdown(report: dict[str, Any]) -> str:
    acc = report.get("accuracy") or {}
    author = acc.get("author_labels") or {}
    cons = report.get("consistency") or {}
    bias = report.get("bias_probes") or []
    strict = report.get("strictness_ordering") or {}
    sig = report.get("editor_signals") or {}
    passed = sum(1 for p in bias if p["passed"])
    lines = [
        "# Trust report",
        "",
        f"Generated {report['generated_at']}. Model(s): {report['model_id']}. "
        f"Prompt: {report['prompt_version']}. {report['dataset']['n_answers']} answers, "
        f"{report['dataset']['n_raters']} human rater(s). This is a pilot.",
        "",
        "## The 4 numbers for the slide",
        "",
        f"1. **Agreement.** AI vs human: MAE {fmt(acc.get('ai_vs_human_mae'), ' marks')}, "
        f"QWK {fmt(acc.get('ai_vs_human_qwk'))}. Human vs human: MAE "
        f"{fmt(acc.get('human_vs_human_mae'), ' marks')}, QWK {fmt(acc.get('human_vs_human_qwk'))}.",
        f"2. **Consistency.** Mean range of totals over {cons.get('runs', '?')} runs: "
        f"{fmt(cons.get('mean_range_marks'), ' marks')} (max {fmt(cons.get('max_range_marks'), ' marks')}).",
        f"3. **Bias probes.** {passed} of {len(bias)} passed.",
        f"4. **Strictness ordering.** {'pass' if strict.get('passed') else 'FAIL'}, "
        f"{strict.get('violations', '?')} violations, mean lenient-to-very_strict spread "
        f"{fmt(strict.get('mean_spread_marks'), ' marks')}.",
        "",
        "## AI vs the author's intended levels (design check, not human raters)",
        "",
        f"n={author.get('n', '?')}, MAE {fmt(author.get('mae_marks'), ' marks')}, "
        f"QWK {fmt(author.get('qwk'))}, mean signed error (AI minus author) "
        f"{fmt(author.get('mean_signed_marks'), ' marks')}. Positive means the AI is more generous.",
        "",
        "| Criterion | Mean signed level error | Exact match |",
        "|---|---|---|",
    ]
    for cid, row in (author.get("by_criterion") or {}).items():
        lines.append(f"| {cid} | {row['mean_signed_levels']} | {row['exact_match_pct']}% |")
    lines += [
        "",
        "## Bias probes",
        "",
        "| Probe | n | Mean abs change | Max abs change | Result |",
        "|---|---|---|---|---|",
    ]
    for p in bias:
        extra = (
            f", flagged {int(p['injection_flag_rate'] * 100)}%"
            if "injection_flag_rate" in p
            else ""
        )
        lines.append(
            f"| {p['name']} | {p['n']} | {p['mean_abs_delta_marks']} | {p['max_abs_delta_marks']} | "
            f"{'pass' if p['passed'] else 'FAIL'} (signed mean {p['mean_signed_delta_marks']}{extra}) |"
        )
    lines += [
        "",
        "## Editor signals",
        "",
        f"{fmt(sig.get('samples'))} sessions. Flagged as paste heavy: typed {fmt(sig.get('typed_flagged'))}, "
        f"pasted {fmt(sig.get('pasted_flagged'))}, retyped {fmt(sig.get('retyped_flagged'))}.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in report["limitations"]],
        "",
    ]
    return "\n".join(lines)


# ---- CLI -------------------------------------------------------------------------------


def estimate_calls(sections: set[str], raw: dict[str, Any], n_answers: int) -> int:
    calls = 0
    needs_baseline = bool(sections & {"accuracy", "strictness", "probes"})
    if needs_baseline:
        calls += max(0, n_answers - len(raw.get("accuracy", {})))
    if "consistency" in sections:
        calls += len(CONSISTENCY_IDS) * CONSISTENCY_RUNS
    if "probes" in sections:
        calls += len(probes.PROBES) * n_answers + n_answers  # grading each variant + polish
    return calls


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m eval.run_eval", description=__doc__)
    for name in ("all", "quick", "accuracy", "consistency", "probes", "strictness", "signals"):
        p.add_argument(f"--{name}", action="store_true")
    p.add_argument("--yes", action="store_true", help="confirm a run of more than 20 LLM calls")
    p.add_argument("--max-calls", type=int, default=DEFAULT_MAX_CALLS)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    sections = {
        n
        for n in ("accuracy", "consistency", "probes", "strictness", "signals")
        if getattr(args, n)
    }
    if args.all:
        sections |= {"accuracy", "consistency", "probes", "strictness", "signals"}
    if args.quick:
        sections |= {"accuracy", "strictness", "signals"}
    if not sections:
        say("Nothing to do. Use --quick, --all or a section flag. See --help.")
        return 2

    if "consistency" in sections:
        os.environ["LLM_CACHE"] = "0"  # repeated runs must really call the model
        get_settings.cache_clear()
    settings = get_settings()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    raw = json.loads(RAW_JSON.read_text(encoding="utf-8")) if RAW_JSON.exists() else {}
    answers = load_answers()
    estimate = estimate_calls(sections, raw, len(answers))
    if not settings.mock_llm and estimate > CONFIRM_ABOVE_CALLS and not args.yes:
        say(
            f"This run needs about {estimate} real LLM calls. Tell the team, then re-run with --yes."
        )
        return 2

    ctx = Context(
        assessment=load_assessment(),
        answers=answers,
        raw=raw,
        start_requests=llm.request_count(),
        max_calls=args.max_calls,
    )
    say(
        f"Mock mode: {settings.mock_llm}. Sections: {sorted(sections)}. Estimated calls: {estimate}."
    )
    updates: dict[str, Any] = {}
    try:
        if "accuracy" in sections:
            updates["accuracy"] = accuracy_section(ctx)
        if "strictness" in sections:
            updates["strictness_ordering"] = strictness_section(ctx)
        if "consistency" in sections:
            updates["consistency"] = consistency_section(ctx)
        if "probes" in sections:
            updates["bias_probes"] = probes_section(ctx)
        if "signals" in sections:
            updates["editor_signals"] = signals_section()
    except BudgetExceeded as exc:
        say(f"STOPPED: {exc}")
        RAW_JSON.write_text(json.dumps(ctx.raw, indent=1), encoding="utf-8")
        return 1

    RAW_JSON.write_text(json.dumps(ctx.raw, indent=1), encoding="utf-8")
    report = build_report(ctx, updates)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    REPORT_MD.write_text(write_markdown(report), encoding="utf-8")
    say(f"Done. {ctx.calls_used()} LLM requests. Wrote {REPORT_JSON.name} and {REPORT_MD.name}.")
    if ctx.failures:
        say(f"WARNING: {len(ctx.failures)} item(s) failed and were left out:")
        for f in ctx.failures[:10]:
            say(f"  - {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
