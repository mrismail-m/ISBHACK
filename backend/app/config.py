"""App settings, read from environment variables and backend/.env.

Variable names and defaults follow .kiro/steering/tech.md.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> parents: app, backend, repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "fixtures"
LLM_FIXTURES_DIR = FIXTURES_DIR / "api" / "llm"
LLM_CACHE_DIR = REPO_ROOT / ".cache" / "llm"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mock_llm: bool = False
    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    # Optional base URL for OpenAI-compatible servers. Empty = provider default.
    llm_base_url: str = ""
    # Key pool. Comma separated. Calls rotate over a provider's keys and fall back to the
    # next key, then the next provider in LLM_ORDER (default: LLM_PROVIDER only).
    llm_order: str = ""
    llm_groq_keys: str = ""
    llm_groq_model: str = "openai/gpt-oss-120b"
    llm_gemini_keys: str = ""
    llm_gemini_model: str = "gemini-3.5-flash"
    llm_cache: bool = True
    llm_timeout_s: int = 30
    database_url: str = "sqlite:///./vivagrade.db"
    grade_on_submit: bool = True
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
