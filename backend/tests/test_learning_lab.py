"""Learning-loop state, grounding, recovery, and classroom isolation."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.ai import learning_lab as ai
from app.ai.learning_lab import RecoveryPlan
from app.config import get_settings
from app.llm.client import LLMError
from app.models.core import Submission, User
from app.models.learning_lab import LearningLabSession
from app.schemas.learning_lab import LabObservation
from tests.conftest import make_submission

ROOT = "/api/v1/submissions/s_1/learning-lab"
STUDENT = {"X-User-Id": "u_student_3"}
TEACHER = {"X-User-Id": "teacher"}


@pytest.fixture
def lab_db(seeded: Session) -> Session:
    for id_, role, classroom in (
        ("u_student_3", "student", "cl_1"), ("other", "student", "cl_1"),
        ("teacher", "teacher", "cl_1"), ("outsider", "teacher", "cl_other"),
    ):
        seeded.add(User(id=id_, name="Not sent to model", role=role, classroom_id=classroom))
    seeded.commit()
    return seeded


def answer(client: TestClient, phase: str, text: str):
    return client.post(ROOT + "/answer", headers=STUDENT,
                       json={"phase": phase, "answer_text": text})


def test_learning_loop_recovery_and_resumption(client: TestClient, lab_db: Session):
    original = lab_db.get(Submission, "s_1")
    original_status = original.status
    first = client.post(ROOT + "/start", headers=STUDENT)
    assert first.status_code == 200, first.text
    assert first.json()["mode"] == "fixture"
    assert first.json()["recovery"] is None
    assert "criteria" not in first.text
    assert client.post(ROOT + "/start", headers=STUDENT).json() == first.json()
    text = "It is always constant time because hashing is fast."
    response = answer(client, "challenge", text)
    assert response.status_code == 200, response.text
    assert response.json()["initial"]["level"] == 0
    assert response.json()["phase"] == "recovery"
    assert response.json()["recovery"] != response.json()["challenge"]
    assert response.json()["initial"]["teaching"]
    assert answer(client, "challenge", text).json() == response.json()
    assert answer(client, "challenge", "A replacement answer").status_code == 409
    final = answer(client, "recovery", "No. The same bucket still holds every key, so lookup "
                   "can scan the entire chain in O(n). Change the hash mapping.")
    assert final.status_code == 200, final.text
    assert final.json()["final"]["level"] == 2
    assert final.json()["phase"] == "complete"
    assert client.get(ROOT, headers=STUDENT).json() == final.json()
    report = client.get("/api/v1/assessments/a_1/learning-lab", headers=TEACHER)
    assert report.json()["sessions"] == [final.json()]
    lab_db.refresh(original)
    assert original.status == original_status


def test_recovery_can_still_need_followup(client: TestClient, lab_db: Session):
    client.post(ROOT + "/start", headers=STUDENT)
    answer(client, "challenge", "The chain requires a linear scan in O(n).")
    final = answer(client, "recovery", "Doubling the space always fixes it.")
    assert final.json()["initial"]["level"] == 2
    assert final.json()["final"]["level"] == 0


def test_access_and_phase_boundaries(client: TestClient, lab_db: Session):
    assert client.post(ROOT + "/start").status_code == 403
    for user in (TEACHER, {"X-User-Id": "other"}, {"X-User-Id": "outsider"}):
        assert client.post(ROOT + "/start", headers=user).status_code == 403
    client.post(ROOT + "/start", headers=STUDENT)
    assert answer(client, "recovery", "Skip the first question").status_code == 409
    assert answer(client, "challenge", "   ").status_code == 422
    assert client.get(ROOT, headers={"X-User-Id": "other"}).status_code == 403
    assert client.get("/api/v1/assessments/a_1/learning-lab", headers=STUDENT).status_code == 403
    assert client.get("/api/v1/assessments/a_1/learning-lab",
                      headers={"X-User-Id": "outsider"}).status_code == 404


def test_draft_cannot_start(client: TestClient, lab_db: Session):
    lab_db.add(make_submission(id="draft", status="draft"))
    lab_db.commit()
    response = client.post("/api/v1/submissions/draft/learning-lab/start", headers=STUDENT)
    assert response.status_code == 409


def test_unverified_observation_is_not_saved(
    client: TestClient, lab_db: Session, monkeypatch: pytest.MonkeyPatch,
):
    client.post(ROOT + "/start", headers=STUDENT)
    monkeypatch.setenv("MOCK_LLM", "0")
    get_settings.cache_clear()
    monkeypatch.setattr(ai, "complete_json", lambda **_: LabObservation(
        level=2, reasoning="Unsupported claim", suspected_gap="", answer_quote="invented",
        teaching="Some teaching",
    ))
    assert answer(client, "challenge", "My actual answer").status_code == 502
    row = lab_db.get(LearningLabSession, "lab_s_1")
    assert row.phase == "challenge"
    assert row.initial is None


def test_real_plan_rejects_invented_anchor(monkeypatch: pytest.MonkeyPatch):
    plan = ai.generate_plan("A hash table stores keys.", "Explain hashing", ["hashing"])
    plan.anchor_quote = "not in the assignment"
    monkeypatch.setenv("MOCK_LLM", "0")
    get_settings.cache_clear()
    monkeypatch.setattr(ai, "complete_json", lambda **_: plan)
    with pytest.raises(LLMError, match="verified quote"):
        ai.generate_plan("A hash table stores keys.", "Explain hashing", ["hashing"])


def test_recovery_generation_receives_observed_gap(monkeypatch: pytest.MonkeyPatch):
    import json

    plan = ai.generate_plan("A hash table stores keys.", "Explain hashing", ["hashing"])
    observation = LabObservation(level=0, reasoning="Missing chain traversal", answer_quote="fast",
                                 suspected_gap="Searching inside a bucket",
                                 teaching="Trace the entries inside the chain.")
    captured = {}

    def generate(**kwargs):
        captured.update(json.loads(kwargs["user"]))
        return RecoveryPlan(question={"scenario": "Five keys share bucket 3.",
                                      "question": "Explain the search for the last key."},
                            criteria="Traverse the chain until the key matches.")

    monkeypatch.setenv("MOCK_LLM", "0")
    get_settings.cache_clear()
    monkeypatch.setattr(ai, "complete_json", generate)
    updated = ai.adapt_recovery(plan, observation)
    assert captured["observed_gap"] == observation.suspected_gap
    assert captured["explanation_given"] == observation.teaching
    assert updated.recovery != plan.recovery
    assert updated.challenge == plan.challenge
    assert "student_id" not in captured
