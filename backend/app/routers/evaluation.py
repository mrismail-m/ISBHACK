"""Evaluation endpoint. Owner: Adeel. Contract: docs/api-contract.md.

Will read backend/eval/reports/trust_report.json (M4.1). Skeleton: returns 501.
"""

from fastapi import APIRouter

from app.deps import not_implemented

router = APIRouter(tags=["evaluation"])
OWNER = "Adeel"


@router.get("/evaluation/trust-report")
def get_trust_report() -> None:
    not_implemented(OWNER)
