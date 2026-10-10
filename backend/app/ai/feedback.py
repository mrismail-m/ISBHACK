"""Feedback writer and topic levels. See docs/ai-spec.md section 5.

Tasks: M1.1 (topic levels, starter feedback), M2.2 (the LLM writer).
"""

import json

from pydantic import BaseModel

from app.ai.grader import verify_quote
from app.ai.loader import load_prompt, render
from app.llm.client import complete_json
from app.schemas.grading import (
    CriterionGrade,
    Feedback,
    FeedbackImprovement,
    FeedbackMode,
    FeedbackStrength,
    Rubric,
    TopicLevel,
)

STRONG_AT = 0.75
OK_AT = 0.5


def topic_levels(rubric: Rubric, criteria: list[CriterionGrade]) -> list[TopicLevel]:
    """Per rubric topic: mean of level/4 over its criteria, then strong, ok or weak. Code only."""
    level_by_id = {c.criterion_id: c.level for c in criteria}
    order: list[str] = []
    values: dict[str, list[float]] = {}
    for crit in rubric.criteria:
        if crit.id not in level_by_id:
            continue
        if crit.topic not in values:
            order.append(crit.topic)
            values[crit.topic] = []
        values[crit.topic].append(level_by_id[crit.id] / 4)
    out: list[TopicLevel] = []
    for topic in order:
        mean = sum(values[topic]) / len(values[topic])
        level = "strong" if mean >= STRONG_AT else "ok" if mean >= OK_AT else "weak"
        out.append(TopicLevel(tag=topic, level=level))
    return out


class LLMFeedback(BaseModel):
    strengths: list[FeedbackStrength]
    improvements: list[FeedbackImprovement]
    next_step: str


def starter_feedback(
    *, mode: FeedbackMode, rubric: Rubric, criteria: list[CriterionGrade]
) -> Feedback:
    """Feedback with computed topics and no LLM text yet (M2.2 fills the text)."""
    return Feedback(mode=mode, topics=topic_levels(rubric, criteria))


def generate_feedback(
    *,
    mode: FeedbackMode,
    rubric: Rubric,
    criteria: list[CriterionGrade],
    content_md: str,
    key: str | None = None,
) -> Feedback:
    """Generate feedback using the LLM and verify its quotes."""
    prompt = load_prompt("feedback")

    levels_list = [
        {
            "criterion_id": c.criterion_id,
            "level": c.level,
            "evidence": [e.quote for e in c.evidence],
            "reasoning": c.reasoning,
        }
        for c in criteria
    ]

    user = render(
        prompt.user_template,
        mode=mode,
        rubric_json=json.dumps(rubric.model_dump(), ensure_ascii=False),
        levels_evidence_reasoning_json=json.dumps(levels_list, ensure_ascii=False),
        content_md=content_md,
    )

    output = complete_json(
        role="feedback",
        system=prompt.system,
        user=user,
        schema=LLMFeedback,
        prompt_version=prompt.version,
        key=key,
    )

    for strength in output.strengths:
        if strength.quote:
            if not verify_quote(strength.quote, content_md):
                strength.quote = None

    for imp in output.improvements:
        if imp.quote:
            if not verify_quote(imp.quote, content_md):
                imp.quote = None
        if mode == "hints":
            imp.explanation = None

    return Feedback(
        mode=mode,
        strengths=output.strengths,
        improvements=output.improvements,
        next_step=output.next_step,
        topics=topic_levels(rubric, criteria),
    )
