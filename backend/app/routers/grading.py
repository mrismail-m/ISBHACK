"""AI setup and grading endpoints. Owner: Adeel. Contract: docs/api-contract.md.

M1.1: grade and get-grade. The rest return 501 until M2.1 and M2.2.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.ai.pipeline import get_grade_row, grade_submission_by_id, to_schema
from app.db import get_session
from app.deps import ApiError, not_implemented
from app.models.core import Submission
from app.schemas.grading import GradeRequest, GradeSchema

SessionDep = Annotated[Session, Depends(get_session)]
router = APIRouter(tags=["grading"])
OWNER = "Adeel"


@router.post("/assessments/{assessment_id}/rubric/draft")
def draft_rubric(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/strictness/preview")
def preview_strictness(assessment_id: str) -> None:
    not_implemented(OWNER)


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
