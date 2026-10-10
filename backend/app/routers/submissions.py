import math
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_session
from app.deps import ApiError, current_user_id
from app.models.core import Assessment, Submission, User
from app.models.grading import Grade, VivaSession
from app.routers.activity import access, load_activity
from app.schemas.core import (
    ApproveRequest,
    StudentResult,
    SubmissionRow,
    SubmissionSchema,
    SubmissionUpdate,
)
from app.schemas.grading import GradeSchema
from app.services.activity_summary import summarize_activity
from app.services.flags import compute_flags
from app.services.scoring import compute_final_score

SESSION_DEPENDENCY = Depends(get_session)
UserIdDep = Annotated[str | None, Depends(current_user_id)]

router = APIRouter(tags=["submissions"])


def require_teacher(session: Session, assessment: Assessment, user_id: str | None):
    user = session.get(User, user_id) if user_id else None
    if not user or user.role != "teacher" or user.classroom_id != assessment.classroom_id:
        raise ApiError(403, "forbidden", "Only this classroom's teacher can review submissions.")

@router.get("/assessments/{assessment_id}/submissions", response_model=list[SubmissionRow])
def list_submissions(assessment_id: str, user_id: UserIdDep, session: Session = SESSION_DEPENDENCY):
    assessment = session.get(Assessment, assessment_id)
    if not assessment:
        raise ApiError(404, "not_found", "Assessment not found")

    require_teacher(session, assessment, user_id)
    submissions = session.exec(
        select(Submission).where(
            Submission.assessment_id == assessment_id, Submission.status != "draft"
        )
    ).all()
    rows = []

    for i, sub in enumerate(submissions):
        user = session.get(User, sub.student_id)
        
        grade = session.exec(select(Grade).where(Grade.submission_id == sub.id)).first()
        viva = session.exec(select(VivaSession).where(VivaSession.submission_id == sub.id)).first()
        
        try:
            activity = load_activity(session, sub.id)
            activity_summary = summarize_activity(
                sub.id, activity, paste_flag_chars=assessment.paste_flag_chars
            )
        except Exception:
            activity_summary = None

        flags = compute_flags(assessment, grade, viva, activity_summary)
        final_score_dict = compute_final_score(assessment, grade, viva, session)

        rows.append(
            SubmissionRow(
                submission_id=sub.id,
                label=f"Student {i+1:02d}",
                student_id=sub.student_id,
                student_name=user.name if user else "Unknown",
                status=sub.status,
                submitted_at=sub.submitted_at,
                ai_total=grade.ai_total if grade else None,
                final_total=grade.final_total if grade else None,
                max_marks=assessment.max_marks,
                understanding=final_score_dict.get("understanding"),
                score_pct=final_score_dict.get("final_pct"),
                score_is_final=grade.status == "approved" if grade else False,
                overall_confidence=grade.overall_confidence if grade else None,
                flags=flags,
            )
        )
    return rows


@router.post("/assessments/{assessment_id}/submissions", response_model=SubmissionSchema)
def start_submission(
    assessment_id: str,
    user_id: str | None = Depends(current_user_id),
    session: Session = SESSION_DEPENDENCY,
):
    if not user_id:
        raise ApiError(401, "unauthorized", "Missing X-User-Id")

    user = session.get(User, user_id)
    assessment = session.get(Assessment, assessment_id)
    if not assessment:
        raise ApiError(404, "not_found", "Assessment not found")
    if not user or user.role != "student" or user.classroom_id != assessment.classroom_id:
        raise ApiError(403, "forbidden", "Only students in this classroom can start work.")
    existing = session.exec(
        select(Submission)
        .where(Submission.assessment_id == assessment_id)
        .where(Submission.student_id == user_id)
    ).first()

    if existing:
        return SubmissionSchema.model_validate(existing, from_attributes=True)

    if assessment.status != "open":
        raise ApiError(409, "conflict", "This assessment is not open.")
    sub = Submission(
        id=f"s_{uuid.uuid4().hex[:8]}",
        assessment_id=assessment_id,
        student_id=user_id,
        content_md="",
        answers=[],
        status="draft",
        started_at=datetime.now(UTC),
    )
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return SubmissionSchema.model_validate(sub, from_attributes=True)


@router.get("/submissions/{submission_id}", response_model=SubmissionSchema)
def get_submission(submission_id: str, user_id: UserIdDep, session: Session = SESSION_DEPENDENCY):
    access(session, submission_id, user_id)
    sub = session.get(Submission, submission_id)
    if not sub:
        raise ApiError(404, "not_found", "Submission not found")
    return SubmissionSchema.model_validate(sub, from_attributes=True)


@router.put("/submissions/{submission_id}", response_model=SubmissionSchema)
def save_submission(
    submission_id: str, data: SubmissionUpdate, user_id: UserIdDep,
    session: Session = SESSION_DEPENDENCY
):
    access(session, submission_id, user_id, write=True)
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
def submit_submission(
    submission_id: str, user_id: UserIdDep, session: Session = SESSION_DEPENDENCY
):
    access(session, submission_id, user_id, write=True)
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
    
    if get_settings().grade_on_submit:
        from app.ai.pipeline import grade_submission_by_id
        grade_submission_by_id(session, sub.id)

    return SubmissionSchema.model_validate(sub, from_attributes=True)


@router.post("/submissions/{submission_id}/approve", response_model=GradeSchema)
def approve_submission(
    submission_id: str, req: ApproveRequest, user_id: UserIdDep,
    session: Session = SESSION_DEPENDENCY
):
    _, assessment = access(session, submission_id, user_id)
    require_teacher(session, assessment, user_id)
    sub = session.get(Submission, submission_id)
    if not sub:
        raise ApiError(404, "not_found", "Submission not found")

    grade = session.exec(select(Grade).where(Grade.submission_id == submission_id)).first()
    if not grade:
        raise ApiError(404, "not_found", "Grade not found")

    assessment = session.get(Assessment, sub.assessment_id)
    if not assessment:
        raise ApiError(404, "not_found", "Assessment not found")
    limits = {c["id"]: c["max_marks"] for c in assessment.rubric["criteria"]}
    graded_ids = {c["criterion_id"] for c in grade.criteria}
    seen = set()
    for override in req.criteria_overrides:
        criterion_id = override.get("criterion_id")
        marks = override.get("marks")
        if (
            not isinstance(criterion_id, str)
            or criterion_id not in limits
            or criterion_id not in graded_ids
            or criterion_id in seen
            or isinstance(marks, bool)
            or not isinstance(marks, int | float)
            or not math.isfinite(marks)
            or not 0 <= marks <= limits[criterion_id]
        ):
            raise ApiError(
                422, "validation_error", "Override must be within the criterion's marks."
            )
        seen.add(criterion_id)

    new_criteria = list(grade.criteria)
    for override in req.criteria_overrides:
        for crit in new_criteria:
            if crit["criterion_id"] == override["criterion_id"]:
                crit["final_marks"] = override["marks"]
                if "note" in override:
                    crit["teacher_note"] = override["note"]
    grade.criteria = new_criteria

    grade.final_total = sum(c.get("final_marks", c.get("ai_marks", 0)) for c in grade.criteria)

    if req.teacher_note is not None:
        grade.teacher_note = req.teacher_note

    if req.feedback_edits:
        new_feedback = dict(grade.feedback)
        for k, v in req.feedback_edits.items():
            new_feedback[k] = v
        grade.feedback = new_feedback
            
    grade.status = "approved"
    grade.approved_at = datetime.now(UTC)
    sub.status = "approved"

    should_release = req.release or (assessment and assessment.release_mode == "auto")
    if should_release:
        grade.released_at = datetime.now(UTC)
        sub.status = "released"

    session.add(grade)
    session.add(sub)
    session.commit()
    session.refresh(grade)
    return GradeSchema.model_validate(grade, from_attributes=True)


@router.get("/submissions/{submission_id}/result", response_model=StudentResult)
def get_result(submission_id: str, user_id: UserIdDep, session: Session = SESSION_DEPENDENCY):
    access(session, submission_id, user_id)
    sub = session.get(Submission, submission_id)
    if not sub:
        raise ApiError(404, "not_found", "Submission not found")

    grade = session.exec(select(Grade).where(Grade.submission_id == submission_id)).first()
    if not grade or not grade.released_at:
        raise ApiError(403, "not_released", "Grade is not released yet")

    assessment = session.get(Assessment, sub.assessment_id)
    viva = session.exec(
        select(VivaSession).where(VivaSession.submission_id == submission_id)
    ).first()

    final_score_dict = compute_final_score(assessment, grade, viva, session)

    return StudentResult(
        submission_id=submission_id,
        assessment_id=sub.assessment_id,
        max_marks=assessment.max_marks,
        work_marks=final_score_dict.get("work_marks", 0),
        understanding=final_score_dict.get("understanding"),
        viva_weight=final_score_dict.get("viva_weight", 0),
        final_marks=final_score_dict.get("final_marks", 0),
        grace_marks=final_score_dict.get("grace_marks", 0),
        final_with_grace=final_score_dict.get("final_with_grace", 0),
        final_pct=final_score_dict.get("final_pct", 0),
        feedback=grade.feedback,
        released_at=grade.released_at
    )
