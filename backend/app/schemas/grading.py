"""Pydantic models for Rubric, Grade, Feedback and StrictnessPreview.

Mirror docs/api-contract.md exactly. Task: M1.1 (changes follow AGENTS.md section 5).
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_serializer

Strictness = Literal["lenient", "normal", "strict", "very_strict"]
FeedbackMode = Literal["hints", "full"]
GraderFlag = Literal[
    "low_confidence", "evidence_unverified", "injection_attempt", "needs_manual_grading"
]


class RubricCriterion(BaseModel):
    id: str
    name: str
    description: str
    max_marks: float
    topic: str
    levels: list[str] = Field(min_length=5, max_length=5)


class Rubric(BaseModel):
    criteria: list[RubricCriterion]


class Evidence(BaseModel):
    quote: str
    start: int  # UTF-16 offset into content_md
    end: int
    verified: bool


class CriterionGrade(BaseModel):
    criterion_id: str
    level: int = Field(ge=0, le=4)
    minor_errors: int = Field(ge=0)
    ambiguous: bool
    ai_marks: float
    final_marks: float
    evidence: list[Evidence]
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    teacher_note: str | None = None


class FeedbackStrength(BaseModel):
    criterion_id: str
    text: str
    quote: str | None = None


class FeedbackImprovement(BaseModel):
    criterion_id: str
    text: str
    quote: str | None = None
    hint: str
    explanation: str | None = None  # present only when mode is "full"

    @model_serializer(mode="wrap")
    def _omit_empty_explanation(self, handler: Any) -> dict[str, Any]:
        data = handler(self)
        if data.get("explanation") is None:
            data.pop("explanation", None)
        return data


class TopicLevel(BaseModel):
    tag: str
    level: Literal["strong", "ok", "weak"]


class Feedback(BaseModel):
    mode: FeedbackMode
    strengths: list[FeedbackStrength] = Field(default_factory=list, max_length=3)
    improvements: list[FeedbackImprovement] = Field(default_factory=list, max_length=3)
    next_step: str = ""
    topics: list[TopicLevel] = Field(default_factory=list)


class GradeSchema(BaseModel):
    id: str
    submission_id: str
    status: Literal["ai_draft", "approved"]
    strictness_used: Strictness
    prompt_version: str
    model_id: str
    max_marks: float
    criteria: list[CriterionGrade]
    ai_total: float
    final_total: float
    overall_confidence: float = Field(ge=0, le=1)
    grader_flags: list[GraderFlag]
    feedback: Feedback
    teacher_note: str | None = None
    approved_at: datetime | None = None
    released_at: datetime | None = None


# ---- request and small response bodies -------------------------------------------------


class GradeRequest(BaseModel):
    """POST /submissions/:id/grade takes an empty body."""


class RubricDraftRequest(BaseModel):
    notes: str | None = None


class StrictnessPreviewRequest(BaseModel):
    answer_text: str


class PreviewCriterion(BaseModel):
    criterion_id: str
    marks: float


class PreviewLevel(BaseModel):
    strictness: Strictness
    total: float
    criteria: list[PreviewCriterion]


class StrictnessPreview(BaseModel):
    levels: list[PreviewLevel]
    note: str = "One grading pass, four strictness policies."


class GradeAllResponse(BaseModel):
    queued: int


class GradingStatus(BaseModel):
    total: int
    graded: int
    in_progress: int
    failed: int


# ---- trust report (docs/evaluation.md) -------------------------------------------------
# Human-dependent numbers are null until two human raters have scored the answers.
# `author_labels`, `n_answers` and the other extras below are additions to the contract.


class TrustDataset(BaseModel):
    assignment: str
    n_answers: int
    n_raters: int


class AuthorLabels(BaseModel):
    n: int
    mae_marks: float
    qwk: float
    mean_signed_marks: float  # AI minus author. Positive means the AI is more generous.
    by_criterion: dict[str, dict[str, float]] = Field(default_factory=dict)


class TrustAccuracy(BaseModel):
    ai_vs_human_mae: float | None = None
    human_vs_human_mae: float | None = None
    ai_vs_human_qwk: float | None = None
    human_vs_human_qwk: float | None = None
    author_labels: AuthorLabels | None = None


class TrustConsistency(BaseModel):
    runs: int
    mean_range_marks: float
    max_range_marks: float
    n_answers: int | None = None
    identical_level_pct: float | None = None


class BiasProbe(BaseModel):
    name: str
    n: int
    mean_abs_delta_marks: float
    max_abs_delta_marks: float
    threshold_marks: float
    passed: bool
    mean_signed_delta_marks: float | None = None
    description: str | None = None
    excluded_criteria: list[str] | None = None
    injection_flag_rate: float | None = None


class StrictnessOrdering(BaseModel):
    passed: bool
    violations: int
    n: int | None = None
    mean_spread_marks: float | None = None


class EditorSignals(BaseModel):
    samples: int
    typed_flagged: int
    pasted_flagged: int
    retyped_flagged: int


class TrustReport(BaseModel):
    generated_at: str
    model_id: str
    prompt_version: str
    dataset: TrustDataset
    accuracy: TrustAccuracy | None = None
    consistency: TrustConsistency | None = None
    bias_probes: list[BiasProbe] | None = None
    strictness_ordering: StrictnessOrdering | None = None
    editor_signals: EditorSignals | None = None
    limitations: list[str] = Field(default_factory=list)
