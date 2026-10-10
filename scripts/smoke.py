"""Golden path smoke test. Prints PASS or FAIL per step, never crashes on a missing endpoint.

Usage: python scripts/smoke.py [base_url]   (backend must be running, ideally with MOCK_LLM=1)
Env:   SMOKE_STUDENT (default u_student_1), SMOKE_TEACHER (default u_teacher_1),
       SMOKE_ASSESSMENT (default a_1)

Steps follow AGENTS.md section 7. A step that depends on an earlier failed step is
reported as FAIL with "skipped". Exit code is 1 if any step fails.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/") + "/api/v1"
STUDENT = os.getenv("SMOKE_STUDENT", "u_student_1")
TEACHER = os.getenv("SMOKE_TEACHER", "u_teacher_1")
ASSESSMENT = os.getenv("SMOKE_ASSESSMENT", "a_1")

TEXT = (
    "# Collisions\n\nA collision happens when two keys map to the same index. "
    "Chaining keeps a list in each slot. Open addressing probes for the next free slot. "
    "Lookups are O(1) on average and O(n) in the worst case."
)


def call(
    method: str, path: str, body: dict | None = None, user: str | None = None
) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if user:
        req.add_header("X-User-Id", user)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read() or b"{}"
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": {"code": "bad_body", "message": raw[:80].decode()}}
    except urllib.error.URLError as exc:
        return 0, {"error": {"code": "unreachable", "message": str(exc.reason)}}


def error_text(payload: Any) -> str:
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        err = payload["error"]
        return f"{err.get('code')}: {err.get('message')}"
    return ""


class Smoke:
    def __init__(self) -> None:
        self.failed = 0
        self.ctx: dict[str, Any] = {}

    def step(self, name: str, fn: Callable[[], str]) -> None:
        """`fn` returns a short note, or raises AssertionError(reason) to fail."""
        try:
            note = fn()
            print(f"PASS  {name}  {note}".rstrip())
        except AssertionError as exc:
            self.failed += 1
            print(f"FAIL  {name}  ({exc})")
        except KeyError as exc:
            self.failed += 1
            print(f"FAIL  {name}  (skipped, missing earlier result: {exc})")

    # ---- steps -----------------------------------------------------------------------

    def health(self) -> str:
        status, body = call("GET", "/health")
        assert status == 200, f"GET /health -> {status} {error_text(body)}"
        return f"(mock_llm={body.get('mock_llm')})"

    def teacher_sees_settings(self) -> str:
        status, body = call("GET", f"/assessments/{ASSESSMENT}", user=TEACHER)
        assert status == 200, f"GET /assessments/{ASSESSMENT} -> {status} {error_text(body)}"
        for field in ("strictness", "viva_weight", "feedback_mode", "release_mode", "ai_policy"):
            assert field in body, f"assessment is missing '{field}'"
        return f"(strictness={body['strictness']}, viva_weight={body['viva_weight']})"

    def student_starts(self) -> str:
        status, body = call("POST", f"/assessments/{ASSESSMENT}/submissions", {}, user=STUDENT)
        assert status == 200, f"start submission -> {status} {error_text(body)}"
        self.ctx["sid"] = body["id"]
        self.ctx["status"] = body["status"]
        return f"({body['id']}, {body['status']})"

    def student_writes_and_submits(self) -> str:
        sid = self.ctx["sid"]
        if self.ctx["status"] != "draft":
            return f"(already {self.ctx['status']}, reusing)"
        status, body = call("PUT", f"/submissions/{sid}", {"content_md": TEXT}, user=STUDENT)
        assert status == 200, f"PUT submission -> {status} {error_text(body)}"
        status, body = call("POST", f"/submissions/{sid}/submit", {}, user=STUDENT)
        assert status == 200, f"submit -> {status} {error_text(body)}"
        return f"(status={body['status']})"

    def grade(self) -> str:
        sid = self.ctx["sid"]
        status, body = call("POST", f"/submissions/{sid}/grade", {}, user=TEACHER)
        assert status == 200, f"POST grade -> {status} {error_text(body)}"
        assert body["criteria"], "grade has no criteria"
        self.ctx["grade"] = body
        return f"(ai_total={body['ai_total']}/{body['max_marks']}, flags={body['grader_flags']})"

    def get_grade(self) -> str:
        status, body = call("GET", f"/submissions/{self.ctx['sid']}/grade", user=TEACHER)
        assert status == 200, f"GET grade -> {status} {error_text(body)}"
        assert body["ai_total"] == self.ctx["grade"]["ai_total"], "saved grade differs"
        return ""

    def viva(self) -> str:
        sid = self.ctx["sid"]
        status, body = call("POST", f"/submissions/{sid}/viva/start", {}, user=STUDENT)
        assert status == 200, f"viva/start -> {status} {error_text(body)}"
        questions = body["questions"]
        for q in questions:
            answer = {
                "question_id": q["id"],
                "answer_text": "Because the lists or probe runs get longer as the table fills.",
                "time_taken_s": 20,
                "pasted": False,
                "tab_switches": 0,
            }
            status, res = call("POST", f"/submissions/{sid}/viva/answer", answer, user=STUDENT)
            assert status == 200, f"viva/answer -> {status} {error_text(res)}"
        status, res = call("POST", f"/submissions/{sid}/viva/finish", {}, user=STUDENT)
        assert status == 200, f"viva/finish -> {status} {error_text(res)}"
        return f"(understanding={res['understanding']})"

    def approve_and_release(self) -> str:
        sid = self.ctx["sid"]
        body = {"criteria_overrides": [], "teacher_note": "Smoke test.", "release": True}
        status, res = call("POST", f"/submissions/{sid}/approve", body, user=TEACHER)
        assert status == 200, f"approve -> {status} {error_text(res)}"
        return f"(status={res['status']})"

    def student_result(self) -> str:
        status, res = call("GET", f"/submissions/{self.ctx['sid']}/result", user=STUDENT)
        assert status == 200, f"result -> {status} {error_text(res)}"
        return f"(final_marks={res['final_marks']})"

    def dashboard(self) -> str:
        status, res = call("GET", f"/assessments/{ASSESSMENT}/stats", user=TEACHER)
        assert status == 200, f"stats -> {status} {error_text(res)}"
        status, res = call(
            "POST", f"/assessments/{ASSESSMENT}/grace/preview", {"marks": 1}, user=TEACHER
        )
        assert status == 200, f"grace/preview -> {status} {error_text(res)}"
        return f"(affected={res['affected_students']})"


def main() -> int:
    s = Smoke()
    s.step("0 health", s.health)
    s.step("1 teacher sees assessment settings", s.teacher_sees_settings)
    s.step("2a student opens the assessment", s.student_starts)
    s.step("2b student writes and submits", s.student_writes_and_submits)
    s.step("4a AI grade (POST)", s.grade)
    s.step("4b AI grade (GET)", s.get_grade)
    s.step("3 student takes the viva", s.viva)
    s.step("4c teacher approves and releases", s.approve_and_release)
    s.step("5 student sees result", s.student_result)
    s.step("6 dashboard stats and grace preview", s.dashboard)
    total = 10
    print(f"\n{total - s.failed}/{total} steps passed")
    return 1 if s.failed else 0


if __name__ == "__main__":
    sys.exit(main())
