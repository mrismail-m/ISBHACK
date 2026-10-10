"""Writing activity endpoints and access checks. Owner: Majid."""

from collections.abc import Generator
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.deps import ApiError
from app.models.activity import ActivityBatchRecord
from app.models.core import Assessment, Submission, User
from app.schemas.activity import (
    NON_EDIT,
    ActivityBatch,
    ActivityEvents,
    ActivitySummary,
    SessionEvent,
    SessionInfo,
)
from app.services.activity_summary import summarize_activity, utc

router = APIRouter(tags=["activity"])


def activity_session(
    session: Annotated[Session, Depends(get_session)],
) -> Generator[Session, None, None]:
    # Own table only. Existing core tables are created by Ismail's seed.
    ActivityBatchRecord.__table__.create(session.get_bind(), checkfirst=True)
    yield session


Db = Annotated[Session, Depends(activity_session)]
UserId = Annotated[str | None, Header(alias="X-User-Id")]


def access(session: Session, submission_id: str, user_id: str | None, *, write: bool = False):
    user = session.get(User, user_id) if user_id else None
    if not user:
        raise ApiError(403, "forbidden", "Choose a seeded user first.")
    submission = session.get(Submission, submission_id)
    if not submission:
        raise ApiError(404, "not_found", "Submission not found.")
    assessment = session.get(Assessment, submission.assessment_id)
    own = user.role == "student" and user.id == submission.student_id
    teacher = user.role == "teacher" and assessment and user.classroom_id == assessment.classroom_id
    if not own and (write or not teacher):
        raise ApiError(403, "forbidden", "You cannot access this writing record.")
    if not assessment:
        raise ApiError(404, "not_found", "Assessment not found.")
    return submission, assessment


def load_activity(session: Session, submission_id: str) -> ActivityEvents:
    records = session.exec(
        select(ActivityBatchRecord).where(ActivityBatchRecord.submission_id == submission_id)
    ).all()
    sessions = {record.session_id: utc(record.session_started_at) for record in records}
    unique: dict[tuple[str, int], SessionEvent] = {}
    for record in records:
        for event in record.events:
            unique.setdefault(
                (record.session_id, event["seq"]),
                SessionEvent(**event, session_id=record.session_id),
            )
    return ActivityEvents(
        sessions=[
            SessionInfo(session_id=id_, started_at=start)
            for id_, start in sorted(sessions.items(), key=lambda pair: (pair[1], pair[0]))
        ],
        events=sorted(unique.values(), key=lambda e: (sessions[e.session_id], e.session_id, e.seq)),
    )


@router.post("/submissions/{submission_id}/activity")
def ingest_activity(
    submission_id: str, batch: ActivityBatch, session: Db, x_user_id: UserId = None
):
    submission, assessment = access(session, submission_id, x_user_id, write=True)
    activity = load_activity(session, submission_id)
    previous = [e for e in activity.events if e.session_id == batch.session_id]
    last = max((e.seq for e in previous), default=-1)
    existing = next((s for s in activity.sessions if s.session_id == batch.session_id), None)
    if existing and utc(existing.started_at) != utc(batch.session_started_at):
        raise ApiError(409, "conflict", "Session start time cannot change.")
    fresh = [e for e in batch.events if e.seq > last]
    if not fresh:
        return {"received": 0, "last_seq": last}
    if fresh[0].seq != last + 1 or any(
        b.seq != a.seq + 1 for a, b in zip(fresh, fresh[1:], strict=False)
    ):
        raise ApiError(409, "conflict", "Upload missing events before later events.")
    if last == -1 and fresh[0].k != "start":
        raise ApiError(422, "validation_error", "A session must begin with a start event.")
    if previous and fresh[0].t < previous[-1].t:
        raise ApiError(422, "validation_error", "Event times must be monotonic.")
    if submission.status != "draft" and any(e.k not in NON_EDIT for e in fresh):
        raise ApiError(409, "already_submitted", "Submitted work cannot accept new edits.")
    if not existing:
        activity.sessions.append(
            SessionInfo(session_id=batch.session_id, started_at=batch.session_started_at)
        )
    activity.events.extend(
        SessionEvent(**e.model_dump(by_alias=True), session_id=batch.session_id) for e in fresh
    )
    try:
        summarize_activity(submission_id, activity, assessment.paste_flag_chars)
    except ValueError as exc:
        raise ApiError(422, "validation_error", str(exc)) from exc
    record = ActivityBatchRecord(
        submission_id=submission_id,
        session_id=batch.session_id,
        session_started_at=utc(batch.session_started_at),
        first_seq=fresh[0].seq,
        last_seq=fresh[-1].seq,
        events=[e.model_dump(by_alias=True) for e in fresh],
    )
    session.add(record)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ApiError(409, "conflict", "Another upload arrived. Retry the same batch.") from exc
    return {"received": len(fresh), "last_seq": fresh[-1].seq}


@router.get("/submissions/{submission_id}/activity/events", response_model=ActivityEvents)
def get_activity_events(submission_id: str, session: Db, x_user_id: UserId = None):
    access(session, submission_id, x_user_id)
    return load_activity(session, submission_id)


@router.get("/submissions/{submission_id}/activity/summary", response_model=ActivitySummary)
def get_activity_summary(
    submission_id: str,
    session: Db,
    x_user_id: UserId = None,
    bucket: Literal["auto", "minute", "hour"] = "auto",
):
    _, assessment = access(session, submission_id, x_user_id)
    return summarize_activity(
        submission_id, load_activity(session, submission_id), assessment.paste_flag_chars, bucket
    )


@router.post("/submissions/{submission_id}/activity/paste-declaration")
def declare_paste(submission_id: str) -> None:
    raise ApiError(501, "not_implemented", "Paste declaration is P2, deferred until P0 is done.")
