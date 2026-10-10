from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

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
    rubric: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    model_answer_md: Optional[str] = None
    strictness: str
    viva_enabled: bool
    viva_weight: float
    viva_question_count: int
    viva_time_limit_s: int
    feedback_mode: str
    release_mode: str
    ai_policy: str
    paste_flag_chars: int
    topics: List[str] = Field(default=[], sa_column=Column(JSON))
    status: str
    due_at: datetime
    created_at: datetime

class Question(SQLModel, table=True):
    __tablename__ = "questions"
    id: str = Field(primary_key=True)
    assessment_id: str
    kind: str
    text: str
    options: List[str] = Field(default=[], sa_column=Column(JSON))
    answer_key: int
    marks: float
    topic: str

class Submission(SQLModel, table=True):
    __tablename__ = "submissions"
    id: str = Field(primary_key=True)
    assessment_id: str
    student_id: str
    content_md: str
    answers: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None

class GraceAdjustment(SQLModel, table=True):
    __tablename__ = "grace_adjustments"
    id: str = Field(primary_key=True)
    assessment_id: str
    marks: float
    reason: str
    applied_at: datetime
    undone_at: Optional[datetime] = None
