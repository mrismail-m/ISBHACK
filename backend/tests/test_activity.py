"""Shared-fixture parity and activity endpoint round trip."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import create_app
from app.models.core import Assessment, Submission, User
from app.schemas.activity import ActivityEvents
from app.services.activity_summary import summarize_activity

CASES = json.loads(
    (Path(__file__).resolve().parents[2] / "fixtures/activity/cases.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("fixture", CASES, ids=lambda f: f["name"])
def test_summary_fixture(fixture):
    summary = summarize_activity(
        fixture["submission_id"],
        ActivityEvents.model_validate(fixture["activity"]),
        fixture["paste_flag_chars"],
    ).model_dump()
    expected = fixture["expected"]
    for field, value in expected.items():
        if field not in {"doc", "paste_chunks"}:
            assert summary[field] == value
    assert len(summary["paste_chunks"]) == len(expected["paste_chunks"])
    for actual, expected_chunk in zip(
        summary["paste_chunks"], expected["paste_chunks"], strict=True
    ):
        for field, value in expected_chunk.items():
            assert actual[field] == value


def test_ingestion_roundtrip_and_access():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "fixtures/api/assessments.json").read_text()
    )[0]
    assessment = Assessment.model_validate(data)
    with Session(engine) as session:
        session.add(assessment)
        session.add(User(id="student", name="Student", role="student", classroom_id="cl_1"))
        session.add(User(id="other", name="Other", role="student", classroom_id="cl_1"))
        session.add(User(id="teacher", name="Teacher", role="teacher", classroom_id="cl_1"))
        session.add(
            Submission(
                id="s_test",
                assessment_id=assessment.id,
                student_id="student",
                content_md="",
                answers=[],
                status="draft",
                started_at=assessment.created_at,
            )
        )
        session.commit()
    app = create_app()

    def sessions():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = sessions
    with TestClient(app) as client:
        path = "/api/v1/submissions/s_test/activity"
        headers = {"X-User-Id": "student"}
        events = [
            {k: v for k, v in e.items() if k != "session_id"}
            for e in CASES[1]["activity"]["events"]
        ]
        batch = {
            "session_id": "one",
            "session_started_at": "2026-10-10T07:00:00Z",
            "events": events,
        }
        assert client.post(path, json=batch, headers=headers).json() == {
            "received": 2,
            "last_seq": 1,
        }
        assert client.post(path, json=batch, headers=headers).json()["received"] == 0
        assert (
            client.get(path + "/summary", headers={"X-User-Id": "teacher"}).json()["pasted_pct"]
            == 100
        )
        assert len(client.get(path + "/events", headers=headers).json()["events"]) == 2
        assert client.get(path + "/events", headers={"X-User-Id": "other"}).status_code == 403
        assert client.post(path, json=batch, headers={"X-User-Id": "teacher"}).status_code == 403
        invalid = {
            **batch,
            "events": [{"seq": 2, "t": 2000, "k": "del", "from": 0, "to": 999, "text": ""}],
        }
        assert client.post(path, json=invalid, headers=headers).status_code == 422
