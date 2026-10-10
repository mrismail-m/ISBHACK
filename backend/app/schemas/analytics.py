
from pydantic import BaseModel


class HistogramBin(BaseModel):
    bin: str
    count: int

class TopicAverage(BaseModel):
    topic: str
    avg_pct: float
    n: int

class CriterionAverage(BaseModel):
    criterion_id: str
    name: str
    avg_pct: float

class AssessmentStats(BaseModel):
    assessment_id: str
    enrolled: int
    submitted: int
    graded: int
    approved: int
    released: int
    pending_review: int
    final: bool
    avg_pct: float | None
    median_pct: float | None
    pass_rate_pct: float | None
    highest_pct: float | None
    lowest_pct: float | None
    histogram: list[HistogramBin]
    topic_averages: list[TopicAverage]
    criterion_averages: list[CriterionAverage]
    grace_marks_applied: float

class AssessmentPerformance(BaseModel):
    assessment_id: str
    title: str
    kind: str
    due_at: str
    avg_pct: float | None
    pass_rate_pct: float | None

class StudentPerformance(BaseModel):
    student_id: str
    name: str
    scores_pct: list[float]

class ClassPerformance(BaseModel):
    classroom_id: str
    assessments: list[AssessmentPerformance]
    students: list[StudentPerformance]

class AttentionStudent(BaseModel):
    student_id: str
    name: str
    reasons: list[str]
    recent_scores_pct: list[float]
    last_understanding: float | None

class GraceMetrics(BaseModel):
    avg_pct: float
    pass_rate_pct: float

class GracePreview(BaseModel):
    marks: float
    affected_students: int
    capped_count: int
    before: GraceMetrics
    after: GraceMetrics

class GraceEntry(BaseModel):
    id: str
    marks: float
    reason: str | None
    applied_at: str
    undone_at: str | None

class GraceState(BaseModel):
    total_marks: float
    entries: list[GraceEntry]

class CriterionOverride(BaseModel):
    criterion_id: str
    override_rate_pct: float
    mean_signed_delta_marks: float

class OverrideStats(BaseModel):
    graded: int
    overridden: int
    override_rate_pct: float
    mean_abs_delta_marks: float
    mean_signed_delta_marks: float
    by_criterion: list[CriterionOverride]

class GraceApplyRequest(BaseModel):
    marks: float
    reason: str

class GracePreviewRequest(BaseModel):
    marks: float
    reason: str | None = None

class GraceUndoRequest(BaseModel):
    entry_id: str | None = None
