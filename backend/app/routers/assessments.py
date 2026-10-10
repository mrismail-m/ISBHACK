import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.deps import ApiError, current_user_id
from app.models.core import Assessment, Question, User
from app.schemas.core import AssessmentCreate, AssessmentSchema, QuestionSchema, UserSchema

SESSION_DEPENDENCY = Depends(get_session)

router = APIRouter(tags=["assessments"])


@router.get("/users", response_model=list[UserSchema])
def list_users(session: Session = SESSION_DEPENDENCY):
    users = session.exec(select(User)).all()
    return [UserSchema.model_validate(u, from_attributes=True) for u in users]


@router.get("/me", response_model=UserSchema)
def get_me(user_id: str | None = Depends(current_user_id), session: Session = SESSION_DEPENDENCY):
    if not user_id:
        raise ApiError(401, "unauthorized", "Missing X-User-Id")
    user = session.get(User, user_id)
    if not user:
        raise ApiError(404, "not_found", "User not found")
    return UserSchema.model_validate(user, from_attributes=True)


@router.get("/assessments", response_model=list[AssessmentSchema])
def list_assessments(
    classroom_id: str | None = None,
    status: str | None = None,
    session: Session = SESSION_DEPENDENCY,
):
    query = select(Assessment)
    if classroom_id:
        query = query.where(Assessment.classroom_id == classroom_id)
    if status:
        query = query.where(Assessment.status == status)
    assessments = session.exec(query).all()
    return [AssessmentSchema.model_validate(a, from_attributes=True) for a in assessments]


@router.post("/assessments", response_model=AssessmentSchema)
def create_assessment(data: AssessmentCreate, session: Session = SESSION_DEPENDENCY):
    a = Assessment(
        **data.model_dump(),
        id=f"a_{uuid.uuid4().hex[:8]}",
        status="draft",
        due_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    session.add(a)
    session.commit()
    session.refresh(a)
    return AssessmentSchema.model_validate(a, from_attributes=True)


@router.get("/assessments/{assessment_id}", response_model=AssessmentSchema)
def get_assessment(assessment_id: str, session: Session = SESSION_DEPENDENCY):
    a = session.get(Assessment, assessment_id)
    if not a:
        raise ApiError(404, "not_found", "Assessment not found")
    return AssessmentSchema.model_validate(a, from_attributes=True)


@router.patch("/assessments/{assessment_id}", response_model=AssessmentSchema)
def update_assessment(assessment_id: str, data: dict, session: Session = SESSION_DEPENDENCY):
    a = session.get(Assessment, assessment_id)
    if not a:
        raise ApiError(404, "not_found", "Assessment not found")
    for key, value in data.items():
        if hasattr(a, key):
            setattr(a, key, value)
    session.add(a)
    session.commit()
    session.refresh(a)
    return AssessmentSchema.model_validate(a, from_attributes=True)


@router.post("/assessments/{assessment_id}/publish", response_model=AssessmentSchema)
def publish_assessment(assessment_id: str, session: Session = SESSION_DEPENDENCY):
    a = session.get(Assessment, assessment_id)
    if not a:
        raise ApiError(404, "not_found", "Assessment not found")
    a.status = "open"
    session.add(a)
    session.commit()
    session.refresh(a)
    return AssessmentSchema.model_validate(a, from_attributes=True)


@router.post("/assessments/{assessment_id}/close", response_model=AssessmentSchema)
def close_assessment(assessment_id: str, session: Session = SESSION_DEPENDENCY):
    a = session.get(Assessment, assessment_id)
    if not a:
        raise ApiError(404, "not_found", "Assessment not found")
    a.status = "closed"
    session.add(a)
    session.commit()
    session.refresh(a)
    return AssessmentSchema.model_validate(a, from_attributes=True)


@router.get("/assessments/{assessment_id}/questions", response_model=list[QuestionSchema])
def list_questions(assessment_id: str, session: Session = SESSION_DEPENDENCY):
    questions = session.exec(select(Question).where(Question.assessment_id == assessment_id)).all()
    return [QuestionSchema.model_validate(q, from_attributes=True) for q in questions]
