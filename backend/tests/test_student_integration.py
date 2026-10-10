"""Majid integration checks for viva, teacher approval and released feedback."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.mark.parametrize("marks", [-1, 6, "5", True])
def test_approval_rejects_invalid_criterion_marks(client: TestClient, seeded: Session, marks):
    path = "/api/v1/submissions/s_1"
    assert client.post(path + "/grade").status_code == 200
    response = client.post(path + "/approve", json={
        "criteria_overrides": [{"criterion_id": "c1", "marks": marks}], "release": True,
    })
    assert response.status_code == 422
    assert client.get(path + "/result").status_code == 403


def test_viva_approval_and_student_result(client: TestClient, seeded: Session):
    path = "/api/v1/submissions/s_1"
    assert client.post(path + "/grade").status_code == 200
    assert client.get(path + "/result").status_code == 403
    start = client.post(path + "/viva/start")
    assert start.status_code == 200
    for question in start.json()["questions"]:
        response = client.post(path + "/viva/answer", json={
            "question_id": question["id"],
            "answer_text": "Chaining stores colliding keys in a list.",
            "time_taken_s": 20, "pasted": False, "tab_switches": 0,
        })
        assert response.status_code == 200
    finish = client.post(path + "/viva/finish")
    assert finish.status_code == 200
    approved = client.post(path + "/approve", json={"release": True})
    assert approved.status_code == 200
    result = client.get(path + "/result")
    assert result.status_code == 200
    body = result.json()
    assert body["understanding"] == finish.json()["understanding"]
    assert body["final_marks"] == round(
        0.7 * body["work_marks"] + 0.3 * body["understanding"] * body["max_marks"], 1
    )
    assert body["released_at"]
    assert body["feedback"]["strengths"]
