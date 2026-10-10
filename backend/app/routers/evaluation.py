"""Evaluation endpoint. Owner: Adeel. Contract: docs/api-contract.md. Task: M4.1.

Serves backend/eval/reports/trust_report.json, which `python -m eval.run_eval` writes.
"""

from pathlib import Path

from fastapi import APIRouter

from app.deps import ApiError
from app.schemas.grading import TrustReport

REPORT_PATH = Path(__file__).resolve().parents[2] / "eval" / "reports" / "trust_report.json"

router = APIRouter(tags=["evaluation"])


@router.get("/evaluation/trust-report", response_model=TrustReport)
def get_trust_report() -> TrustReport:
    if not REPORT_PATH.exists():
        raise ApiError(
            404,
            "not_found",
            "The trust report has not been generated yet. Run: python -m eval.run_eval --quick",
        )
    return TrustReport.model_validate_json(REPORT_PATH.read_text(encoding="utf-8"))
