"""Learning evidence, kept separate from the grade ledger."""

from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel


class LearningLabSession(SQLModel, table=True):
    __tablename__ = "learning_lab_sessions"
    id: str = Field(primary_key=True)
    submission_id: str = Field(index=True, unique=True)
    assessment_id: str = Field(index=True)
    phase: str = "challenge"
    plan: dict[str, Any] = Field(sa_column=Column(JSON))
    initial_answer: str = ""
    recovery_answer: str = ""
    initial: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    final: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    mode: str
    created_at: str
