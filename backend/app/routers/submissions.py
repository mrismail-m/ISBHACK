"""Submissions and results endpoints. Owner: Ismail. Contract: docs/api-contract.md.

Skeleton from Adeel (M0.1): every route returns 501. Ismail replaces this file (M1.3, M2.4).
"""

from fastapi import APIRouter

from app.deps import not_implemented

router = APIRouter(tags=["submissions"])
OWNER = "Ismail"


@router.get("/assessments/{assessment_id}/submissions")
def list_submissions(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/submissions")
def start_submission(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: str) -> None:
    not_implemented(OWNER)


@router.put("/submissions/{submission_id}")
def save_submission(submission_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/submit")
def submit_submission(submission_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/approve")
def approve_submission(submission_id: str) -> None:
    not_implemented(OWNER)


@router.get("/submissions/{submission_id}/result")
def get_result(submission_id: str) -> None:
    not_implemented(OWNER)
