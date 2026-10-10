"""Contract activity types. Positions and character counts use UTF-16 units."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EventKind = Literal[
    "start",
    "end",
    "type",
    "paste",
    "drop",
    "cut",
    "del",
    "undo",
    "redo",
    "blur",
    "focus",
    "hidden",
    "visible",
]
NON_EDIT = {"start", "end", "blur", "focus", "hidden", "visible"}


class ActivityEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    seq: int = Field(ge=0, strict=True)
    t: int = Field(ge=0, strict=True)
    k: EventKind
    from_: int = Field(alias="from", ge=0, strict=True)
    to: int = Field(ge=0, strict=True)
    text: str

    @model_validator(mode="after")
    def valid_range(self):
        if self.to < self.from_:
            raise ValueError("to must be at least from")
        if self.k in NON_EDIT and (self.from_ or self.to or self.text):
            raise ValueError("Non-edit events require empty ranges and text")
        if self.k in {"cut", "del"} and self.text:
            raise ValueError("Deletions require empty text")
        return self


class ActivityBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=200)
    session_started_at: datetime
    events: list[ActivityEvent] = Field(max_length=2000)

    @model_validator(mode="after")
    def valid_order(self):
        if self.session_started_at.utcoffset() is None:
            raise ValueError("session_started_at must include a UTC offset")
        for previous, current in zip(self.events, self.events[1:], strict=False):
            if current.seq <= previous.seq or current.t < previous.t:
                raise ValueError("Events must have increasing seq and monotonic t")
        return self


class SessionInfo(BaseModel):
    session_id: str
    started_at: datetime


class SessionEvent(ActivityEvent):
    session_id: str


class ActivityEvents(BaseModel):
    sessions: list[SessionInfo]
    events: list[SessionEvent]


class PasteChunk(BaseModel):
    session_id: str
    event_seq: int
    at: str
    t: int
    chars: int
    survived_chars: int
    survived_pct: float
    major: bool
    declared_source: str | None = None


class HeatBucket(BaseModel):
    bucket_start: str
    edits: int
    typed_chars: int
    pasted_chars: int


class ActivitySummary(BaseModel):
    submission_id: str
    final_chars: int
    typed_pct: float
    pasted_pct: float
    paste_chunks: list[PasteChunk]
    revision_ratio: float
    active_minutes: int
    span_minutes: float
    tab_switches: int
    sessions: int
    bucket: Literal["minute", "hour"]
    heatmap: list[HeatBucket]
