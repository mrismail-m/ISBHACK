"""Student learning loop and teacher evidence, independent of grading."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.ai.learning_lab import LabPlan, adapt_recovery, generate_plan, observe
from app.config import get_settings
from app.db import get_session
from app.deps import ApiError, current_user_id
from app.models.core import Assessment, User
from app.models.learning_lab import LearningLabSession
from app.routers.activity import access
from app.schemas.learning_lab import LabAnswer, LabObservation, LabReport, LabState

router = APIRouter(tags=["learning-lab"])
Db = Annotated[Session, Depends(get_session)]
UserId = Annotated[str | None, Depends(current_user_id)]


def state(row: LearningLabSession) -> LabState:
    plan = LabPlan.model_validate(row.plan)
    return LabState(
        id=row.id, submission_id=row.submission_id, assessment_id=row.assessment_id,
        concept=plan.concept, anchor_quote=plan.anchor_quote, phase=row.phase,
        challenge=plan.challenge,
        recovery=plan.recovery if row.phase != "challenge" else None,
        initial_answer=row.initial_answer, recovery_answer=row.recovery_answer,
        initial=LabObservation.model_validate(row.initial) if row.initial else None,
        final=LabObservation.model_validate(row.final) if row.final else None,
        mode=row.mode, created_at=row.created_at,
    )


def require_row(session: Session, submission_id: str) -> LearningLabSession:
    row = session.get(LearningLabSession, f"lab_{submission_id}")
    if row is None:
        raise ApiError(404, "not_found", "Start the Learning Lab first.")
    return row


@router.get("/submissions/{submission_id}/learning-lab", response_model=LabState)
def get_lab(submission_id: str, session: Db, user_id: UserId) -> LabState:
    access(session, submission_id, user_id)
    return state(require_row(session, submission_id))


@router.post("/submissions/{submission_id}/learning-lab/start", response_model=LabState)
def start_lab(submission_id: str, session: Db, user_id: UserId) -> LabState:
    submission, assessment = access(session, submission_id, user_id, write=True)
    existing = session.get(LearningLabSession, f"lab_{submission_id}")
    if existing:
        return state(existing)
    if submission.status == "draft" or not submission.content_md.strip():
        raise ApiError(409, "conflict", "Submit your written assignment before starting.")
    plan = generate_plan(submission.content_md, assessment.instructions_md, assessment.topics)
    row = LearningLabSession(
        id=f"lab_{submission_id}", submission_id=submission_id,
        assessment_id=assessment.id, plan=plan.model_dump(),
        mode="fixture" if get_settings().mock_llm else "live",
        created_at=datetime.now(UTC).isoformat(),
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return state(require_row(session, submission_id))
    session.refresh(row)
    return state(row)


@router.post("/submissions/{submission_id}/learning-lab/answer", response_model=LabState)
def answer_lab(
    submission_id: str, body: LabAnswer, session: Db, user_id: UserId,
) -> LabState:
    access(session, submission_id, user_id, write=True)
    row = require_row(session, submission_id)
    stored = row.initial_answer if body.phase == "challenge" else row.recovery_answer
    if stored and stored == body.answer_text:
        return state(row)  # safe replay after a lost HTTP response
    if row.phase != body.phase:
        raise ApiError(409, "conflict", "This step is already completed. Refresh to continue.")
    plan = LabPlan.model_validate(row.plan)
    result = observe(plan, body.answer_text,
                     recovery=body.phase == "recovery")
    if body.phase == "challenge":
        plan = adapt_recovery(plan, result)
    values = (
        {"phase": "recovery", "initial_answer": body.answer_text,
         "initial": result.model_dump(), "plan": plan.model_dump()}
        if body.phase == "challenge" else
        {"phase": "complete", "recovery_answer": body.answer_text,
         "final": result.model_dump()}
    )
    changed = session.execute(
        update(LearningLabSession).where(LearningLabSession.id == row.id)
        .where(LearningLabSession.phase == body.phase).values(**values)
        .execution_options(synchronize_session=False)
    )
    session.commit()
    session.refresh(row)
    if changed.rowcount != 1:
        stored = row.initial_answer if body.phase == "challenge" else row.recovery_answer
        if stored != body.answer_text:
            raise ApiError(409, "conflict", "Another answer was saved. Refresh to continue.")
    return state(row)


@router.get("/assessments/{assessment_id}/learning-lab", response_model=LabReport)
def report(assessment_id: str, session: Db, user_id: UserId) -> LabReport:
    user = session.get(User, user_id) if user_id else None
    assessment = session.get(Assessment, assessment_id)
    if not user or user.role != "teacher":
        raise ApiError(403, "forbidden", "Only teachers can view class learning evidence.")
    if not assessment or assessment.classroom_id != user.classroom_id:
        raise ApiError(404, "not_found", "Assessment not found in your classroom.")
    rows = session.exec(
        select(LearningLabSession).where(LearningLabSession.assessment_id == assessment_id)
        .order_by(LearningLabSession.created_at)
    ).all()
    return LabReport(assessment_id=assessment_id, sessions=[state(row) for row in rows])
