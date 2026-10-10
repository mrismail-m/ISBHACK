"""Viva orchestration: start, answer, finish, detail. Task: M3.1.

Understanding is the mean of per-question scores (0, 0.5, 1). A missing, empty or timed-out
answer scores 0 without calling the model. Time, paste and tab data are stored for the teacher
and are never given to the scorer.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from app.ai.viva import excerpt_for, generate_questions, score_answer, understanding_score
from app.deps import ApiError
from app.models.core import Assessment, Submission
from app.models.grading import VivaSession
from app.schemas.viva import (
    VivaAnswer,
    VivaAnswerResponse,
    VivaDetail,
    VivaDetailItem,
    VivaQuestion,
    VivaResult,
    VivaStart,
)

TIMEOUT_GRACE_S = 5  # allows for network delay before an answer counts as timed out
MAX_PARALLEL_SCORES = 3


def _row(session: Session, submission_id: str) -> VivaSession | None:
    return session.exec(
        select(VivaSession).where(VivaSession.submission_id == submission_id)
    ).first()


def _need_row(session: Session, submission_id: str) -> VivaSession:
    row = _row(session, submission_id)
    if row is None:
        raise ApiError(409, "conflict", "The viva has not been started for this submission.")
    return row


def _start_payload(row: VivaSession) -> VivaStart:
    questions = [VivaQuestion.model_validate(q) for q in row.questions]
    return VivaStart(
        session_id=row.id,
        questions=questions,
        total_time_limit_s=sum(q.time_limit_s for q in questions),
    )


def _answered(row: VivaSession) -> int:
    return sum(1 for a in row.answers if str(a.get("answer_text", "")).strip())


def start_viva(session: Session, submission_id: str) -> VivaStart:
    """Create the viva (or resume it) and return the questions. Safe to call twice."""
    sub = session.get(Submission, submission_id)
    if sub is None:
        raise ApiError(404, "not_found", "Submission not found.")
    if sub.status == "draft":
        raise ApiError(409, "conflict", "Submit your work before the viva.")
    assessment = session.get(Assessment, sub.assessment_id)
    if assessment is None:
        raise ApiError(404, "not_found", "Assessment not found.")
    if not assessment.viva_enabled:
        raise ApiError(409, "conflict", "The viva is not enabled for this assessment.")

    existing = _row(session, submission_id)
    if existing is not None:
        if existing.status == "done":
            raise ApiError(409, "conflict", "The viva is already finished.")
        return _start_payload(existing)

    questions = generate_questions(
        content_md=sub.content_md,
        instructions_md=assessment.instructions_md,
        topics=list(assessment.topics or []),
        count=assessment.viva_question_count,
        time_limit_s=assessment.viva_time_limit_s,
        key=sub.id,
    )
    row = VivaSession(
        id=f"v_{sub.id}",
        submission_id=sub.id,
        status="started",
        questions=questions,
        answers=[],
        scores=[],
        understanding=None,
        started_at=datetime.now(UTC),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _start_payload(row)


def record_answer(session: Session, submission_id: str, answer: VivaAnswer) -> VivaAnswerResponse:
    row = _need_row(session, submission_id)
    if row.status == "done":
        raise ApiError(409, "conflict", "The viva is already finished.")
    if answer.question_id not in {q["id"] for q in row.questions}:
        raise ApiError(422, "validation_error", "Unknown question for this viva.")
    # Re-sending an answer for the same question replaces it (retry after a network error).
    kept = [a for a in row.answers if a["question_id"] != answer.question_id]
    kept.append(answer.model_dump())
    row.answers = kept
    session.add(row)
    session.commit()
    answered = _answered(row)
    return VivaAnswerResponse(answered=answered, remaining=len(row.questions) - answered)


def _score_all(row: VivaSession, content_md: str, submission_id: str) -> list[dict[str, Any]]:
    answers = {a["question_id"]: a for a in row.answers}
    results: dict[str, dict[str, Any]] = {}
    to_score: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for q in row.questions:
        a = answers.get(q["id"])
        if a is None or not str(a.get("answer_text", "")).strip():
            results[q["id"]] = {"score": 0.0, "note": "No answer."}
        elif a.get("time_taken_s", 0) > q["time_limit_s"] + TIMEOUT_GRACE_S:
            results[q["id"]] = {"score": 0.0, "note": "Answer arrived after the time limit."}
        else:
            to_score.append((q, a))

    def run(pair: tuple[dict[str, Any], dict[str, Any]]) -> tuple[str, float, str]:
        q, a = pair
        score, note = score_answer(
            question=q["text"],
            work_excerpt=excerpt_for(content_md, q.get("anchor_quote", "")),
            answer_text=a["answer_text"],
            key=f"{submission_id}_{q['id']}",
        )
        return q["id"], score, note

    if to_score:
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SCORES) as pool:
            for qid, score, note in pool.map(run, to_score):
                results[qid] = {"score": score, "note": note}
    return [{"question_id": q["id"], **results[q["id"]]} for q in row.questions]


def finish_viva(session: Session, submission_id: str) -> VivaResult:
    """Score every answer once and save the understanding score. Finishing twice is safe."""
    row = _need_row(session, submission_id)
    total = len(row.questions)
    if row.status == "done":
        return VivaResult(
            understanding=row.understanding or 0.0, answered=_answered(row), total=total
        )
    sub = session.get(Submission, submission_id)
    if sub is None:
        raise ApiError(404, "not_found", "Submission not found.")

    scores = _score_all(row, sub.content_md, submission_id)  # may raise LLMError: retry later
    row.scores = scores
    row.understanding = understanding_score([s["score"] for s in scores])
    row.status = "done"
    row.finished_at = datetime.now(UTC)
    session.add(row)
    session.commit()
    return VivaResult(understanding=row.understanding, answered=_answered(row), total=total)


def viva_detail(session: Session, submission_id: str) -> VivaDetail:
    row = _row(session, submission_id)
    if row is None:
        raise ApiError(404, "not_found", "No viva for this submission.")
    answers = {a["question_id"]: a for a in row.answers}
    scores = {s["question_id"]: s for s in row.scores}
    items = []
    for q in row.questions:
        a = answers.get(q["id"], {})
        s = scores.get(q["id"])
        items.append(
            VivaDetailItem(
                question_id=q["id"],
                text=q["text"],
                answer_text=a.get("answer_text", ""),
                score=s["score"] if s else None,
                note=s["note"] if s else "",
                time_taken_s=a.get("time_taken_s", 0),
                pasted=a.get("pasted", False),
                tab_switches=a.get("tab_switches", 0),
            )
        )
    done = row.status == "done"
    return VivaDetail(
        status="done" if done else "in_progress",
        understanding=row.understanding if done else None,
        items=items,
    )
