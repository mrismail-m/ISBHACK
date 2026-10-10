"""Viva endpoints. Owner: Adeel. Contract: docs/api-contract.md.

Skeleton: every route returns 501 until implemented (M3.1).
"""

from fastapi import APIRouter

from app.deps import not_implemented

router = APIRouter(tags=["viva"])
OWNER = "Adeel"


@router.post("/submissions/{submission_id}/viva/start")
def start_viva(submission_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/viva/answer")
def answer_viva(submission_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/viva/finish")
def finish_viva(submission_id: str) -> None:
    not_implemented(OWNER)


@router.get("/submissions/{submission_id}/viva")
def get_viva(submission_id: str) -> None:
    not_implemented(OWNER)
