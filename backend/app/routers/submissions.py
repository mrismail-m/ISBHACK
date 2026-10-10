import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.deps import ApiError, current_user_id, not_implemented
from app.models.core import Assessment, Submission, User
from app.schemas.core import SubmissionRow, SubmissionSchema, SubmissionUpdate

router = APIRouter(tags=["submissions"])
OWNER = "Ismail"

@router.get("/assessments/{assessment_id}/submissions", response_model=list[SubmissionRow])
def list_submissions(assessment_id: str, session: Session = Depends(get_session)):
    assessment = session.get(Assessment, assessment_id)
    if not assessment:
        raise ApiError(404, "not_found", "Assessment not found")
        
    submissions = session.exec(select(Submission).where(Submission.assessment_id == assessment_id)).all()
    rows = []
    
    # We also need user details
    for i, sub in enumerate(submissions):
        user = session.get(User, sub.student_id)
        rows.append(SubmissionRow(
            submission_id=sub.id,
            label=f"Student {i+1:02d}", # stable anonymous label
            student_id=sub.student_id,
            student_name=user.name if user else "Unknown",
            status=sub.status,
            submitted_at=sub.submitted_at,
            ai_total=None,
            final_total=None,
            max_marks=assessment.max_marks,
            understanding=None,
            score_pct=None,
            score_is_final=False,
            overall_confidence=None,
            flags=[]
        ))
    return rows

@router.post("/assessments/{assessment_id}/submissions", response_model=SubmissionSchema)
def start_submission(
    assessment_id: str, 
    user_id: str | None = Depends(current_user_id), 
    session: Session = Depends(get_session)
):
    if not user_id:
        raise ApiError(401, "unauthorized", "Missing X-User-Id")
        
    # Check if already exists (idempotent)
    existing = session.exec(
        select(Submission)
        .where(Submission.assessment_id == assessment_id)
        .where(Submission.student_id == user_id)
    ).first()
    
    if existing:
        return SubmissionSchema.model_validate(existing, from_attributes=True)
        
    sub = Submission(
        id=f"s_{uuid.uuid4().hex[:8]}",
        assessment_id=assessment_id,
        student_id=user_id,
        content_md="",
        answers=[],
        status="draft",
        started_at=datetime.now(UTC)
    )
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return SubmissionSchema.model_validate(sub, from_attributes=True)

@router.get("/submissions/{submission_id}", response_model=SubmissionSchema)
def get_submission(submission_id: str, session: Session = Depends(get_session)):
    sub = session.get(Submission, submission_id)
    if not sub:
        raise ApiError(404, "not_found", "Submission not found")
    return SubmissionSchema.model_validate(sub, from_attributes=True)

@router.put("/submissions/{submission_id}", response_model=SubmissionSchema)
def save_submission(
    submission_id: str, 
    data: SubmissionUpdate, 
    session: Session = Depends(get_session)
):
    sub = session.get(Submission, submission_id)
    if not sub:
        raise ApiError(404, "not_found", "Submission not found")
        
    if sub.status != "draft":
        raise ApiError(409, "already_submitted", "Submission is already submitted")
        
    if data.content_md is not None:
        sub.content_md = data.content_md
    if data.answers is not None:
        sub.answers = data.answers
        
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return SubmissionSchema.model_validate(sub, from_attributes=True)

@router.post("/submissions/{submission_id}/submit", response_model=SubmissionSchema)
def submit_submission(submission_id: str, session: Session = Depends(get_session)):
    sub = session.get(Submission, submission_id)
    if not sub:
        raise ApiError(404, "not_found", "Submission not found")
        
    if sub.status != "draft":
        raise ApiError(409, "already_submitted", "Submission is already submitted")
        
    sub.status = "submitted"
    sub.submitted_at = datetime.now(UTC)
    session.add(sub)
    session.commit()
    session.refresh(sub)
    
    # Background grading logic would go here if GRADE_ON_SUBMIT=1
    # For now, it just submits successfully.
    return SubmissionSchema.model_validate(sub, from_attributes=True)

@router.post("/submissions/{submission_id}/approve")
def approve_submission(submission_id: str) -> None:
    # Depends on Adeel's grading output
    not_implemented(OWNER)

@router.get("/submissions/{submission_id}/result")
def get_result(submission_id: str) -> None:
    # Depends on grading and viva
    not_implemented(OWNER)
