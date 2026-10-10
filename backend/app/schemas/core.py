from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

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
    rubric: Optional[Dict[str, Any]] = None
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
    topics: List[str]

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
    options: List[str]
    answer_key: int
    marks: float
    topic: str

class SubmissionSchema(BaseModel):
    id: str
    assessment_id: str
    student_id: str
    content_md: str
    answers: List[Dict[str, Any]]
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
