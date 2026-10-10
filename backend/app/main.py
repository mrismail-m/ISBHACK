"""App factory and router registration. Adeel only.

Others: ask Adeel for a router registration line instead of editing this file.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import create_db_and_tables
from app.deps import ApiError
from app.llm.client import LLMError
from app.models import grading as _grading_models  # noqa: F401  (registers tables)
from app.routers import (
    activity,
    analytics,
    assessments,
    evaluation,
    grading,
    submissions,
    viva,
)

API_PREFIX = "/api/v1"


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Idempotent. Makes sure grades and viva_sessions exist even on an old database.
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="VivaGrade API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _error(exc.status_code, exc.code, exc.message)

    @app.exception_handler(LLMError)
    async def _llm_error(_: Request, exc: LLMError) -> JSONResponse:
        return _error(502, "llm_unavailable", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(422, "validation_error", "Request validation failed.")

    @app.get(f"{API_PREFIX}/health", tags=["health"])
    def health() -> dict[str, object]:
        return {"status": "ok", "mock_llm": settings.mock_llm}

    for module in (
        assessments,
        submissions,
        grading,
        viva,
        activity,
        analytics,
        evaluation,
    ):
        app.include_router(module.router, prefix=API_PREFIX)

    return app


app = create_app()
