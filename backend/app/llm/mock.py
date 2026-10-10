"""MOCK_LLM=1 support: return canned outputs from fixtures/api/llm/."""

import json
from pathlib import Path
from typing import Any

from app.config import LLM_FIXTURES_DIR


def load_mock(role: str, key: str | None, fixtures_dir: Path = LLM_FIXTURES_DIR) -> Any | None:
    """Return fixtures/api/llm/{role}_{key}.json, else {role}.json, else None.

    `key` is the submission id with underscores removed (s_1 becomes s1).
    """
    candidates: list[Path] = []
    if key:
        candidates.append(fixtures_dir / f"{role}_{key.replace('_', '')}.json")
    candidates.append(fixtures_dir / f"{role}.json")
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None
