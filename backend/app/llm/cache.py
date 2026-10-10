"""On-disk response cache for LLM calls, keyed by a hash of the full input."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.config import LLM_CACHE_DIR


def make_key(
    *,
    provider: str,
    model: str,
    role: str,
    prompt_version: str,
    system: str,
    user: str,
    temperature: float,
) -> str:
    payload = json.dumps(
        {
            "provider": provider,
            "model": model,
            "role": role,
            "prompt_version": prompt_version,
            "system": system,
            "user": user,
            "temperature": temperature,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _path(key: str, cache_dir: Path) -> Path:
    return cache_dir / f"{key}.json"


def get(key: str, cache_dir: Path = LLM_CACHE_DIR) -> Any | None:
    path = _path(key, cache_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def put(key: str, value: Any, cache_dir: Path = LLM_CACHE_DIR) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    _path(key, cache_dir).write_text(
        json.dumps(value, ensure_ascii=False), encoding="utf-8"
    )
