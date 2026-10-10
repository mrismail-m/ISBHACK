"""LLM client: JSON parsing, provider requests, repair retry, transient retry, cache."""

import json

import httpx
import pytest
from pydantic import BaseModel

from app.config import get_settings
from app.llm import client
from app.llm.client import LLMError, complete_json, extract_json


class Answer(BaseModel):
    value: int


def _use_provider(monkeypatch: pytest.MonkeyPatch, provider: str, **extra: str) -> None:
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    for name, value in extra.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()


def _openai_reply(text: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def _call() -> Answer:
    return complete_json(
        role="grader", system="s", user="u", schema=Answer, prompt_version="t-v1"
    )


def test_extract_json_handles_fences_and_surrounding_text() -> None:
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 1} Hope that helps.') == {"a": 1}
    with pytest.raises(ValueError):
        extract_json("no json here")


def test_mock_mode_uses_fixture_and_needs_no_key() -> None:
    from app.ai.grader import GraderOutput

    out = complete_json(
        role="grader",
        system="s",
        user="u",
        schema=GraderOutput,
        prompt_version="grader-v1",
        key="s_1",
    )
    assert len(out.criteria) == 4


def test_unconfigured_provider_fails_with_llm_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_LLM", "0")
    get_settings.cache_clear()
    with pytest.raises(LLMError, match="not configured"):
        _call()


def test_openai_request_shape_and_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return _openai_reply('{"value": 7}')

    monkeypatch.setattr(client, "_transport", httpx.MockTransport(handler))
    _use_provider(monkeypatch, "openai")
    assert _call().value == 7
    assert seen["url"] == "https://api.openai.com/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert seen["body"]["temperature"] == 0.0
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert seen["body"]["messages"][0] == {"role": "system", "content": "s"}


def test_anthropic_request_shape_and_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers["x-api-key"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"content": [{"type": "text", "text": '{"value": 3}'}]})

    monkeypatch.setattr(client, "_transport", httpx.MockTransport(handler))
    _use_provider(monkeypatch, "anthropic")
    assert _call().value == 3
    assert seen["url"] == "https://api.anthropic.com/v1/messages"
    assert seen["key"] == "test-key"
    assert seen["body"]["system"] == "s"


def test_openai_compatible_requires_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_provider(monkeypatch, "openai_compatible")
    with pytest.raises(LLMError, match="LLM_BASE_URL"):
        _call()


def test_one_repair_retry_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    replies = iter(["not json at all", '{"value": 2}'])
    users: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        users.append(json.loads(request.content)["messages"][1]["content"])
        return _openai_reply(next(replies))

    monkeypatch.setattr(client, "_transport", httpx.MockTransport(handler))
    _use_provider(monkeypatch, "openai")
    assert _call().value == 2
    assert len(users) == 2
    assert "not valid JSON" in users[1]


def test_bad_output_twice_raises_llm_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return _openai_reply('{"wrong": true}')

    monkeypatch.setattr(client, "_transport", httpx.MockTransport(handler))
    _use_provider(monkeypatch, "openai")
    with pytest.raises(LLMError):
        _call()
    assert calls["n"] == 2


def test_retries_once_on_503(monkeypatch: pytest.MonkeyPatch) -> None:
    replies = iter([httpx.Response(503), _openai_reply('{"value": 5}')])
    monkeypatch.setattr(
        client, "_transport", httpx.MockTransport(lambda request: next(replies))
    )
    _use_provider(monkeypatch, "openai")
    assert _call().value == 5


def test_two_failures_raise_llm_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client, "_transport", httpx.MockTransport(lambda request: httpx.Response(429))
    )
    _use_provider(monkeypatch, "openai")
    with pytest.raises(LLMError, match="unavailable"):
        _call()


def test_client_error_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401)

    monkeypatch.setattr(client, "_transport", httpx.MockTransport(handler))
    _use_provider(monkeypatch, "openai")
    with pytest.raises(LLMError, match="401"):
        _call()
    assert calls["n"] == 1


def test_temperature_rejection_retries_without_it(monkeypatch: pytest.MonkeyPatch) -> None:
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        bodies.append(body)
        if "temperature" in body:
            return httpx.Response(400, text="Unsupported value: temperature")
        return _openai_reply('{"value": 9}')

    monkeypatch.setattr(client, "_transport", httpx.MockTransport(handler))
    _use_provider(monkeypatch, "openai")
    assert _call().value == 9
    assert "temperature" not in bodies[-1]


def test_cache_avoids_second_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    store: dict[str, object] = {}
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return _openai_reply('{"value": 4}')

    monkeypatch.setattr(client, "_transport", httpx.MockTransport(handler))
    monkeypatch.setattr(client.cache, "get", lambda key: store.get(key))
    monkeypatch.setattr(client.cache, "put", lambda key, value: store.__setitem__(key, value))
    _use_provider(monkeypatch, "openai", LLM_CACHE="1")
    assert _call().value == 4
    assert _call().value == 4
    assert calls["n"] == 1
