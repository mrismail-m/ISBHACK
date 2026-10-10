"""Users and assessments endpoints. Owner: Ismail. Contract: docs/api-contract.md.

Skeleton from Adeel (M0.1): every route returns 501. Ismail replaces this file (M0.3, M1.3).
"""

from fastapi import APIRouter

from app.deps import not_implemented

router = APIRouter(tags=["assessments"])
OWNER = "Ismail"


@router.get("/users")
def list_users() -> None:
    not_implemented(OWNER)


@router.get("/me")
def get_me() -> None:
    not_implemented(OWNER)


@router.get("/assessments")
def list_assessments() -> None:
    not_implemented(OWNER)


@router.post("/assessments")
def create_assessment() -> None:
    not_implemented(OWNER)


@router.get("/assessments/{assessment_id}")
def get_assessment(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.patch("/assessments/{assessment_id}")
def update_assessment(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/publish")
def publish_assessment(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/close")
def close_assessment(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.get("/assessments/{assessment_id}/questions")
def list_questions(assessment_id: str) -> None:
    not_implemented(OWNER)
