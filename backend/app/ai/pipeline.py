"""Grading orchestration: grade one submission and save it. Task: M1.1.

`grade_submission_by_id` is the single entry point. The grading router calls it, and Ismail's
submit route can call it for GRADE_ON_SUBMIT (see docs/progress.md, "Needs from others").
"""

from sqlmodel import Session, select

from app.ai.feedback import starter_feedback
from app.ai.grader import apply_marks, run_grader
from app.deps import ApiError
from app.models.core import Assessment, Submission
from app.models.grading import Grade
from app.schemas.grading import GradeSchema, Rubric


def get_grade_row(session: Session, submission_id: str) -> Grade | None:
    return session.exec(select(Grade).where(Grade.submission_id == submission_id)).first()


def to_schema(row: Grade) -> GradeSchema:
    return GradeSchema.model_validate(row, from_attributes=True)


def rubric_of(assessment: Assessment) -> Rubric:
    if not assessment.rubric or not assessment.rubric.get("criteria"):
        raise ApiError(409, "conflict", "The assessment has no rubric yet.")
    return Rubric.model_validate(assessment.rubric)


def grade_submission_by_id(session: Session, submission_id: str) -> GradeSchema:
    """Grade a submitted piece of work, save the AI draft, and return it.

    Raises ApiError: 404 (unknown submission), 409 (not submitted, or already approved).
    May raise LLMError (the app maps it to 502 `llm_unavailable`).
    """
    sub = session.get(Submission, submission_id)
    if sub is None:
        raise ApiError(404, "not_found", "Submission not found.")
    assessment = session.get(Assessment, sub.assessment_id)
    if assessment is None:
        raise ApiError(404, "not_found", "Assessment not found.")
    if sub.status == "draft":
        raise ApiError(409, "conflict", "The student has not submitted this work yet.")

    existing = get_grade_row(session, submission_id)
    if existing is not None and existing.status == "approved":
        raise ApiError(409, "conflict", "This grade is approved and cannot be regraded.")

    rubric = rubric_of(assessment)
    result = run_grader(
        content_md=sub.content_md,
        title=assessment.title,
        instructions_md=assessment.instructions_md,
        model_answer_md=assessment.model_answer_md,
        rubric=rubric,
        key=sub.id,
    )
    criteria = apply_marks(result, rubric=rubric, strictness=assessment.strictness)
    total = sum(c.ai_marks for c in criteria)
    feedback = starter_feedback(
        mode=assessment.feedback_mode,  # type: ignore[arg-type]
        rubric=rubric,
        criteria=criteria,
    )
    grade = GradeSchema(
        id=existing.id if existing else f"g_{sub.id}",
        submission_id=sub.id,
        status="ai_draft",
        strictness_used=assessment.strictness,  # type: ignore[arg-type]
        prompt_version=result.prompt_version,
        model_id=result.model_id,
        max_marks=assessment.max_marks,
        criteria=criteria,
        ai_total=total,
        final_total=total,
        overall_confidence=result.overall_confidence,
        grader_flags=result.flags,
        feedback=feedback,
    )

    data = grade.model_dump(mode="json")
    row = existing or Grade(**{**data, "criteria": [], "feedback": {}})
    for name in (
        "status",
        "strictness_used",
        "prompt_version",
        "model_id",
        "max_marks",
        "criteria",
        "ai_total",
        "final_total",
        "overall_confidence",
        "grader_flags",
        "feedback",
    ):
        setattr(row, name, data[name])
    session.add(row)
    if sub.status == "submitted":
        sub.status = "graded"
        session.add(sub)
    session.commit()
    session.refresh(row)
    return to_schema(row)
