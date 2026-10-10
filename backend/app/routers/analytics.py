"""Analytics and grace marks endpoints. Owner: Ismail. Contract: docs/api-contract.md.

Skeleton from Adeel (M0.1): every route returns 501. Ismail replaces this file (M3.3).
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.analytics import (
    AssessmentStats,
    AttentionStudent,
    ClassPerformance,
    GraceApplyRequest,
    GracePreview,
    GracePreviewRequest,
    GraceState,
    GraceUndoRequest,
    OverrideStats,
)
from app.services.analytics import (
    get_assessment_stats,
    get_attention,
    get_class_performance,
    get_override_stats,
)
from app.services.grace import (
    apply_grace_marks,
    preview_grace_marks,
    undo_grace_marks,
)

router = APIRouter(tags=["analytics"])
SESSION_DEPENDENCY = Depends(get_session)


@router.get("/assessments/{assessment_id}/stats", response_model=AssessmentStats)
def get_stats(assessment_id: str, session: Session = SESSION_DEPENDENCY):
    return get_assessment_stats(session, assessment_id)


@router.get("/classrooms/{classroom_id}/performance", response_model=ClassPerformance)
def get_class_performance_route(classroom_id: str, session: Session = SESSION_DEPENDENCY):
    return get_class_performance(session, classroom_id)


@router.get("/classrooms/{classroom_id}/attention", response_model=list[AttentionStudent])
def get_attention_route(classroom_id: str, session: Session = SESSION_DEPENDENCY):
    return get_attention(session, classroom_id)


@router.post("/assessments/{assessment_id}/grace/preview", response_model=GracePreview)
def preview_grace(
    assessment_id: str, req: GracePreviewRequest, session: Session = SESSION_DEPENDENCY
):
    return preview_grace_marks(session, assessment_id, req.marks)


@router.post("/assessments/{assessment_id}/grace/apply", response_model=GraceState)
def apply_grace(assessment_id: str, req: GraceApplyRequest, session: Session = SESSION_DEPENDENCY):
    return apply_grace_marks(session, assessment_id, req.marks, req.reason)


@router.post("/assessments/{assessment_id}/grace/undo", response_model=GraceState)
def undo_grace(assessment_id: str, req: GraceUndoRequest, session: Session = SESSION_DEPENDENCY):
    return undo_grace_marks(session, assessment_id, req.entry_id)


@router.get("/assessments/{assessment_id}/override-stats", response_model=OverrideStats)
def get_override_stats_route(assessment_id: str, session: Session = SESSION_DEPENDENCY):
    return get_override_stats(session, assessment_id)
