"""Additive Learning Lab contract. See docs/learning-lab.md."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

LabPhase = Literal["challenge", "recovery", "complete"]


class LabQuestion(BaseModel):
    scenario: str = Field(min_length=1, max_length=2000)
    question: str = Field(min_length=1, max_length=1000)


class LabObservation(BaseModel):
    level: Literal[0, 1, 2]  # not demonstrated, partial, demonstrated
    reasoning: str = Field(min_length=1, max_length=1500)
    suspected_gap: str = Field(max_length=500)
    answer_quote: str = Field(max_length=500)
    teaching: str = Field(min_length=1, max_length=2000)


class LabState(BaseModel):
    id: str
    submission_id: str
    assessment_id: str
    concept: str
    anchor_quote: str
    phase: LabPhase
    challenge: LabQuestion
    recovery: LabQuestion | None = None
    initial_answer: str = ""
    recovery_answer: str = ""
    initial: LabObservation | None = None
    final: LabObservation | None = None
    mode: Literal["live", "fixture"]
    created_at: str


class LabAnswer(BaseModel):
    phase: Literal["challenge", "recovery"]
    answer_text: str = Field(min_length=1, max_length=3000)

    @field_validator("answer_text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Write an answer before continuing.")
        return value.strip()


class LabReport(BaseModel):
    assessment_id: str
    sessions: list[LabState]
