"""Analytics and grace marks endpoints. Owner: Ismail. Contract: docs/api-contract.md.

Skeleton from Adeel (M0.1): every route returns 501. Ismail replaces this file (M3.3).
"""

from fastapi import APIRouter

from app.deps import not_implemented

router = APIRouter(tags=["analytics"])
OWNER = "Ismail"


@router.get("/assessments/{assessment_id}/stats")
def get_stats(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.get("/classrooms/{classroom_id}/performance")
def get_class_performance(classroom_id: str) -> None:
    not_implemented(OWNER)


@router.get("/classrooms/{classroom_id}/attention")
def get_attention(classroom_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/grace/preview")
def preview_grace(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/grace/apply")
def apply_grace(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.post("/assessments/{assessment_id}/grace/undo")
def undo_grace(assessment_id: str) -> None:
    not_implemented(OWNER)


@router.get("/assessments/{assessment_id}/override-stats")
def get_override_stats(assessment_id: str) -> None:
    not_implemented(OWNER)
