"""Evaluation code: metrics, probes, dataset, runner (mock mode) and the report endpoint."""

import csv
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.llm import client as llm
from app.routers import evaluation as evaluation_router
from app.schemas.grading import Rubric, TrustReport
from eval import metrics, probes, run_eval
from eval.data import load_answers, load_assessment, load_author_levels, load_human_scores
from tests.sample_data import RUBRIC

# ---- metrics ---------------------------------------------------------------------------


def test_mae() -> None:
    assert metrics.mae([1, 2, 3], [1, 2, 3]) == 0
    assert metrics.mae([1, 2, 3], [2, 4, 3]) == 1
    with pytest.raises(ValueError):
        metrics.mae([], [])


def test_qwk_known_cases() -> None:
    assert metrics.qwk([0, 1, 2, 3, 4], [0, 1, 2, 3, 4]) == 1.0
    assert metrics.qwk([0, 4], [4, 0]) == -1.0
    assert metrics.qwk([2, 2, 2], [2, 2, 2]) == 1.0  # no variance, full agreement
    assert metrics.qwk([2, 2, 2], [3, 3, 3]) == 0.0  # no variance, no agreement
    # Worked by hand: observed disagreement 3/16, expected 143/16/7, so 1 - 0.1875/1.27679.
    # This implementation also matched scikit-learn on 200 random cases (max diff 2e-16).
    got = metrics.qwk([0, 1, 2, 3, 4, 2, 3], [0, 2, 2, 3, 3, 2, 4])
    assert got == pytest.approx(0.8531468531, abs=1e-9)


def test_range_stats_and_identical_share() -> None:
    mean_range, max_range = metrics.range_stats([[10, 10, 10], [12, 13, 11]])
    assert (mean_range, max_range) == (1.0, 2)
    same = metrics.share_identical([[[3, 2], [3, 2], [3, 2]], [[1, 1], [1, 2], [1, 1]]])
    assert same == 0.75  # 3 of 4 (item, criterion) pairs never changed


def test_delta_stats() -> None:
    assert metrics.abs_delta_stats([10, 10], [11, 8]) == (1.5, 2)
    assert metrics.signed_mean_delta([10, 10], [11, 8]) == -0.5


# ---- dataset ---------------------------------------------------------------------------


def test_dataset_files_are_consistent() -> None:
    answers = load_answers()
    levels = load_author_levels()
    assert len(answers) == 15
    assert {a.answer_id for a in answers} == set(levels)
    assert all(len(v) == 4 and all(0 <= x <= 4 for x in v) for v in levels.values())
    assert all(len(a.text) < 2000 for a in answers)  # well under the 8,000 character limit
    # The set must cover weak to strong work, not only one band.
    totals = sorted(sum(v) for v in levels.values())
    assert totals[0] <= 5 and totals[-1] >= 15


def test_assessment_matches_the_seeded_a1() -> None:
    a = load_assessment()
    assert a.max_marks == 20
    assert [c.id for c in a.rubric.criteria] == ["c1", "c2", "c3", "c4"]


def test_blank_template_gives_no_human_scores(tmp_path: Path) -> None:
    template = Path(__file__).resolve().parents[2] / "fixtures" / "eval"
    template = template / "human_scores_a1.template.csv"
    assert load_human_scores(["c1", "c2", "c3", "c4"], template) == {}


def test_only_complete_rater_rows_are_used(tmp_path: Path) -> None:
    path = tmp_path / "h.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["answer_id", "rater", "criterion_id", "level"])
        for c, level in zip(["c1", "c2", "c3", "c4"], [3, 2, 1, 4], strict=True):
            w.writerow(["e01", "rater1", c, level])
        for c in ["c1", "c2", "c3"]:  # c4 missing: this answer is incomplete
            w.writerow(["e02", "rater1", c, 2])
    assert load_human_scores(["c1", "c2", "c3", "c4"], path) == {"rater1": {"e01": [3, 2, 1, 4]}}
    path.write_text("answer_id,rater,criterion_id,level\ne01,rater1,c1,9\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_human_scores(["c1"], path)


# ---- probes ----------------------------------------------------------------------------


def test_text_probes_change_only_what_they_claim() -> None:
    text = load_answers()[0].text
    swapped = probes.identity_swap("e01", text, 0)
    assert swapped.startswith("Author: ") and swapped.endswith(text)
    assert probes.pad(text).startswith(text) and len(probes.pad(text)) > len(text)
    injected = probes.inject(text)
    assert injected.startswith(text) and "Ignore previous instructions" in injected

    typos = probes.add_typos("e01", text)
    assert typos == probes.add_typos("e01", text)  # deterministic
    assert typos != text
    assert len(typos.split()) >= len(text.split()) * 0.9  # only a few articles dropped
    assert "hash" in typos.lower() and "O(1)" in typos  # meaning-bearing words survive


def test_rubric_shuffle_reorders_but_keeps_every_criterion() -> None:
    rubric = Rubric.model_validate(RUBRIC)
    shuffled = probes.shuffled_rubric("e01", rubric)
    assert [c.id for c in shuffled.criteria] != [c.id for c in rubric.criteria]
    assert sorted(c.id for c in shuffled.criteria) == sorted(c.id for c in rubric.criteria)


def test_probe_list_matches_the_spec() -> None:
    assert [p.name for p in probes.PROBES] == [
        "identity_swap",
        "typos_nonnative",
        "padding",
        "ai_polish",
        "rubric_shuffle",
        "prompt_injection",
    ]


# ---- request counter -------------------------------------------------------------------


def test_request_counter_counts_provider_calls_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        llm,
        "_transport",
        httpx.MockTransport(
            lambda r: httpx.Response(200, json={"choices": [{"message": {"content": '{"a": 1}'}}]})
        ),
    )
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "m")
    monkeypatch.setenv("LLM_API_KEY", "k")
    get_settings.cache_clear()
    from pydantic import BaseModel

    class A(BaseModel):
        a: int

    assert llm.request_count() == 0
    llm.complete_json(role="grader", system="s", user="u", schema=A, prompt_version="t")
    assert llm.request_count() == 1


# ---- runner and endpoint ---------------------------------------------------------------


@pytest.fixture
def report_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(run_eval, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(run_eval, "REPORT_JSON", tmp_path / "trust_report.json")
    monkeypatch.setattr(run_eval, "REPORT_MD", tmp_path / "trust_report.md")
    monkeypatch.setattr(run_eval, "RAW_JSON", tmp_path / "raw_results.json")
    return tmp_path


def test_full_run_in_mock_mode_writes_a_valid_report(report_dir: Path) -> None:
    assert run_eval.main(["--all"]) == 0
    data = json.loads((report_dir / "trust_report.json").read_text(encoding="utf-8"))
    report = TrustReport.model_validate(data)  # the endpoint's schema accepts it
    assert report.dataset.n_answers == 15 and report.dataset.n_raters == 0
    assert [p.name for p in report.bias_probes or []] == [p.name for p in probes.PROBES]
    assert report.strictness_ordering and report.strictness_ordering.passed
    assert report.consistency and report.consistency.runs == 5
    assert report.consistency.mean_range_marks == 0  # mock output never changes
    assert report.editor_signals and report.editor_signals.samples == 3
    assert report.editor_signals.pasted_flagged == 1 and report.editor_signals.typed_flagged == 0
    assert report.model_id == "mock"
    # No human ratings: human numbers stay empty, never invented.
    acc = report.accuracy
    assert acc and acc.ai_vs_human_mae is None and acc.human_vs_human_qwk is None
    assert acc.author_labels and acc.author_labels.n == 15
    assert "Human ratings are pending" in report.limitations[0]
    md = (report_dir / "trust_report.md").read_text(encoding="utf-8")
    assert "The 4 numbers for the slide" in md and "pending" in md


def test_partial_runs_keep_earlier_sections(report_dir: Path) -> None:
    run_eval.main(["--signals"])
    run_eval.main(["--strictness"])
    data = json.loads((report_dir / "trust_report.json").read_text(encoding="utf-8"))
    assert data["editor_signals"] is not None and data["strictness_ordering"] is not None
    assert data["accuracy"] is None and data["bias_probes"] is None


def test_human_scores_fill_the_human_numbers(
    report_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    author = load_author_levels()
    # rater1 agrees with the author, rater2 is one level lower on every criterion.
    humans = {
        "rater1": {k: list(v) for k, v in author.items()},
        "rater2": {k: [max(0, x - 1) for x in v] for k, v in author.items()},
    }
    monkeypatch.setattr(run_eval, "load_human_scores", lambda crit_ids: humans)
    run_eval.main(["--accuracy"])
    data = json.loads((report_dir / "trust_report.json").read_text(encoding="utf-8"))
    acc = data["accuracy"]
    assert data["dataset"]["n_raters"] == 2
    assert acc["human_vs_human_mae"] > 0 and acc["human_vs_human_qwk"] is not None
    assert acc["ai_vs_human_mae"] is not None and acc["ai_vs_human_qwk"] is not None
    assert not any("pending" in item for item in data["limitations"])


def test_big_real_run_needs_confirmation(
    report_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("MOCK_LLM", "0")
    get_settings.cache_clear()
    assert run_eval.main(["--all"]) == 2
    assert "--yes" in capsys.readouterr().out
    assert not (report_dir / "trust_report.json").exists()


def test_call_estimate_matches_the_plan() -> None:
    everything = {"accuracy", "consistency", "probes", "strictness", "signals"}
    assert run_eval.estimate_calls(everything, {}, 15) == 15 + 25 + (6 * 15 + 15)
    assert run_eval.estimate_calls({"signals"}, {}, 15) == 0
    done = {"accuracy": {f"e{i:02d}": {} for i in range(1, 16)}}
    assert run_eval.estimate_calls({"strictness"}, done, 15) == 0


def test_endpoint_serves_the_report_or_404(
    report_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = TestClient(__import__("app.main", fromlist=["app"]).app)
    monkeypatch.setattr(evaluation_router, "REPORT_PATH", report_dir / "trust_report.json")
    missing = client.get("/api/v1/evaluation/trust-report")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"
    run_eval.main(["--quick"])
    ok = client.get("/api/v1/evaluation/trust-report")
    assert ok.status_code == 200
    assert ok.json()["dataset"]["assignment"].startswith("A1")
