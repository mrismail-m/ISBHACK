"""Export only synthetic cohort data for the offline frontend."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import engine, get_session
from app.demo_seed import install_demo
from app.main import app
from app.models.core import Assessment, Classroom, User


def export_demo() -> None:
    memory = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(memory)
    with Session(engine) as source, Session(memory) as session:
        template = source.get(Assessment, "a_1")
        if not template:
            raise ValueError("Seed the database before exporting fixtures.")
        session.add(Assessment.model_validate(template.model_dump()))
        session.add(User(id="u_teacher_1", name="Demo teacher", role="teacher",
                         classroom_id="cl_1"))
        session.add(Classroom(id="cl_1", name="BAI demo cohort", teacher_id="u_teacher_1"))
        session.commit()
        install_demo(session)
        app.dependency_overrides[get_session] = lambda: session
        try:
            with TestClient(app) as client:
                routes = ["/classrooms/cl_1/performance", "/classrooms/cl_1/attention"]
                for period in range(1, 5):
                    aid = f"demo_a_{period}" if period < 4 else "a_1"
                    routes += [f"/assessments/{aid}{suffix}" for suffix in
                               ("", "/submissions", "/stats", "/override-stats")]
                for period in range(1, 5):
                    for number in range(1, 51):
                        routes += [f"/submissions/demo_s_{period}_{number}{suffix}"
                                   for suffix in ("", "/grade", "/activity/events",
                                                  "/activity/summary")]
                routes += ["/assessments/a_write"]
                data = {}
                for route in routes:
                    response = client.get("/api/v1" + route,
                                          headers={"X-User-Id": "u_teacher_1"})
                    if response.status_code != 200:
                        raise ValueError(f"Fixture export failed: {route}: {response.status_code}")
                    data[route] = response.json()
                assessments = client.get("/api/v1/assessments").json()
        finally:
            app.dependency_overrides.clear()
    root = Path(__file__).resolve().parents[2] / "fixtures"
    (root / "demo/api.json").write_text(json.dumps(data) + "\n", encoding="utf-8")
    (root / "api/assessments.json").write_text(json.dumps(assessments, indent=2) + "\n")
    print("Offline synthetic demo fixtures exported.")


if __name__ == "__main__":
    export_demo()
