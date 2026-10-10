"""Majid integration checks for viva, teacher approval and released feedback."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.core import Submission, User

TEACHER = {"X-User-Id": "u_teacher_1"}
STUDENT = {"X-User-Id": "u_student_3"}


@pytest.fixture(autouse=True)
def users(client: TestClient, seeded: Session):
    for id_, role, classroom in [
        ("u_teacher_1", "teacher", "cl_1"),
        ("u_student_3", "student", "cl_1"),
        ("other_student", "student", "cl_1"),
        ("other_teacher", "teacher", "cl_other"),
    ]:
        seeded.add(User(id=id_, role=role, classroom_id=classroom, name=id_))
    seeded.commit()
    client.headers.update(STUDENT)


@pytest.mark.parametrize("marks", [-1, 6, "5", True])
def test_approval_rejects_invalid_criterion_marks(client: TestClient, seeded: Session, marks):
    path = "/api/v1/submissions/s_1"
    assert client.post(path + "/grade").status_code == 200
    response = client.post(path + "/approve", headers=TEACHER, json={
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
    approved = client.post(path + "/approve", headers=TEACHER, json={"release": True})
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


@pytest.mark.parametrize("user", ["other_student", "other_teacher", "missing"])
def test_other_users_cannot_read_or_mutate_work(client: TestClient, seeded: Session, user):
    headers = {"X-User-Id": user}
    path = "/api/v1/submissions/s_1"
    for suffix in ["", "/result", "/viva"]:
        assert client.get(path + suffix, headers=headers).status_code == 403
    assert client.put(path, headers=headers, json={"content_md": "changed"}).status_code == 403
    for suffix, body in [
        ("/submit", {}), ("/approve", {"release": True}), ("/viva/start", {}),
        ("/viva/answer", {"question_id": "vq_1", "answer_text": "changed", "time_taken_s": 1}),
        ("/viva/finish", {}),
    ]:
        assert client.post(path + suffix, headers=headers, json=body).status_code == 403
    assert seeded.get(Submission, "s_1").content_md != "changed"


def test_student_cannot_approve_or_list_class_work(client: TestClient):
    assert client.post("/api/v1/submissions/s_1/approve", json={"release": True}).status_code == 403
    assert client.get("/api/v1/assessments/a_1/submissions").status_code == 403
    assert client.get("/api/v1/assessments/a_1/submissions", headers=TEACHER).status_code == 200
