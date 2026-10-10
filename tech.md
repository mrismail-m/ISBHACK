---
inclusion: always
---

# Tech

## Stack
- **Frontend:** Vite, React 18, TypeScript (strict), Tailwind CSS, React Router, Recharts, CodeMirror 6 (`@codemirror/state`, `@codemirror/view`, `@codemirror/lang-markdown`), react-markdown. Tests: vitest.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLModel on SQLite, Uvicorn. Tests: pytest. Lint: ruff.
- **AI:** one provider behind `backend/app/llm/client.py` (`complete_json`). Prompts live in `backend/app/ai/prompts/`.
- **Auth:** none. A role switcher sends `X-User-Id`. Seeded users only.

## URLs
Backend `http://localhost:8000` (API under `/api/v1`, interactive docs at `/docs`). Frontend `http://localhost:5173`.

## Commands
- Backend: `cd backend && uvicorn app.main:app --reload --port 8000`
- Seed or reset data: `cd backend && python -m app.seed --reset`
- Backend checks: `cd backend && pytest -q && ruff check .`
- Frontend: `cd frontend && npm run dev`
- Frontend checks: `cd frontend && npm run typecheck && npm run lint && npm test`
- Golden path smoke test: `python scripts/smoke.py`
- Trust report: `cd backend && python -m eval.run_eval --all`

## Environment variables

Backend `.env`:

| Variable | Default | Meaning |
|---|---|---|
| `MOCK_LLM` | `0` | `1` returns canned outputs from `fixtures/api/llm/` instead of calling the provider |
| `LLM_PROVIDER` | set at M0 | provider id used by `llm/client.py` |
| `LLM_MODEL` | set at M0 | model name |
| `LLM_API_KEY` | none | secret, never committed |
| `LLM_CACHE` | `1` | `0` disables the response cache (used for consistency tests) |
| `LLM_TIMEOUT_S` | `30` | per call timeout |
| `DATABASE_URL` | `sqlite:///./vivagrade.db` | database |
| `GRADE_ON_SUBMIT` | `1` | start background grading when a student submits |
| `CORS_ORIGINS` | `http://localhost:5173` | allowed origins |

Frontend `.env`:

| Variable | Default | Meaning |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | backend base URL |
| `VITE_USE_FIXTURES` | `0` | `1` serves responses from `fixtures/api/` with no backend |

## Conventions
- JSON is snake_case. Timestamps are ISO 8601 UTC. IDs are opaque strings.
- Errors: `{ "error": { "code": "...", "message": "..." } }`.
- Criterion marks and work totals are multiples of 0.5. Blended final marks have 1 decimal. Percentages are floats with 1 decimal. Understanding and confidence are 0 to 1.
- Vite alias `@fixtures` points to `../fixtures` (add the repo root to `server.fs.allow`).
- Only `backend/app/llm/client.py` calls an LLM provider.
