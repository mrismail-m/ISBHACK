"""The only module that talks to an LLM provider. Everyone else calls complete_json().

Contract: docs/ai-spec.md section 8.

Order of a call: mock (MOCK_LLM=1), disk cache, provider pool. Provider output is parsed as
JSON and validated with the caller's Pydantic schema. One repair retry on bad output, then
LLMError (routers map it to 502 `llm_unavailable`).

Provider pool: every configured key is an endpoint. Calls rotate round-robin over the keys of
the first provider (spreads rate limits). A key that fails with 429, 5xx, a timeout or an auth
error goes on cooldown and the next key is tried, then the next provider (the fallback).
Keys are never logged. Prompts and student text are never logged at INFO.
"""

import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings
from app.llm import cache
from app.llm.mock import load_mock

T = TypeVar("T", bound=BaseModel)

ROLES = {
    "rubric_draft", "grader", "feedback", "viva_questions", "viva_scores", "eval_polish",
    "lab_plan", "lab_observe", "lab_recovery",
}

log = logging.getLogger(__name__)

BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "anthropic": "https://api.anthropic.com/v1",
}
ANTHROPIC_VERSION = "2023-06-01"
KNOWN_PROVIDERS = {"openai", "groq", "gemini", "anthropic", "openai_compatible"}

# Seconds a failing key is skipped before it is tried again.
COOLDOWN_RATE_LIMIT_S = 60
COOLDOWN_SERVER_S = 20
COOLDOWN_BAD_KEY_S = 3600
COOLDOWN_OTHER_4XX_S = 300
MIN_TOTAL_BUDGET_S = 45  # stop trying more keys after this long (the API promises 30 s)

# Tests set this to an httpx.MockTransport so no network call is made.
_transport: httpx.BaseTransport | None = None


class LLMError(Exception):
    """Raised when the LLM is unavailable or returns unusable output.

    Routers map it to HTTP 502 with code `llm_unavailable`.
    """


# ---- the key pool ----------------------------------------------------------------------


@dataclass(frozen=True)
class Endpoint:
    label: str  # for example "groq#2". Never contains the key.
    provider: str
    model: str
    api_key: str = field(repr=False)
    base_url: str = ""

    @property
    def model_id(self) -> str:
        return f"{self.provider}:{self.model}"


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def build_pool(settings: Settings) -> list[Endpoint]:
    """All usable endpoints, in priority order (provider order, then key order)."""
    providers: list[str] = []
    for name in ([settings.llm_provider.strip().lower()] if settings.llm_provider else []) + [
        p.lower() for p in _split(settings.llm_order)
    ]:
        if name not in providers:
            providers.append(name)

    pool: list[Endpoint] = []
    for provider in providers:
        if provider not in KNOWN_PROVIDERS:
            raise LLMError(f"Unknown LLM provider '{provider}'.")
        single_key = [settings.llm_api_key] if settings.llm_api_key else []
        is_primary = provider == settings.llm_provider.strip().lower()
        if provider == "groq":
            keys = _split(settings.llm_groq_keys) or (single_key if is_primary else [])
            model = settings.llm_groq_model or settings.llm_model
            base = BASE_URLS["groq"]
        elif provider == "gemini":
            keys = _split(settings.llm_gemini_keys) or (single_key if is_primary else [])
            model = settings.llm_gemini_model or settings.llm_model
            base = BASE_URLS["gemini"]
        else:
            keys = single_key if is_primary else []
            model = settings.llm_model
            base = settings.llm_base_url.strip().rstrip("/") or BASE_URLS.get(provider, "")
            if keys and provider == "openai_compatible" and not base:
                raise LLMError("LLM_BASE_URL is required for openai_compatible.")
        if not model:
            continue
        for i, key in enumerate(keys, start=1):
            pool.append(
                Endpoint(label=f"{provider}#{i}", provider=provider, model=model,
                         api_key=key, base_url=base)
            )
    return pool


_lock = threading.Lock()
_cooldown_until: dict[str, float] = {}
_rotation = 0
_requests = 0
_last = threading.local()


def reset_pool_state() -> None:
    """Forget cooldowns, the rotation position and the request counter (used by tests)."""
    global _rotation, _requests
    with _lock:
        _cooldown_until.clear()
        _rotation = 0
        _requests = 0


def request_count() -> int:
    """Provider requests made so far in this process (cache and mock hits do not count)."""
    return _requests


def last_model_id() -> str | None:
    """Model behind the latest result on this thread, like 'groq:openai/gpt-oss-120b'."""
    return getattr(_last, "model_id", None)


def _ordered_candidates(pool: list[Endpoint]) -> list[Endpoint]:
    """Round-robin inside each provider, providers in priority order, cooling keys last."""
    global _rotation
    with _lock:
        turn = _rotation
        _rotation += 1
        now = time.monotonic()
        cooling = {label for label, until in _cooldown_until.items() if until > now}
    groups: dict[str, list[Endpoint]] = {}
    for ep in pool:
        groups.setdefault(ep.provider, []).append(ep)
    ordered: list[Endpoint] = []
    for members in groups.values():
        k = turn % len(members)
        ordered.extend(members[k:] + members[:k])
    return [e for e in ordered if e.label not in cooling] + [
        e for e in ordered if e.label in cooling
    ]


def _count_request() -> None:
    global _requests
    with _lock:
        _requests += 1


def _cool(ep: Endpoint, seconds: float) -> None:
    with _lock:
        _cooldown_until[ep.label] = time.monotonic() + seconds


class _EndpointFailure(Exception):
    def __init__(self, reason: str, *, retryable: bool, cooldown_s: float) -> None:
        super().__init__(reason)
        self.reason = reason
        self.retryable = retryable
        self.cooldown_s = cooldown_s


# ---- public entry point ----------------------------------------------------------------


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

    Order: mock (MOCK_LLM=1), then disk cache, then the provider pool.
    """
    if role not in ROLES:
        raise ValueError(f"unknown LLM role: {role}")

    settings = get_settings()

    if settings.mock_llm:
        raw = load_mock(role, key)
        if raw is None:
            raise LLMError(f"No mock fixture for role '{role}' (key={key}).")
        _last.model_id = "mock"
        return _validate(schema, raw)

    pool = build_pool(settings)
    signature = "|".join(sorted({e.model_id for e in pool}))
    cache_key = cache.make_key(
        provider="pool",
        model=signature,
        role=role,
        prompt_version=prompt_version,
        system=system,
        user=user,
        temperature=temperature,
    )
    if settings.llm_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            data, model_id = _unwrap_cached(cached)
            try:
                result = _validate(schema, data)
                _last.model_id = model_id
                return result
            except LLMError:
                pass  # stale or corrupt cache entry: fall through to a fresh call

    result = _call_with_repair(
        pool=pool,
        system=system,
        user=user,
        schema=schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if settings.llm_cache:
        cache.put(
            cache_key,
            {"_model_id": last_model_id(), "_data": result.model_dump(mode="json")},
        )
    return result


def _unwrap_cached(cached: Any) -> tuple[Any, str | None]:
    if isinstance(cached, dict) and "_data" in cached:
        return cached["_data"], cached.get("_model_id")
    return cached, None  # entry written before the pool existed


def _validate(schema: type[T], raw: Any) -> T:
    try:
        return schema.model_validate(raw)
    except ValidationError as exc:
        raise LLMError(f"LLM output did not match {schema.__name__}.") from exc


def _call_with_repair(
    *,
    pool: list[Endpoint],
    system: str,
    user: str,
    schema: type[T],
    temperature: float,
    max_tokens: int,
) -> T:
    """Call the pool. If the output is not valid JSON for `schema`, retry once."""
    text = _call_provider(
        pool, system=system, user=user, temperature=temperature, max_tokens=max_tokens
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
            pool, system=system, user=repair_user, temperature=temperature, max_tokens=max_tokens
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


# ---- provider calls --------------------------------------------------------------------


def _call_provider(
    pool: list[Endpoint], *, system: str, user: str, temperature: float, max_tokens: int
) -> str:
    """Try endpoints in rotation order until one answers. Returns the reply text."""
    settings = get_settings()
    if not pool:
        raise LLMError(
            "LLM provider is not configured. Set LLM_PROVIDER and keys in backend/.env "
            "(LLM_GROQ_KEYS, LLM_GEMINI_KEYS or LLM_API_KEY), or set MOCK_LLM=1."
        )

    candidates = _ordered_candidates(pool)
    single = len(candidates) == 1
    deadline = time.monotonic() + max(MIN_TOTAL_BUDGET_S, 2 * settings.llm_timeout_s)
    failures: list[str] = []
    attempt = 0
    while attempt < len(candidates) + (1 if single else 0):
        ep = candidates[attempt % len(candidates)]
        attempt += 1
        _count_request()
        try:
            with httpx.Client(timeout=settings.llm_timeout_s, transport=_transport) as client:
                text = _request(client, ep, system, user, temperature, max_tokens)
            _last.model_id = ep.model_id
            return text
        except _EndpointFailure as failure:
            failures.append(f"{ep.label}: {failure.reason}")
            log.info("LLM endpoint %s failed: %s", ep.label, failure.reason)
            _cool(ep, failure.cooldown_s)
            if single and not failure.retryable:
                break
        if time.monotonic() > deadline:
            failures.append("time budget used up")
            break
    raise LLMError(
        f"LLM unavailable after trying {min(attempt, len(candidates))} endpoint(s): "
        + "; ".join(failures)
        + "."
    )


def _fail_for_status(res: httpx.Response) -> _EndpointFailure:
    status = res.status_code
    reason = f"HTTP {status}"
    if status == 429:
        try:
            wait = float(res.headers.get("retry-after", COOLDOWN_RATE_LIMIT_S))
        except ValueError:
            wait = COOLDOWN_RATE_LIMIT_S
        return _EndpointFailure(reason, retryable=True, cooldown_s=min(120.0, max(5.0, wait)))
    if status >= 500:
        return _EndpointFailure(reason, retryable=True, cooldown_s=COOLDOWN_SERVER_S)
    if status in (401, 403):
        return _EndpointFailure(reason, retryable=False, cooldown_s=COOLDOWN_BAD_KEY_S)
    return _EndpointFailure(reason, retryable=False, cooldown_s=COOLDOWN_OTHER_4XX_S)


def _post_dropping_unsupported(
    client: httpx.Client, url: str, body: dict[str, Any], headers: dict[str, str],
    optional: tuple[str, ...],
) -> httpx.Response:
    """POST. If the server rejects an optional parameter (HTTP 400 naming it), drop it, retry."""
    res = client.post(url, json=body, headers=headers)
    for name in optional:
        if res.status_code == 400 and name in body and name in res.text.lower():
            body.pop(name)
            res = client.post(url, json=body, headers=headers)
    return res


def _request(
    client: httpx.Client, ep: Endpoint, system: str, user: str, temperature: float, max_tokens: int
) -> str:
    try:
        if ep.provider == "anthropic":
            return _anthropic(client, ep, system, user, temperature, max_tokens)
        return _openai_style(client, ep, system, user, temperature, max_tokens)
    except httpx.TimeoutException:
        raise _EndpointFailure(
            "timeout", retryable=True, cooldown_s=COOLDOWN_SERVER_S
        ) from None
    except httpx.HTTPError as exc:
        raise _EndpointFailure(
            type(exc).__name__, retryable=True, cooldown_s=COOLDOWN_SERVER_S
        ) from None


def _openai_style(
    client: httpx.Client, ep: Endpoint, system: str, user: str, temperature: float, max_tokens: int
) -> str:
    # OpenAI's newer models want max_completion_tokens; other servers still use max_tokens.
    token_field = "max_completion_tokens" if ep.provider == "openai" else "max_tokens"
    body: dict[str, Any] = {
        "model": ep.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        token_field: max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    # Reasoning models spend output tokens on thinking. Keep that small for fast JSON answers.
    if ep.provider == "gemini":
        body["reasoning_effort"] = "none"
    elif ep.provider == "groq" and "gpt-oss" in ep.model:
        body["reasoning_effort"] = "low"
        body[token_field] = max_tokens + 1500  # headroom for the reasoning tokens
    headers = {"Authorization": f"Bearer {ep.api_key}"}
    res = _post_dropping_unsupported(
        client, f"{ep.base_url}/chat/completions", body, headers,
        optional=("temperature", "reasoning_effort"),
    )
    if res.status_code >= 400:
        raise _fail_for_status(res)
    try:
        return str(res.json()["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError, ValueError):
        raise _EndpointFailure(
            "unexpected response shape", retryable=False, cooldown_s=COOLDOWN_OTHER_4XX_S
        ) from None


def _anthropic(
    client: httpx.Client, ep: Endpoint, system: str, user: str, temperature: float, max_tokens: int
) -> str:
    body: dict[str, Any] = {
        "model": ep.model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {"x-api-key": ep.api_key, "anthropic-version": ANTHROPIC_VERSION}
    res = _post_dropping_unsupported(
        client, f"{ep.base_url}/messages", body, headers, optional=("temperature",)
    )
    if res.status_code >= 400:
        raise _fail_for_status(res)
    try:
        parts = res.json()["content"]
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    except (KeyError, TypeError, ValueError, AttributeError):
        raise _EndpointFailure(
            "unexpected response shape", retryable=False, cooldown_s=COOLDOWN_OTHER_4XX_S
        ) from None
