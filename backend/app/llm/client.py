"""The only module that talks to an LLM provider. Everyone else calls complete_json().

Contract: docs/ai-spec.md section 8.

Order of a call: mock (MOCK_LLM=1), disk cache, provider. Provider output is parsed as JSON
and validated with the caller's Pydantic schema. One repair retry on bad output, one retry on
timeouts, 429 and 5xx, then LLMError (routers map it to 502 `llm_unavailable`).
Prompts and student text are never logged at INFO.
"""

import json
import logging
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.llm import cache
from app.llm.mock import load_mock

T = TypeVar("T", bound=BaseModel)

ROLES = {"rubric_draft", "grader", "feedback", "viva_questions", "viva_scores"}

log = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"
RETRY_STATUSES = {429, 500, 502, 503, 504}

# Tests set this to an httpx.MockTransport so no network call is made.
_transport: httpx.BaseTransport | None = None


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
            try:
                return _validate(schema, cached)
            except LLMError:
                pass  # stale or corrupt cache entry: fall through to a fresh call

    result = _call_with_repair(
        system=system,
        user=user,
        schema=schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if settings.llm_cache:
        cache.put(cache_key, result.model_dump(mode="json"))
    return result


def _validate(schema: type[T], raw: Any) -> T:
    try:
        return schema.model_validate(raw)
    except ValidationError as exc:
        raise LLMError(f"LLM output did not match {schema.__name__}.") from exc


def _call_with_repair(
    *,
    system: str,
    user: str,
    schema: type[T],
    temperature: float,
    max_tokens: int,
) -> T:
    """Call the provider. If the output is not valid JSON for `schema`, retry once."""
    text = _call_provider(
        system=system, user=user, temperature=temperature, max_tokens=max_tokens
    )
    try:
        return _parse_and_validate(schema, text)
    except (ValueError, ValidationError) as first_error:
        log.info("LLM output failed validation, retrying once (%s)", type(first_error).__name__)
        repair_user = (
            f"{user}\n\nYour last output was not valid JSON for this schema: "
            f"{_short_error(first_error)}. Return JSON only, with no extra text."
        )
        text = _call_provider(
            system=system, user=repair_user, temperature=temperature, max_tokens=max_tokens
        )
        try:
            return _parse_and_validate(schema, text)
        except (ValueError, ValidationError) as exc:
            raise LLMError(f"LLM output did not match {schema.__name__}.") from exc


def _parse_and_validate(schema: type[T], text: str) -> T:
    return schema.model_validate(extract_json(text))


def extract_json(text: str) -> Any:
    """Parse JSON from model text. Tolerates code fences and short text around the object."""
    cleaned = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("no JSON object found") from None
        return json.loads(cleaned[start : end + 1])


def _short_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:300]


def _call_provider(*, system: str, user: str, temperature: float, max_tokens: int) -> str:
    """One provider request, with one retry on timeout, 429 and 5xx. Returns the reply text."""
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()
    if not provider or not settings.llm_model or not settings.llm_api_key:
        raise LLMError(
            "LLM provider is not configured. Set LLM_PROVIDER, LLM_MODEL and LLM_API_KEY "
            "in backend/.env, or set MOCK_LLM=1."
        )
    if provider not in {"openai", "anthropic", "openai_compatible"}:
        raise LLMError(f"Unknown LLM_PROVIDER '{provider}'.")

    last_error: str = "unknown error"
    for attempt in range(2):
        try:
            with httpx.Client(timeout=settings.llm_timeout_s, transport=_transport) as client:
                if provider == "anthropic":
                    return _anthropic(client, system, user, temperature, max_tokens)
                return _openai_style(client, provider, system, user, temperature, max_tokens)
        except _Retryable as exc:
            last_error = str(exc)
            log.info("LLM call failed (attempt %d): %s", attempt + 1, last_error)
        except httpx.TimeoutException:
            last_error = "timeout"
            log.info("LLM call timed out (attempt %d)", attempt + 1)
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM request failed: {type(exc).__name__}.") from exc
    raise LLMError(f"LLM unavailable after retry: {last_error}.")


class _Retryable(Exception):
    pass


def _check(res: httpx.Response) -> None:
    if res.status_code in RETRY_STATUSES:
        raise _Retryable(f"HTTP {res.status_code}")
    if res.status_code >= 400:
        raise LLMError(f"LLM provider returned HTTP {res.status_code}.")


def _openai_style(
    client: httpx.Client,
    provider: str,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
) -> str:
    settings = get_settings()
    base = settings.llm_base_url.strip().rstrip("/")
    if not base:
        if provider == "openai_compatible":
            raise LLMError("LLM_BASE_URL is required for openai_compatible.")
        base = OPENAI_BASE_URL
    # OpenAI's newer models want max_completion_tokens; other servers still use max_tokens.
    token_field = "max_completion_tokens" if provider == "openai" else "max_tokens"
    body: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        token_field: max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    res = client.post(f"{base}/chat/completions", json=body, headers=headers)
    # Some models only accept their default temperature. Retry once without it.
    if res.status_code == 400 and "temperature" in res.text.lower():
        body.pop("temperature")
        res = client.post(f"{base}/chat/completions", json=body, headers=headers)
    _check(res)
    try:
        return str(res.json()["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise LLMError("LLM provider returned an unexpected response shape.") from exc


def _anthropic(
    client: httpx.Client, system: str, user: str, temperature: float, max_tokens: int
) -> str:
    settings = get_settings()
    base = settings.llm_base_url.strip().rstrip("/") or ANTHROPIC_BASE_URL
    body: dict[str, Any] = {
        "model": settings.llm_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }
    res = client.post(f"{base}/messages", json=body, headers=headers)
    if res.status_code == 400 and "temperature" in res.text.lower():
        body.pop("temperature")
        res = client.post(f"{base}/messages", json=body, headers=headers)
    _check(res)
    try:
        parts = res.json()["content"]
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise LLMError("LLM provider returned an unexpected response shape.") from exc
