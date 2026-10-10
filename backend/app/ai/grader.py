"""Level-based grader, quote verifier, injection guard.

See docs/ai-spec.md section 4. The model picks levels and quotes. Code verifies the quotes
and computes every mark (see strictness.py). Tasks: M1.1 (core), M2.1 (retries, guards).
"""

import json
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from app.ai.loader import load_prompt, render
from app.ai.strictness import STRICTNESS_ORDER, criterion_marks
from app.config import get_settings
from app.deps import ApiError
from app.llm.client import LLMError, complete_json
from app.schemas.grading import CriterionGrade, Evidence, GraderFlag, Rubric

MAX_SUBMISSION_CHARS = 8000
MAX_QUOTES_PER_CRITERION = 3
LOW_CONFIDENCE_BELOW = 0.6
UNVERIFIED_CONFIDENCE_CAP = 0.3

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all|any|previous|the above)", re.IGNORECASE),
    re.compile(r"give\s+(me\s+)?(full|maximum|100)", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now", re.IGNORECASE),
]


# ---- what the model returns ------------------------------------------------------------


class LLMCriterion(BaseModel):
    criterion_id: str
    level: int = Field(ge=0, le=4)
    minor_errors: int = Field(default=0, ge=0)
    ambiguous: bool = False
    evidence: list[str] = Field(default_factory=list)
    reasoning: str = ""
    confidence: float = Field(default=0.5, ge=0, le=1)


class GraderOutput(BaseModel):
    criteria: list[LLMCriterion]
    overall_confidence: float = Field(default=0.5, ge=0, le=1)
    flags: list[str] = Field(default_factory=list)


# ---- verified result (no marks yet, so one pass can serve every strictness) ---------------


@dataclass
class VerifiedCriterion:
    criterion_id: str
    level: int
    minor_errors: int
    ambiguous: bool
    evidence: list[Evidence]
    reasoning: str
    confidence: float


@dataclass
class VerifiedResult:
    criteria: list[VerifiedCriterion]
    overall_confidence: float
    flags: list[GraderFlag] = field(default_factory=list)
    prompt_version: str = ""
    model_id: str = ""


# ---- quote verification ----------------------------------------------------------------

_CURLY = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}


def _normalize(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace runs and straighten curly quotes.

    Returns the normalized text and, for each normalized char, its index in the original.
    """
    out: list[str] = []
    index: list[int] = []
    prev_space = False
    for i, ch in enumerate(text):
        ch = _CURLY.get(ch, ch)
        if ch.isspace():
            if prev_space:
                continue
            out.append(" ")
            prev_space = True
        else:
            out.append(ch)
            prev_space = False
        index.append(i)
    return "".join(out), index


def utf16_offset(text: str, code_point_index: int) -> int:
    """Convert a Python string index to a UTF-16 code unit offset (same as JavaScript)."""
    return len(text[:code_point_index].encode("utf-16-le", errors="surrogatepass")) // 2


def verify_quote(quote: str, content: str) -> Evidence | None:
    """Find `quote` in `content`. Return Evidence with UTF-16 offsets, or None if not verbatim."""
    norm_quote, _ = _normalize(quote.strip())
    if not norm_quote:
        return None
    norm_content, index = _normalize(content)
    pos = norm_content.find(norm_quote)
    if pos == -1:
        return None
    start = index[pos]
    end = index[pos + len(norm_quote) - 1] + 1
    return Evidence(
        quote=content[start:end],
        start=utf16_offset(content, start),
        end=utf16_offset(content, end),
        verified=True,
    )


def looks_like_injection(text: str) -> bool:
    return any(p.search(text) for p in INJECTION_PATTERNS)


# ---- prompt input ----------------------------------------------------------------------


def prepare_submission_text(content_md: str) -> str:
    """Reject over-long text and neutralise the closing delimiter."""
    if len(content_md) > MAX_SUBMISSION_CHARS:
        raise ApiError(
            422,
            "validation_error",
            f"Submission is longer than {MAX_SUBMISSION_CHARS} characters.",
        )
    return content_md.replace("</submission>", "[/submission]")


# ---- the grading pass ------------------------------------------------------------------


def run_grader(
    *,
    content_md: str,
    title: str,
    instructions_md: str,
    model_answer_md: str | None,
    rubric: Rubric,
    key: str | None = None,
) -> VerifiedResult:
    """Ask the model for levels and quotes, verify the quotes, set confidence and flags.

    No student name, email or ID is ever passed in. Marks are not computed here.
    """
    safe_text = prepare_submission_text(content_md)
    prompt = load_prompt("grader")
    user = render(
        prompt.user_template,
        title=title,
        instructions_md=instructions_md,
        model_answer=model_answer_md or "none",
        rubric_json=json.dumps(rubric.model_dump(), ensure_ascii=False),
        content_md=safe_text,
    )
    output = complete_json(
        role="grader",
        system=prompt.system,
        user=user,
        schema=GraderOutput,
        prompt_version=prompt.version,
        max_tokens=2500,
        key=key,
    )
    settings = get_settings()
    result = verify_output(output, rubric=rubric, content_md=content_md)
    result.prompt_version = prompt.version
    result.model_id = "mock" if settings.mock_llm else settings.llm_model
    return result


def verify_output(output: GraderOutput, *, rubric: Rubric, content_md: str) -> VerifiedResult:
    """Steps 1 to 3, 5 and 7 of docs/ai-spec.md section 4 (no marks)."""
    by_id: dict[str, LLMCriterion] = {}
    for item in output.criteria:
        if item.criterion_id in by_id:
            raise LLMError("Grader returned a criterion twice.")
        by_id[item.criterion_id] = item
    expected = [c.id for c in rubric.criteria]
    if set(by_id) != set(expected):
        raise LLMError("Grader output does not match the rubric criteria.")

    flags: list[GraderFlag] = []
    verified: list[VerifiedCriterion] = []
    for cid in expected:
        item = by_id[cid]
        evidence: list[Evidence] = []
        if item.level >= 1:
            for quote in item.evidence[:MAX_QUOTES_PER_CRITERION]:
                found = verify_quote(quote, content_md)
                if found is not None and all(found.start != e.start for e in evidence):
                    evidence.append(found)
        confidence = item.confidence
        if item.level >= 1 and not evidence:
            confidence = min(confidence, UNVERIFIED_CONFIDENCE_CAP)
            if "evidence_unverified" not in flags:
                flags.append("evidence_unverified")
        verified.append(
            VerifiedCriterion(
                criterion_id=cid,
                level=item.level,
                minor_errors=item.minor_errors,
                ambiguous=item.ambiguous,
                evidence=evidence,
                reasoning=item.reasoning,
                confidence=confidence,
            )
        )

    if "injection_attempt" in output.flags or looks_like_injection(content_md):
        flags.append("injection_attempt")

    overall = sum(c.confidence for c in verified) / len(verified) if verified else 0.0
    if sum(1 for c in verified if c.ambiguous) >= 2:
        overall -= 0.1
    overall = round(min(1.0, max(0.0, overall)), 2)
    if overall < LOW_CONFIDENCE_BELOW:
        flags.append("low_confidence")

    return VerifiedResult(criteria=verified, overall_confidence=overall, flags=flags)


# ---- marks (code only) -----------------------------------------------------------------


def apply_marks(
    result: VerifiedResult, *, rubric: Rubric, strictness: str
) -> list[CriterionGrade]:
    """Turn verified levels into marks for one strictness. Pure code, no model."""
    max_by_id = {c.id: c.max_marks for c in rubric.criteria}
    graded: list[CriterionGrade] = []
    for c in result.criteria:
        marks = criterion_marks(
            c.level, c.minor_errors, c.ambiguous, max_by_id[c.criterion_id], strictness
        )
        graded.append(
            CriterionGrade(
                criterion_id=c.criterion_id,
                level=c.level,
                minor_errors=c.minor_errors,
                ambiguous=c.ambiguous,
                ai_marks=marks,
                final_marks=marks,
                evidence=c.evidence,
                reasoning=c.reasoning,
                confidence=c.confidence,
            )
        )
    return graded


def totals_by_strictness(result: VerifiedResult, *, rubric: Rubric) -> dict[str, float]:
    """Total marks under every strictness from one grading pass."""
    return {
        s: sum(g.ai_marks for g in apply_marks(result, rubric=rubric, strictness=s))
        for s in STRICTNESS_ORDER
    }
