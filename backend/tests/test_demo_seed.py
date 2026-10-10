"""Demo data must remain coherent, repeatable and independent of real marks."""

from sqlmodel import select

from app.demo_seed import ROSTER, install_demo
from app.models.activity import ActivityBatchRecord
from app.models.core import Submission, User
from app.models.grading import Grade
from app.routers.activity import load_activity
from app.schemas.grading import GradeSchema
from app.services.activity_summary import summarize_activity
from app.services.analytics import get_attention, get_class_performance
from tests.conftest import make_assessment


def test_demo_seed_is_idempotent_and_replay_matches(db):
    db.add(make_assessment())
    db.commit()
    install_demo(db)
    install_demo(db)
    assert len(ROSTER) == len({row["reg_no"] for row in ROSTER}) == 50
    assert len(db.exec(select(User)).all()) == 50
    assert len(db.exec(select(Submission)).all()) == 150
    assert len(db.exec(select(ActivityBatchRecord)).all()) == 150
    for grade in db.exec(select(Grade)).all():
        GradeSchema.model_validate(grade.model_dump())
        submission = db.get(Submission, grade.submission_id)
        events = load_activity(db, submission.id)
        summary = summarize_activity(submission.id, events)
        assert summary.final_chars == len(submission.content_md)
        doc = ""
        for event in events.events:
            doc = doc[:event.from_] + event.text + doc[event.to:]
        assert doc == submission.content_md
        assert summary.heatmap
        for criterion in grade.criteria:
            for evidence in criterion["evidence"]:
                assert submission.content_md[evidence["start"]:evidence["end"]] == evidence["quote"]
    assert summarize_activity("demo_s_3_3", load_activity(db, "demo_s_3_3")).pasted_pct > 50
    assert summarize_activity("demo_s_3_1", load_activity(db, "demo_s_3_1")).pasted_pct == 0


def test_pending_work_is_not_a_zero_score_or_falling_trend(db):
    db.add(make_assessment())
    db.commit()
    install_demo(db)
    # The open, unsubmitted assessment must not add zero to a student's history.
    performance = get_class_performance(db, "cl_1")
    assert len(performance.assessments) == 3
    assert all(len(student.scores_pct) == 3 for student in performance.students)
    row = next(student for student in get_attention(db, "cl_1")
               if student.student_id == "u_student_3")
    assert row.recent_scores_pct[-1] == 60
    assert "below_pass_recent" not in row.reasons
    assert "falling_trend" not in row.reasons
    assert row.last_understanding == 0.25
