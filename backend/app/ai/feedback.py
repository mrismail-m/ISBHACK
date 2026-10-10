"""Feedback writer and topic levels. See docs/ai-spec.md section 5.

Tasks: M1.1 (topic levels, starter feedback), M2.2 (the LLM writer).
"""

from app.schemas.grading import CriterionGrade, Feedback, FeedbackMode, Rubric, TopicLevel

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


def starter_feedback(
    *, mode: FeedbackMode, rubric: Rubric, criteria: list[CriterionGrade]
) -> Feedback:
    """Feedback with computed topics and no LLM text yet (M2.2 fills the text)."""
    return Feedback(mode=mode, topics=topic_levels(rubric, criteria))
