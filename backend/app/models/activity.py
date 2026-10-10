"""Append-only writing activity storage, owned by Majid."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import JSON, Column, Field, SQLModel


class ActivityBatchRecord(SQLModel, table=True):
    __tablename__ = "activity_batches"
    __table_args__ = (UniqueConstraint("submission_id", "session_id", "first_seq"),)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    submission_id: str = Field(index=True)
    session_id: str = Field(index=True)
    session_started_at: datetime
    first_seq: int
    last_seq: int
    events: list[dict] = Field(sa_column=Column(JSON, nullable=False))
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
