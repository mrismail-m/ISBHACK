"""Add synthetic demo data without deleting existing work or calling an LLM."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, select

from app.db import create_db_and_tables, engine
from app.models.activity import ActivityBatchRecord
from app.models.core import Assessment, Submission, User
from app.models.grading import Grade, VivaSession

ROSTER = json.loads(
    (Path(__file__).resolve().parents[2] / "fixtures/demo/roster.json").read_text()
)


def install_demo(session: Session) -> None:
    template = session.get(Assessment, "a_1")
    if not template:
        raise ValueError("Run python -m app.seed first.")
    for row in ROSTER:
        user = session.get(User, row["user_id"])
        if user:
            user.name = row["name"]
        else:
            user = User(id=row["user_id"], name=row["name"], role="student", classroom_id="cl_1")
        session.add(user)
    for period in range(1, 4):
        aid = f"demo_a_{period}"
        if session.get(Assessment, aid):
            continue
        start = datetime(2026, 9, period * 7, 9, tzinfo=UTC)
        assessment = Assessment.model_validate({
            **template.model_dump(), "id": aid,
            "title": f"Hashing practice {period}", "status": "closed",
            "created_at": start, "due_at": start + timedelta(days=1),
        })
        session.add(assessment)
        for number, row in enumerate(ROSTER, 1):
            sid = f"demo_s_{period}_{number}"
            session_id = f"demo_activity_{period}_{number}"
            events = [{"seq": 0, "t": 0, "k": "start", "from": 0, "to": 0, "text": ""}]
            content = ""
            paragraphs = [
                "# Hash table collisions\n\n"
                "A collision occurs when distinct keys map to one index.\n\n",
                "Chaining stores colliding entries in a list. Open addressing probes another slot. "
                "Load factor controls how often probes collide. "
                "A resized table reduces long probes. "
                "A poor hash function may place many keys in the same bucket. " * 3 + "\n\n",
                "Expected lookup is O(1) with a good hash function and controlled load. "
                "Worst-case lookup is O(n) when all keys collide.\n",
            ]
            for paragraph_index, paragraph in enumerate(paragraphs):
                kind = "paste" if number % 3 == 0 and paragraph_index == 1 else "type"
                pieces = [paragraph] if kind == "paste" else [
                    paragraph[i:i + 24] for i in range(0, len(paragraph), 24)
                ]
                for piece in pieces:
                    seq = len(events)
                    events.append({"seq": seq, "t": seq * (4000 + number * 70), "k": kind,
                                   "from": len(content), "to": len(content), "text": piece})
                    content += piece
            events.append({"seq": len(events), "t": events[-1]["t"] + 1000,
                           "k": "end", "from": 0, "to": 0, "text": ""})
            finish = start + timedelta(milliseconds=events[-1]["t"])
            session.add(Submission(id=sid, assessment_id=aid, student_id=row["user_id"],
                                   content_md=content, answers=[], status="released",
                                   started_at=start, submitted_at=finish))
            session.add(ActivityBatchRecord(submission_id=sid, session_id=session_id,
                                           session_started_at=start, first_seq=0,
                                           last_seq=events[-1]["seq"], events=events))
            level = 1 + (number + period) % 4
            marks = level * 1.25
            criteria = [{"criterion_id": c["id"], "level": level, "ai_marks": marks,
                         "final_marks": marks, "confidence": 0.8,
                         "reasoning": "Synthetic demonstration score, not an evaluation.",
                         "minor_errors": 0, "ambiguous": False, "teacher_note": None,
                         "evidence": [{"quote": "A collision occurs", "start": 25,
                                       "end": 43, "verified": True}]}
                        for c in template.rubric["criteria"]]
            session.add(Grade(id=f"demo_g_{period}_{number}", submission_id=sid,
                              status="approved", strictness_used="normal",
                              prompt_version="synthetic-demo", model_id="synthetic-demo",
                              max_marks=20, criteria=criteria, ai_total=marks * 4,
                              final_total=marks * 4, overall_confidence=0.8,
                              feedback={"mode": "full", "strengths": [], "improvements": [],
                                        "next_step": "Compare average and worst-case lookup.",
                                        "topics": []}, teacher_note="Synthetic demo data",
                              approved_at=finish, released_at=finish))
            session.add(VivaSession(id=f"demo_v_{period}_{number}", submission_id=sid,
                                    status="done", understanding=((number + period) % 5) / 4,
                                    started_at=finish, finished_at=finish + timedelta(minutes=3)))
    session.commit()
    enrich_presentation(session)


def enrich_presentation(session: Session) -> None:
    """Populate missing A1 examples and overrides, preserving existing submissions."""
    template = session.get(Assessment, "a_1")
    for period in range(1, 4):
        assessment = session.get(Assessment, f"demo_a_{period}")
        assessment.title = f"Hashing practice {period}"
        session.add(assessment)
    for number, row in enumerate(ROSTER, 1):
        source_id = f"demo_s_3_{number}"
        source = session.get(Submission, source_id)
        source_grade = session.get(Grade, f"demo_g_3_{number}")
        for period in range(1, 4):
            grade = session.get(Grade, f"demo_g_{period}_{number}")
            if grade.teacher_note == "Synthetic demo data":
                criteria = [dict(c) for c in grade.criteria]
                if number % 5 == 0:
                    c = criteria[0]
                    c["final_marks"] = c["ai_marks"] + (-1 if c["ai_marks"] >= 5 else 1)
                    c["teacher_note"] = "Adjusted for the explanation of collision handling."
                for c in criteria:
                    c["reasoning"] = "Explains collision handling and lookup complexity."
                grade.criteria = criteria
                grade.final_total = sum(c["final_marks"] for c in criteria)
                grade.teacher_note = "Reviewed against the rubric."
                session.add(grade)
        existing = session.exec(select(Submission).where(
            Submission.assessment_id == "a_1", Submission.student_id == row["user_id"]
        )).first()
        if existing:
            continue
        sid = f"demo_s_4_{number}"
        start = template.created_at + timedelta(hours=2)
        finish = start + (source.submitted_at - source.started_at)
        session.add(Submission.model_validate({**source.model_dump(), "id": sid,
                                              "assessment_id": "a_1",
                                              "started_at": start, "submitted_at": finish}))
        session.add(Grade.model_validate({**source_grade.model_dump(),
                                         "id": f"demo_g_4_{number}", "submission_id": sid,
                                         "approved_at": finish, "released_at": finish}))
        viva = session.get(VivaSession, f"demo_v_3_{number}")
        session.add(VivaSession.model_validate({**viva.model_dump(),
                                               "id": f"demo_v_4_{number}", "submission_id": sid,
                                               "started_at": finish,
                                               "finished_at": finish + timedelta(minutes=3)}))
        record = session.exec(select(ActivityBatchRecord).where(
            ActivityBatchRecord.submission_id == source_id
        )).first()
        session.add(ActivityBatchRecord.model_validate({
            **record.model_dump(), "id": f"demo_batch_4_{number}",
            "submission_id": sid, "session_id": f"demo_activity_4_{number}",
            "session_started_at": start,
        }))
    # Students still have an open assessment for new writing after A1 is populated.
    if not session.get(Assessment, "a_write"):
        session.add(Assessment.model_validate({
            **template.model_dump(), "id": "a_write", "title": "A2: Collision strategies",
            "status": "open",
        }))
    session.commit()


if __name__ == "__main__":
    create_db_and_tables()
    with Session(engine) as session:
        install_demo(session)
    print("Presentation data installed; existing work preserved.")
