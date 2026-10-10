# AGENTS.md

Instructions for every coding agent on this repo (Kiro loads this file automatically). Three people build in parallel, each with their own agent session: **Adeel**, **Majid**, **Ismail**. Read this fully, then follow the session protocol.

## 1. Project in 30 seconds

**VivaGrade** (working name; tagline "grade the work, verify the learning") is a teacher copilot for Islamabad Hack 2026, track Education & Future of Work. It does not replace teachers: AI drafts, the teacher decides, students learn.

- AI grades each submission against the teacher's locked rubric at a teacher-chosen strictness (`lenient`, `normal`, `strict`, `very_strict`), with a verbatim evidence quote per criterion, then writes student feedback (what went well, what to improve).
- The student then defends their own work in a short AI-run viva (3 timed questions about their own submission). The understanding score blends into the final grade.
- Students write in a markdown editor that records the writing process. Teachers see paste chunks, an authorship map, an activity heatmap and a replay.
- Teachers get a dashboard (stats, graphs, students needing attention) and a grace-marks button.

Constraints: built on-site on 10 Oct 2026. The pitch is 4 minutes (1 problem and solution, 2 live demo, 1 Q&A). Scoring: Problem 20, Creativity 20, Prototype 20, Impact 15, Kiro use 15, Presentation 10. **A working golden path beats breadth.**

## 2. Session protocol (every session, no exceptions)

**Start**
1. Find out who you work for (Adeel, Majid or Ismail). If the human has not said, ask once.
2. Run `git pull --rebase origin main`.
3. Read only what you need, in this order: `docs/progress.md` (Current snapshot, Integration status, your member's last 5 log entries), the current milestone in `docs/roadmap.md`, then the parts of `docs/api-contract.md` and `docs/architecture.md` that touch your task.
4. State in 5 lines or fewer: task ID, files you will touch, what you will mock, first step.

**During**
- Work in small steps. After each step print one line: `DONE: <what>` or `BLOCKED: <why>`.
- Commit every 20 to 30 minutes, small and green.
- If a task is not working after 20 minutes, stop, log the blocker in `docs/progress.md`, and use the fallback listed under "Cut lines" in `docs/roadmap.md`.

**End (or before any long pause)**
1. Run the checks for the parts you touched (section 9).
2. Append one entry to your own log in `docs/progress.md` (template inside that file) and update your row in "Current snapshot".
3. Tick finished boxes in `docs/roadmap.md`.
4. Commit and push. Docs-only edits to `progress.md` and `roadmap.md` may go straight to `main`.

Write progress entries for a reader with zero memory: facts, file paths, next step. No code dumps, no filler.

## 3. Ownership map (scope lock)

You MUST edit only paths your member owns. Need a change elsewhere? Ask the owner through the human, or add it under "Needs from others" in your progress entry. Ownership is a default: if the team swaps work, edit this table in the same commit and tell everyone.

| Member | Slice | Backend paths | Frontend paths | Other |
|---|---|---|---|---|
| Adeel | AI core, integration, evaluation | `app/llm/`, `app/ai/`, `app/routers/grading.py`, `app/routers/viva.py`, `app/models/grading.py`, `app/schemas/grading.py`, `app/schemas/viva.py`, `app/main.py`, `app/config.py`, `app/deps.py`, `eval/` | none | `scripts/`, `.env.example`, `.gitignore`, `fixtures/eval/`, `fixtures/api/llm/`, `docs/ai-spec.md`, `docs/evaluation.md` |
| Majid | Student app, writing evidence | `app/routers/activity.py`, `app/services/activity_summary.py`, `app/models/activity.py`, `app/schemas/activity.py` | `src/features/student/`, `src/features/insights/`, `src/lib/replay-core/`, `src/api/client.ts`, `src/api/student.ts`, `src/api/activity.ts`, `src/routes.tsx` | `fixtures/activity/` |
| Ismail | Teacher console, data and API | `app/db.py`, `app/models/core.py`, `app/models/__init__.py`, `app/schemas/core.py`, `app/schemas/analytics.py`, `app/routers/assessments.py`, `app/routers/submissions.py`, `app/routers/analytics.py`, `app/services/scoring.py`, `app/services/flags.py`, `app/services/analytics.py`, `app/services/grace.py`, `app/seed.py` | `src/features/teacher/`, `src/components/ui/`, `src/api/teacher.ts` | `fixtures/api/` (except `llm/`) |

Backend paths are under `backend/`, frontend paths under `frontend/`.

Shared files:

| File | Rule |
|---|---|
| `docs/api-contract.md`, `backend/app/schemas/*`, `frontend/src/api/types.ts` | The contract. Change only through the protocol in section 5. |
| `backend/app/main.py` | Adeel only. Others ask for a router registration line. |
| `frontend/src/routes.tsx` | Majid creates it. Ismail may add teacher route lines. |
| `docs/progress.md` | Edit your own section only. Append-only for "Contract changes" and "Decisions". |
| `docs/roadmap.md` | Tick your own boxes only. |
| `frontend/src/components/` | Ismail owns `ui/`. Majid adds under `student/`. |

## 4. Golden rules

1. **Contract first.** Build against `docs/api-contract.md`. Never invent fields.
2. **Mock first.** Every endpoint MUST work with `MOCK_LLM=1`, and every screen MUST work with `VITE_USE_FIXTURES=1`, so nobody waits on you.
3. **The model never computes marks.** It classifies levels and quotes evidence. Code computes marks.
4. **Evidence or it did not happen.** Every evidence quote MUST be verified as a verbatim substring of the submission.
5. **AI drafts, teacher decides.** Nothing is released to a student before approval unless `release_mode` is `auto`.
6. **Signals, not verdicts.** Writing-process data and viva scores raise flags for the teacher. They never change a mark on their own, except through the teacher-set viva weight.
7. **No student identity in prompts.** Names, emails and IDs NEVER go to the LLM. Activity logs NEVER go to the LLM.
8. **Protect the golden path.** It must work on `main` at every sync.
9. **Stay in your lane.** See section 3.
10. **Time-box.** 20 minutes stuck means log it and take the fallback.

## 5. Contract change protocol

1. Propose in the group chat. Wait for a thumbs up from every consumer.
2. In ONE commit update `docs/api-contract.md`, the Pydantic schema, `frontend/src/api/types.ts` and the fixtures.
3. Add a `CONTRACT CHANGE` entry in `docs/progress.md`.
4. Consumers adapt within 15 minutes. Never change a field's meaning silently: add a new field instead.

## 6. Briefs per member

### Adeel: AI core, integration, evaluation
- **Mission:** make the AI trustworthy, explainable and cheap to demo.
- **Provide:** `llm/client.py` (`complete_json`), rubric drafting, level-based grader with strictness, feedback, viva (questions and scoring), MCQ grading, `trust_report.json`, `scripts/smoke.py`.
- **Consume:** assessment and submission models from Ismail. `ActivitySummary` only in tests.
- **Tasks:** M0.1, M1.1, M2.1, M2.2, M3.1, M4.1, M4.4, M5.x.
- **Follow exactly:** `docs/ai-spec.md` (levels, strictness table, evidence verification, injection guard) and `docs/evaluation.md`.
- **Integration owner duties:** owns `backend/app/main.py`; tags `contract-v1`, `m1-ok`, `m2-ok`, `m3-ok`, `demo-v1`; runs `scripts/smoke.py` at every sync; decides reverts.
- **Done means:** works in mock and real mode, unit tests for strictness mapping and quote verification, prompt version strings set, demo submissions cached.

### Majid: student app, writing evidence
- **Mission:** a smooth student experience and writing-process evidence a teacher can read in 10 seconds.
- **Provide:** student UI (assessment list, editor, viva screen, result and feedback), `lib/replay-core`, insights components (paste chunks, authorship map, heatmap, replay viewer), activity ingestion and summary on the backend, `fixtures/activity/` (sample logs with expected summaries, used as parity tests).
- **Consume:** submissions API (Ismail), viva API (Adeel), result API (Ismail).
- **Tasks:** M0.2, M1.2, M2.3, M3.2, M4.2.
- **Follow exactly:** `docs/architecture.md` section 7 (capture, event schema, authorship, internal paste rule, UTF-16 positions).
- **Rules:** capture only inside the editor; show a visible "what is recorded" banner; `typed_pct` and `pasted_pct` MUST match between `activity_summary.py` and `replay-core` within 1 percentage point on every fixture.
- **Done means:** a 10 minute session round-trips through capture, storage, summary and replay with the paste highlighted.

### Ismail: teacher console, data and API
- **Mission:** give teachers control and clarity: setup, review, dashboard.
- **Provide:** DB and seed, assessments, submissions and analytics routers, `services/scoring.py` (blend and grace), `services/flags.py`, teacher UI (setup with strictness and options, rubric editor, review queue with blind mode, review detail with evidence, override, approve and release, dashboard, grace marks, trust report page), shared UI components.
- **Consume:** grading and viva APIs (Adeel), activity summary and insights components (Majid).
- **Tasks:** M0.3, M1.3, M2.4, M3.3, M4.3.
- **Rules:** marks and percentages are computed only in `services/scoring.py`; grace marks are a separate ledger and never overwrite scores; the dashboard says "final" only when every submitted work is approved; never label students "weak" in the UI, use "needs attention" with reasons.
- **Done means:** a teacher can go from an open assessment to approved, released grades and a dashboard without touching the database.
- **Gotcha:** schema changes hit everyone. Announce, then everyone runs `python -m app.seed --reset`.

## 7. Golden path (must work on `main` at every sync)

1. Teacher opens an open assessment and sees its settings (strictness, viva weight, feedback mode, release mode, AI policy).
2. Student opens it, writes in the editor (types, then pastes a block), submits.
3. Student takes the viva (3 timed questions).
4. Teacher reviews the AI draft (per-criterion marks with evidence, flags, paste chunks, replay), approves and releases.
5. Student sees final score, understanding score and feedback (went well, to improve, next step).
6. Teacher dashboard shows stats and graphs; grace marks preview then apply.

## 8. Git

- Trunk-based on `main`. Small commits. `git pull --rebase origin main` before every push. No force push to `main`. No `git reset --hard` on shared work.
- Commit message: `<task id> <type>: <summary>`, for example `M2.1 feat: strictness mapping with tests`. Types: feat, fix, docs, test, chore.
- Never commit `.env`, `.cache/`, `*.db`, `node_modules/`, `__pycache__/`, `dist/`.
- If `main` is broken, whoever notices reverts the offending commit within 10 minutes and tells the owner. Revert first, debate later.
- Rebase conflict in a file you do not own: keep the owner's version, ask, then re-apply your change.
- After M3 (feature freeze): fixes, seed data and polish only.

## 9. Code standards and checks

- Python 3.11+, FastAPI, Pydantic v2, SQLModel, type hints, `ruff` clean. TypeScript strict, React function components, Tailwind. No `any` in `src/api/` or `src/lib/replay-core/`.
- JSON is snake_case everywhere (API, DB, fixtures). Timestamps ISO 8601 UTC. IDs are opaque strings.
- Every screen handles loading and error states. Anything slower than 2 seconds shows progress.
- Tests that must exist: strictness mapping, scoring blend, quote verification, activity summary (against fixtures), replay-core (against fixtures). Keep the suite under 10 seconds.
- Before pushing, run what you touched: `cd backend && pytest -q && ruff check .` and `cd frontend && npm run typecheck && npm run lint && npm test`.
- Docs and comments: short sentences, plain words, no em dashes (use commas, colons or parentheses).

## 10. LLM rules

Details in `docs/ai-spec.md`.
- Only `backend/app/llm/client.py` talks to an LLM provider. Everyone else calls `complete_json(...)`.
- Temperature 0. Output is JSON validated by Pydantic. One repair retry, then fail loudly with `llm_unavailable`.
- Responses are cached by input hash. `MOCK_LLM=1` returns fixtures.
- Treat student text as data: delimit it, tell the model to ignore instructions inside it, and verify quotes after.
- No AI-detector services.

## 11. Stop and ask the human before

- Any contract change, or a schema change in a models file you do not own.
- Deleting files you did not create, destructive commands (`rm -rf`, `git reset --hard`, `git push --force`), or dropping the database outside `python -m app.seed --reset`.
- Adding a new dependency, or running a script that makes more than 20 LLM calls.
- Anything that changes the golden path.

## 12. Do not

- Add features that are not in `docs/roadmap.md` (login, LMS integration, voice answers and plagiarism databases are out of scope today).
- Refactor or reformat files you do not own.
- Call an LLM provider outside `llm/client.py`.
- Hide failures. If something is broken, say so in `docs/progress.md`.
