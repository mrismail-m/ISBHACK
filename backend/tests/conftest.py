"""Shared test setup: mock LLM on, a fresh in-memory database per test."""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings
from app.db import get_session
from app.llm.client import reset_pool_state
from app.main import app
from app.models import grading as _grading_models  # noqa: F401
from app.models.core import Assessment, Submission
from tests.sample_data import RUBRIC, SAMPLE_SUBMISSION


@pytest.fixture(autouse=True)
def _mock_llm_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Every test starts in mock mode with no cache. Tests can override the env."""
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setenv("LLM_PROVIDER", "")
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_BASE_URL", "")
    # A developer's backend/.env may hold real keys. Tests must never use them.
    for name in ("LLM_ORDER", "LLM_GROQ_KEYS", "LLM_GEMINI_KEYS"):
        monkeypatch.setenv(name, "")
    get_settings.cache_clear()
    reset_pool_state()
    yield
    get_settings.cache_clear()
    reset_pool_state()


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_assessment(**overrides: object) -> Assessment:
    values: dict[str, object] = {
        "id": "a_1",
        "classroom_id": "cl_1",
        "kind": "assignment",
        "title": "A1: Hash table collisions",
        "instructions_md": "Explain how a hash table handles collisions in about 300 words.",
        "max_marks": 20.0,
        "pass_mark_pct": 50.0,
        "rubric": RUBRIC,
        "model_answer_md": None,
        "strictness": "normal",
        "viva_enabled": True,
        "viva_weight": 0.3,
        "viva_question_count": 3,
        "viva_time_limit_s": 90,
        "feedback_mode": "full",
        "release_mode": "after_approval",
        "ai_policy": "allowed_with_disclosure",
        "paste_flag_chars": 500,
        "topics": ["hashing", "collisions", "complexity", "communication"],
        "status": "open",
        "due_at": datetime(2026, 10, 12, 18, 0, tzinfo=UTC),
        "created_at": datetime(2026, 10, 10, 5, 0, tzinfo=UTC),
    }
    values.update(overrides)
    return Assessment(**values)  # type: ignore[arg-type]


def make_submission(**overrides: object) -> Submission:
    values: dict[str, object] = {
        "id": "s_1",
        "assessment_id": "a_1",
        "student_id": "u_student_3",
        "content_md": SAMPLE_SUBMISSION,
        "answers": [],
        "status": "submitted",
        "started_at": datetime(2026, 10, 10, 7, 12, tzinfo=UTC),
        "submitted_at": datetime(2026, 10, 10, 7, 40, tzinfo=UTC),
    }
    values.update(overrides)
    return Submission(**values)  # type: ignore[arg-type]


@pytest.fixture
def seeded(db: Session) -> Session:
    db.add(make_assessment())
    db.add(make_submission())
    db.commit()
    return db
