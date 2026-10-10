"""Writing activity endpoints. Owner: Majid. Contract: docs/api-contract.md.

Skeleton from Adeel (M0.1): every route returns 501. Majid replaces this file (M1.2, M2.3).
"""

from fastapi import APIRouter

from app.deps import not_implemented

router = APIRouter(tags=["activity"])
OWNER = "Majid"


@router.post("/submissions/{submission_id}/activity")
def ingest_activity(submission_id: str) -> None:
    not_implemented(OWNER)


@router.get("/submissions/{submission_id}/activity/summary")
def get_activity_summary(submission_id: str) -> None:
    not_implemented(OWNER)


@router.get("/submissions/{submission_id}/activity/events")
def get_activity_events(submission_id: str) -> None:
    not_implemented(OWNER)


@router.post("/submissions/{submission_id}/activity/paste-declaration")
def declare_paste(submission_id: str) -> None:
    not_implemented(OWNER)
