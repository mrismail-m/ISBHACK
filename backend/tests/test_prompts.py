"""Prompt files render fully: a system part, a filled user part, no leftover placeholders."""

import re

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.ai import feedback as feedback_module
from app.ai import rubric as rubric_module
from app.ai.feedback import LLMFeedback
from app.ai.loader import load_prompt
from app.models.core import Assessment
from app.schemas.grading import CriterionGrade, Rubric
from tests.sample_data import RUBRIC, SAMPLE_SUBMISSION

PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


@pytest.mark.parametrize("name", ["grader", "feedback", "rubric", "examiner", "scorer"])
def test_every_prompt_has_a_version_system_and_user_part(name: str) -> None:
    prompt = load_prompt(name)
    assert re.fullmatch(r"[a-z]+-v\d+", prompt.version)
    assert len(prompt.system) > 100
    assert len(prompt.user_template) > 20, f"{name}.md is missing the ---USER--- section"


def test_feedback_prompt_carries_rubric_result_and_submission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def spy(**kwargs: object) -> LLMFeedback:
        seen["system"], seen["user"] = str(kwargs["system"]), str(kwargs["user"])
        return LLMFeedback(strengths=[], improvements=[], next_step="x")

    monkeypatch.setattr(feedback_module, "complete_json", spy)
    rubric = Rubric.model_validate(RUBRIC)
    criteria = [
        CriterionGrade(
            criterion_id=c.id, level=3, minor_errors=0, ambiguous=False, ai_marks=4,
            final_marks=4, evidence=[], reasoning="Solid.", confidence=0.8,
        )
        for c in rubric.criteria
    ]
    feedback_module.generate_feedback(
        mode="hints", rubric=rubric, criteria=criteria, content_md=SAMPLE_SUBMISSION, key="s_1"
    )
    assert "Mode: hints" in seen["user"]
    assert "Concept accuracy" in seen["user"]
    assert "Solid." in seen["user"]
    assert "a collision happens when two keys map to the same index" in seen["user"]
    assert not PLACEHOLDER.search(seen["user"])


def test_feedback_lists_are_trimmed_to_three(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.schemas.grading import FeedbackImprovement, FeedbackStrength

    def many(**kwargs: object) -> LLMFeedback:
        return LLMFeedback(
            strengths=[FeedbackStrength(criterion_id="c1", text=f"s{i}") for i in range(5)],
            improvements=[
                FeedbackImprovement(criterion_id="c2", text=f"i{i}", hint="h") for i in range(4)
            ],
            next_step="x",
        )

    monkeypatch.setattr(feedback_module, "complete_json", many)
    rubric = Rubric.model_validate(RUBRIC)
    out = feedback_module.generate_feedback(
        mode="full", rubric=rubric, criteria=[], content_md="text", key="s_1"
    )
    assert len(out.strengths) == 3 and len(out.improvements) == 3


def test_rubric_prompt_carries_marks_instructions_and_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def spy(**kwargs: object) -> Rubric:
        seen["user"] = str(kwargs["user"])
        return Rubric.model_validate(RUBRIC)

    monkeypatch.setattr(rubric_module, "complete_json", spy)
    assessment = Assessment(
        id="a_x", classroom_id="cl_1", kind="assignment", title="T",
        instructions_md="Explain chaining.", max_marks=20.0, pass_mark_pct=50.0,
        strictness="normal", viva_enabled=True, viva_weight=0.3, viva_question_count=3,
        viva_time_limit_s=90, feedback_mode="full", release_mode="after_approval",
        ai_policy="allowed", paste_flag_chars=500, topics=[], status="draft",
        due_at=None, created_at=None,  # type: ignore[arg-type]
    )
    rubric_module.draft_rubric(assessment, notes="Stress examples.")
    assert "Total marks: 20" in seen["user"]
    assert "Explain chaining." in seen["user"]
    assert "Stress examples." in seen["user"]
    assert not PLACEHOLDER.search(seen["user"])


def test_rubric_draft_endpoint_in_mock_mode(client: TestClient, seeded: Session) -> None:
    res = client.post("/api/v1/assessments/a_1/rubric/draft", json={"notes": "More on O(n)."})
    assert res.status_code == 200, res.text
    criteria = res.json()["criteria"]
    assert len(criteria) == 4
    assert sum(c["max_marks"] for c in criteria) == 20
    assert all(len(c["levels"]) == 5 for c in criteria)
    assert client.post("/api/v1/assessments/nope/rubric/draft", json={}).status_code == 404
