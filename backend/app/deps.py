"""Shared FastAPI helpers: error envelope and the current user header."""

from typing import NoReturn

from fastapi import Header


class ApiError(Exception):
    """Raised anywhere in a request. main.py turns it into the contract error envelope."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def not_implemented(owner: str) -> NoReturn:
    """Skeleton stub for endpoints that are not built yet. Remove the call when you implement it."""
    raise ApiError(501, "not_implemented", f"Not implemented yet (owner: {owner}).")


def current_user_id(x_user_id: str | None = Header(default=None)) -> str | None:
    """The role switcher sends X-User-Id. There is no real auth (see ADR-6)."""
    return x_user_id
