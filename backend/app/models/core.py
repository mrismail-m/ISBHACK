from datetime import datetime
from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True)
    name: str
    role: str
    classroom_id: str


class Classroom(SQLModel, table=True):
    __tablename__ = "classrooms"
    id: str = Field(primary_key=True)
    name: str
    teacher_id: str


class Assessment(SQLModel, table=True):
    __tablename__ = "assessments"
    id: str = Field(primary_key=True)
    classroom_id: str
    kind: str
    title: str
    instructions_md: str
    max_marks: float
    pass_mark_pct: float
    rubric: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
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
    topics: list[str] = Field(default=[], sa_column=Column(JSON))
    status: str
    due_at: datetime
    created_at: datetime


class Question(SQLModel, table=True):
    __tablename__ = "questions"
    id: str = Field(primary_key=True)
    assessment_id: str
    kind: str
    text: str
    options: list[str] = Field(default=[], sa_column=Column(JSON))
    answer_key: int
    marks: float
    topic: str


class Submission(SQLModel, table=True):
    __tablename__ = "submissions"
    id: str = Field(primary_key=True)
    assessment_id: str
    student_id: str
    content_md: str
    answers: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    status: str
    started_at: datetime
    submitted_at: datetime | None = None


class GraceAdjustment(SQLModel, table=True):
    __tablename__ = "grace_adjustments"
    id: str = Field(primary_key=True)
    assessment_id: str
    marks: float
    reason: str
    applied_at: datetime
    undone_at: datetime | None = None
