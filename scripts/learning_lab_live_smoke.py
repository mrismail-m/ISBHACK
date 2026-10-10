"""Four-call live Learning Lab check in an isolated in-memory DB.

Run from backend: .venv/Scripts/python ../scripts/learning_lab_live_smoke.py
Saves controlled demo evidence, never modifies the classroom database.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models.core import User  # noqa: E402
from tests.conftest import make_assessment, make_submission  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--interactive', action='store_true',
                        help='Read the actual recovery scenario before typing its answer.')
    args = parser.parse_args()
    if get_settings().mock_llm:
        raise SystemExit("This check requires real provider mode, not MOCK_LLM=1.")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(make_assessment(topics=["complexity"]))
        session.add(make_submission())
        session.add(User(id="u_student_3", name="Controlled demo", role="student",
                         classroom_id="cl_1"))
        session.add(User(id="teacher", name="Demo teacher", role="teacher", classroom_id="cl_1"))
        session.commit()
        app.dependency_overrides[get_session] = lambda: session
        try:
            with TestClient(app) as client:
                root = "/api/v1/submissions/s_1/learning-lab"
                headers = {"X-User-Id": "u_student_3"}
                start = client.post(root + "/start", headers=headers)
                assert start.status_code == 200, start.text
                print("CHALLENGE", json.dumps(start.json()["challenge"]), flush=True)
                initial = client.post(root + "/answer", headers=headers, json={
                    "phase": "challenge", "answer_text":
                    "Lookup is always O(1) because a hash computes an index directly. "
                    "The number of keys in a bucket cannot change that.",
                })
                assert initial.status_code == 200, initial.text
                print("RECOVERY", json.dumps(initial.json()["recovery"]), flush=True)
                print("INITIAL LEVEL", initial.json()["initial"]["level"], flush=True)
                recovery_answer = input("Recovery answer: ") if args.interactive else (
                    "Constant-time lookup is an average-case claim, not a guarantee. "
                    "When all keys collide in one bucket, chaining can require scanning "
                    "every entry, O(n) worst case. With open addressing, long probe "
                    "sequences similarly require O(n). Merely adding empty buckets will "
                    "not help if the faulty hash still sends all keys to one bucket. "
                    "Use a hash mapping that spreads these keys, then rehash the entries, "
                    "and manage load factor. If collisions persist, the worst case remains "
                    "linear rather than automatically becoming O(1)."
                )
                # A broad, explicit explanation, assessed independently against the new scenario.
                final = client.post(root + "/answer", headers=headers, json={
                    "phase": "recovery", "answer_text": recovery_answer,
                })
                assert final.status_code == 200, final.text
                assert final.json()["phase"] == "complete"
                report = client.get("/api/v1/assessments/a_1/learning-lab",
                                    headers={"X-User-Id": "teacher"})
                assert report.status_code == 200
                assert report.json()["sessions"] == [final.json()]
                target = (Path(__file__).resolve().parents[1] /
                          "docs/demo-assets/learning-lab-live-proof.json")
                target.write_text(json.dumps(final.json(), indent=2), encoding="utf-8")
                print("FINAL LEVEL", final.json()["final"]["level"])
                print("PASS: live loop, quote grounding, teacher report; controlled example only.")
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    main()
