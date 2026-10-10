"""AI setup and grading endpoints. Owner: Adeel. Contract: docs/api-contract.md.

Skeleton: every route returns 501 until implemented (M1.1, M2.1, M2.2).
"""

from fastapi import APIRouter

from app.deps import not_implemented

router = APIRouter(tags=["grading"])
OWNER = "Adeel"


@router.post("/assessments/{assessment_id}/rubric/draft")
def draft_rubric(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/strictness/preview")
def preview_strictness(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/grade")
def grade_submission(submission_id: str) -> None:
    not_implemented(OWNER)


@router.get("/submissions/{submission_id}/grade")
def get_grade(submission_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/grade-all")
def grade_all(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.get("/assessments/{assessment_id}/grading-status")
def grading_status(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/feedback/regenerate")
def regenerate_feedback(submission_id: str) -> None:
    not_implemented(OWNER)
