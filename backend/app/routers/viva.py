"""Viva endpoints. Owner: Adeel. Contract: docs/api-contract.md. Task: M3.1.

Start, answer and finish are for the student. GET viva is for teachers only (no real auth:
the X-User-Id header must name a seeded teacher).
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.ai.viva_service import finish_viva, record_answer, start_viva, viva_detail
from app.db import get_session
from app.deps import ApiError, current_user_id
from app.models.core import User
from app.schemas.viva import VivaAnswer, VivaAnswerResponse, VivaDetail, VivaResult, VivaStart

SessionDep = Annotated[Session, Depends(get_session)]
UserIdDep = Annotated[str | None, Depends(current_user_id)]
router = APIRouter(tags=["viva"])


@router.post("/submissions/{submission_id}/viva/start", response_model=VivaStart)
def start(submission_id: str, session: SessionDep) -> VivaStart:
    return start_viva(session, submission_id)


@router.post("/submissions/{submission_id}/viva/answer", response_model=VivaAnswerResponse)
def answer(submission_id: str, body: VivaAnswer, session: SessionDep) -> VivaAnswerResponse:
    return record_answer(session, submission_id, body)


@router.post("/submissions/{submission_id}/viva/finish", response_model=VivaResult)
def finish(submission_id: str, session: SessionDep) -> VivaResult:
    return finish_viva(session, submission_id)


@router.get("/submissions/{submission_id}/viva", response_model=VivaDetail)
def get_viva(submission_id: str, session: SessionDep, user_id: UserIdDep) -> VivaDetail:
    user = session.get(User, user_id) if user_id else None
    if user is None or user.role != "teacher":
        raise ApiError(403, "forbidden", "Only teachers can read viva answers.")
    return viva_detail(session, submission_id)
