"""SQLModel tables `grades` and `viva_sessions`. See docs/architecture.md section 4.

Task: M1.1. Schema changes: everyone re-runs `python -m app.seed --reset`.
Both tables are created at app startup (main.py) so they exist even before seed imports them.
"""

from datetime import datetime
from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel


class Grade(SQLModel, table=True):
    __tablename__ = "grades"
    id: str = Field(primary_key=True)
    submission_id: str = Field(unique=True, index=True)
    status: str  # ai_draft | approved
    strictness_used: str
    prompt_version: str
    model_id: str
    max_marks: float
    criteria: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    ai_total: float
    final_total: float
    overall_confidence: float
    grader_flags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    feedback: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    teacher_note: str | None = None
    approved_at: datetime | None = None
    released_at: datetime | None = None


class VivaSession(SQLModel, table=True):
    __tablename__ = "viva_sessions"
    id: str = Field(primary_key=True)
    submission_id: str = Field(unique=True, index=True)
    status: str  # started | done
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    answers: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    scores: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    understanding: float | None = None
    started_at: datetime
    finished_at: datetime | None = None
