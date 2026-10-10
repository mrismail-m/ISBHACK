from datetime import datetime
from typing import Any

from pydantic import BaseModel


class UserSchema(BaseModel):
    id: str
    name: str
    role: str
    classroom_id: str


class AssessmentCreate(BaseModel):
    classroom_id: str
    kind: str
    title: str
    instructions_md: str
    max_marks: float
    pass_mark_pct: float
    rubric: dict[str, Any] | None = None
    model_answer_md: str | None = None
    strictness: str
    viva_enabled: bool
    viva_weight: float
    viva_question_count: int
    viva_time_limit_s: int
    feedback_mode: str
    release_mode: str
    ai_policy: str
    paste_flag_chars: int
    topics: list[str]


class AssessmentSchema(AssessmentCreate):
    id: str
    status: str
    due_at: datetime
    created_at: datetime


class QuestionSchema(BaseModel):
    id: str
    assessment_id: str
    kind: str
    text: str
    options: list[str]
    answer_key: int
    marks: float
    topic: str


class SubmissionSchema(BaseModel):
    id: str
    assessment_id: str
    student_id: str
    content_md: str
    answers: list[dict[str, Any]]
    status: str
    started_at: datetime
    submitted_at: datetime | None = None


class SubmissionRow(BaseModel):
    submission_id: str
    label: str
    student_id: str
    student_name: str
    status: str
    submitted_at: datetime | None = None
    ai_total: float | None = None
    final_total: float | None = None
    max_marks: float
    understanding: float | None = None
    score_pct: float | None = None
    score_is_final: bool
    overall_confidence: float | None = None
    flags: list[str]


class SubmissionUpdate(BaseModel):
    content_md: str | None = None
    answers: list[dict[str, Any]] | None = None


class ApproveRequest(BaseModel):
    criteria_overrides: list[dict[str, Any]] = []
    teacher_note: str | None = None
    feedback_edits: dict[str, str] = {}
    release: bool


class StudentResult(BaseModel):
    submission_id: str
    assessment_id: str
    max_marks: float
    work_marks: float
    understanding: float | None = None
    viva_weight: float
    final_marks: float
    grace_marks: float
    final_with_grace: float
    final_pct: float
    feedback: dict[str, Any]
    released_at: datetime | None = None
