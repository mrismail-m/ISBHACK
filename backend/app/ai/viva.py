"""Examiner (viva questions) and answer scorer. See docs/ai-spec.md section 6. Task: M3.1.

The model writes questions and scores answers as 0, 0.5 or 1. Code snaps the scores and
computes the understanding score. The scorer never sees time, paste or tab data.
"""

from typing import Any

from pydantic import BaseModel, Field

from app.ai.grader import prepare_submission_text, verify_quote
from app.ai.loader import load_prompt, render
from app.config import get_settings
from app.llm.client import LLMError, complete_json
from app.schemas.viva import VivaKind

MAX_QUESTIONS = 5
EXCERPT_RADIUS = 400
EXCERPT_FALLBACK_CHARS = 800


# ---- what the model returns ------------------------------------------------------------


class LLMQuestion(BaseModel):
    id: str = ""
    kind: VivaKind
    text: str = Field(min_length=1)
    topic: str = ""
    anchor_quote: str = ""


class ExaminerOutput(BaseModel):
    questions: list[LLMQuestion]


class ScorerOutput(BaseModel):
    score: float
    note: str = ""


# ---- questions -------------------------------------------------------------------------


def generate_questions(
    *,
    content_md: str,
    instructions_md: str,
    topics: list[str],
    count: int,
    time_limit_s: int,
    key: str | None = None,
) -> list[dict[str, Any]]:
    """Return stored question dicts: id, kind, text, topic, time_limit_s, anchor_quote.

    Every anchor_quote is checked against the submission. Questions whose anchor is not
    found are asked for again once. In mock mode the canned questions are accepted as is.
    """
    count = max(1, min(MAX_QUESTIONS, count))
    safe_text = prepare_submission_text(content_md)
    prompt = load_prompt("examiner")
    mock = get_settings().mock_llm

    def ask(n: int, extra: str) -> list[LLMQuestion]:
        user = render(
            prompt.user_template,
            instructions_md=instructions_md,
            topics=", ".join(topics),
            content_md=safe_text,
            extra=extra,
        )
        out = complete_json(
            role="viva_questions",
            system=render(prompt.system, n=str(n)),
            user=user,
            schema=ExaminerOutput,
            prompt_version=prompt.version,
            max_tokens=1200,
            key=key,
        )
        return out.questions

    chosen: list[LLMQuestion] = []
    seen_anchors: set[int] = set()
    failed: list[str] = []

    def take(candidates: list[LLMQuestion]) -> None:
        for q in candidates:
            if len(chosen) >= count:
                return
            if mock:
                chosen.append(q)
                continue
            found = verify_quote(q.anchor_quote, content_md) if q.anchor_quote else None
            if found is None:
                failed.append(q.anchor_quote)
            elif found.start not in seen_anchors:
                seen_anchors.add(found.start)
                chosen.append(q)

    take(ask(count, ""))
    if not mock and len(chosen) < count:
        note = (
            "Earlier anchor_quote values were not found in the submission. "
            "Copy each anchor_quote exactly from the submission text. Not found: "
            + "; ".join(f'"{a}"' for a in failed[:5])
        )
        take(ask(count - len(chosen), note))
    if not chosen:
        raise LLMError("Could not write viva questions grounded in the submission.")

    fallback_topic = topics[0] if topics else "general"
    return [
        {
            "id": f"vq_{i}",
            "kind": q.kind,
            "text": q.text.strip(),
            "topic": q.topic if q.topic in topics else fallback_topic,
            "time_limit_s": time_limit_s,
            "anchor_quote": q.anchor_quote,
        }
        for i, q in enumerate(chosen, start=1)
    ]


# ---- scoring ---------------------------------------------------------------------------


def excerpt_for(content_md: str, anchor_quote: str) -> str:
    """The student's own text around the anchor, or the start of the work as a fallback."""
    found = verify_quote(anchor_quote, content_md) if anchor_quote else None
    if found is None:
        return content_md[:EXCERPT_FALLBACK_CHARS]
    # Offsets are UTF-16. Re-find in code points to slice safely.
    idx = content_md.find(found.quote)
    if idx == -1:
        return content_md[:EXCERPT_FALLBACK_CHARS]
    start = max(0, idx - EXCERPT_RADIUS)
    end = min(len(content_md), idx + len(found.quote) + EXCERPT_RADIUS)
    return content_md[start:end]


def snap_score(value: float) -> float:
    """Clamp to 0..1 and snap to 0, 0.5 or 1."""
    return min(1.0, max(0.0, round(value * 2) / 2))


def score_answer(
    *, question: str, work_excerpt: str, answer_text: str, key: str | None = None
) -> tuple[float, str]:
    """Score one answer. Only question, the student's text and the answer reach the model."""
    prompt = load_prompt("scorer")
    user = render(
        prompt.user_template,
        question=question,
        work_excerpt=work_excerpt.replace("</student_work>", "[/student_work]"),
        answer=answer_text.replace("</answer>", "[/answer]"),
    )
    out = complete_json(
        role="viva_scores",
        system=prompt.system,
        user=user,
        schema=ScorerOutput,
        prompt_version=prompt.version,
        max_tokens=300,
        key=key,
    )
    return snap_score(out.score), out.note.strip()


def understanding_score(scores: list[float]) -> float:
    """Mean of the question scores. Missing or timed-out answers are in the list as 0."""
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)
