"""The only module that talks to an LLM provider. Everyone else calls complete_json().

Contract: docs/ai-spec.md section 8. Skeleton (M0.1): mock mode and caching work,
the real provider call is a stub until M1.1.
"""

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.llm import cache
from app.llm.mock import load_mock

T = TypeVar("T", bound=BaseModel)

ROLES = {"rubric_draft", "grader", "feedback", "viva_questions", "viva_scores"}


class LLMError(Exception):
    """Raised when the LLM is unavailable or returns unusable output.

    Routers map it to HTTP 502 with code `llm_unavailable`.
    """


def complete_json(
    *,
    role: str,
    system: str,
    user: str,
    schema: type[T],
    prompt_version: str,
    temperature: float = 0.0,
    max_tokens: int = 1500,
    key: str | None = None,
) -> T:
    """Return a validated `schema` instance for this call.

    Order: mock (MOCK_LLM=1), then disk cache, then the provider.
    """
    if role not in ROLES:
        raise ValueError(f"unknown LLM role: {role}")

    settings = get_settings()

    if settings.mock_llm:
        raw = load_mock(role, key)
        if raw is None:
            raise LLMError(f"No mock fixture for role '{role}' (key={key}).")
        return _validate(schema, raw)

    cache_key = cache.make_key(
        provider=settings.llm_provider,
        model=settings.llm_model,
        role=role,
        prompt_version=prompt_version,
        system=system,
        user=user,
        temperature=temperature,
    )
    if settings.llm_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return _validate(schema, cached)

    raw = _call_provider(
        system=system, user=user, temperature=temperature, max_tokens=max_tokens
    )
    result = _validate(schema, raw)
    if settings.llm_cache:
        cache.put(cache_key, result.model_dump(mode="json"))
    return result


def _validate(schema: type[T], raw: Any) -> T:
    try:
        return schema.model_validate(raw)
    except ValidationError as exc:
        raise LLMError(f"LLM output did not match {schema.__name__}.") from exc


def _call_provider(
    *, system: str, user: str, temperature: float, max_tokens: int
) -> dict[str, Any]:
    """Provider call. TODO(M1.1): pick the provider, add one JSON repair retry and one
    retry on timeout, 429 or 5xx, honour LLM_TIMEOUT_S, never log prompts at INFO."""
    raise LLMError("LLM provider is not configured yet. Set MOCK_LLM=1 or finish M1.1.")
