"""AI setup and grading endpoints. Owner: Adeel. Contract: docs/api-contract.md.

M1.1: grade and get-grade. The rest return 501 until M2.1 and M2.2.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.ai.grader import apply_marks, run_grader
from app.ai.pipeline import get_grade_row, grade_submission_by_id, rubric_of, to_schema
from app.ai.rubric import draft_rubric as generate_rubric_draft
from app.ai.strictness import STRICTNESS_ORDER
from app.db import get_session
from app.deps import ApiError, not_implemented
from app.models.core import Assessment, Submission
from app.schemas.grading import (
    GradeRequest,
    GradeSchema,
    PreviewCriterion,
    PreviewLevel,
    Rubric,
    RubricDraftRequest,
    StrictnessPreview,
    StrictnessPreviewRequest,
)

SessionDep = Annotated[Session, Depends(get_session)]
router = APIRouter(tags=["grading"])
OWNER = "Adeel"


@router.post("/assessments/{assessment_id}/rubric/draft", response_model=Rubric)
def draft_rubric_route(assessment_id: str, session: SessionDep, body: RubricDraftRequest) -> Rubric:
    assessment = session.get(Assessment, assessment_id)
    if not assessment:
        raise ApiError(404, "not_found", "Assessment not found.")
    return generate_rubric_draft(assessment, notes=body.notes, key=assessment_id)


@router.post("/assessments/{assessment_id}/strictness/preview", response_model=StrictnessPreview)
def preview_strictness(
    assessment_id: str, session: SessionDep, body: StrictnessPreviewRequest
) -> StrictnessPreview:
    assessment = session.get(Assessment, assessment_id)
    if not assessment:
        raise ApiError(404, "not_found", "Assessment not found.")
    rubric = rubric_of(assessment)

    result = run_grader(
        content_md=body.answer_text,
        title=assessment.title,
        instructions_md=assessment.instructions_md,
        model_answer_md=assessment.model_answer_md,
        rubric=rubric,
        key=assessment.id,
    )

    levels = []
    for strictness in STRICTNESS_ORDER:
        criteria_grades = apply_marks(result, rubric=rubric, strictness=strictness)
        total = sum(c.ai_marks for c in criteria_grades)
        preview_criteria = [
            PreviewCriterion(criterion_id=c.criterion_id, marks=c.ai_marks) for c in criteria_grades
        ]
        levels.append(
            PreviewLevel(
                strictness=strictness,  # type: ignore[arg-type]
                total=total,
                criteria=preview_criteria,
            )
        )

    return StrictnessPreview(levels=levels, note="One grading pass, four strictness policies.")


@router.post("/submissions/{submission_id}/grade", response_model=GradeSchema)
def grade_submission(
    submission_id: str,
    session: SessionDep,
    body: GradeRequest | None = None,
) -> GradeSchema:
    return grade_submission_by_id(session, submission_id)


@router.get("/submissions/{submission_id}/grade", response_model=GradeSchema)
def get_grade(submission_id: str, session: SessionDep) -> GradeSchema:
    row = get_grade_row(session, submission_id)
    if row is None:
        if session.get(Submission, submission_id) is None:
            raise ApiError(404, "not_found", "Submission not found.")
        raise ApiError(404, "not_found", "This submission has not been graded yet.")
    return to_schema(row)


@router.post("/assessments/{assessment_id}/grade-all")
def grade_all(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.get("/assessments/{assessment_id}/grading-status")
def grading_status(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/feedback/regenerate")
def regenerate_feedback(submission_id: str) -> None:
    not_implemented(OWNER)
