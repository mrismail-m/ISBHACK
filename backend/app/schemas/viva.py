"""Pydantic models for VivaStart, VivaAnswer, VivaResult, VivaDetail.

Mirror docs/api-contract.md exactly. Task: M3.1 (changes follow AGENTS.md section 5).
"""

from typing import Literal

from pydantic import BaseModel, Field

VivaKind = Literal["explain", "change", "defend", "trace"]


class VivaQuestion(BaseModel):
    id: str
    kind: VivaKind
    text: str
    topic: str
    time_limit_s: int


class VivaStart(BaseModel):
    session_id: str
    questions: list[VivaQuestion]
    total_time_limit_s: int


class VivaAnswer(BaseModel):
    question_id: str
    answer_text: str = Field(max_length=3000)
    time_taken_s: float = Field(default=0, ge=0)
    pasted: bool = False
    tab_switches: int = Field(default=0, ge=0)


class VivaAnswerResponse(BaseModel):
    ok: bool = True
    answered: int
    remaining: int


class VivaResult(BaseModel):
    understanding: float = Field(ge=0, le=1)
    answered: int
    total: int


class VivaDetailItem(BaseModel):
    question_id: str
    text: str
    answer_text: str
    score: float | None  # 0, 0.5 or 1 once scored
    note: str
    time_taken_s: float
    pasted: bool
    tab_switches: int


class VivaDetail(BaseModel):
    status: Literal["in_progress", "done"]
    understanding: float | None  # null until the viva is finished
    items: list[VivaDetailItem]
