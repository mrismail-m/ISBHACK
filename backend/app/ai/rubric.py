"""Rubric drafter (LLM role `rubric_draft`). See docs/ai-spec.md section 2. Task: M2.1 (P1)."""

from app.ai.loader import load_prompt, render
from app.llm.client import complete_json
from app.models.core import Assessment
from app.schemas.grading import Rubric


def draft_rubric(
    assessment: Assessment, notes: str | None = None, key: str | None = None
) -> Rubric:
    prompt = load_prompt("rubric")
    user = render(
        prompt.user_template,
        max_marks=f"{assessment.max_marks:g}",
        instructions_md=assessment.instructions_md,
        notes=notes or "None provided.",
    )
    return complete_json(
        role="rubric_draft",
        system=prompt.system,
        user=user,
        schema=Rubric,
        prompt_version=prompt.version,
        key=key,
    )
