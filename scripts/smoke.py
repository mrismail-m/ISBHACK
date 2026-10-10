"""Golden path smoke test. Prints PASS or FAIL per step. Task: M1.1 (v0 below is health only).

Usage: python scripts/smoke.py [base_url]   (backend must be running)
"""

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/") + "/api/v1"


def call(method: str, path: str) -> tuple[int, dict]:
    req = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")
    except urllib.error.URLError as exc:
        return 0, {"error": {"code": "unreachable", "message": str(exc.reason)}}


def main() -> int:
    steps = [("health", "GET", "/health", 200)]
    failed = 0
    for name, method, path, expected in steps:
        status, _ = call(method, path)
        ok = status == expected
        failed += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({method} {path} -> {status})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
