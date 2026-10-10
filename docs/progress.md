# Progress

This file is the shared memory for all three agents. It exists so a new agent session can recover context in under a minute. Humans read it too.

## How to use it

- **Read first:** "Current snapshot", "Integration status", and the last 5 entries of your member's log. Do not read the whole file.
- **Write last:** at the end of every session (or before a long pause), add one entry to **your own** log, newest first, and update your row in "Current snapshot".
- **Own section only.** Never edit another member's log or snapshot row. "Contract changes" and "Decisions" are append-only for everyone.
- **Facts, not stories.** Say what changed, where, what is next, and what you need. No code dumps. Link to file paths.
- **Keep entries to 8 lines or fewer.** If you need more, put the detail in a doc and link it.
- **Compaction:** when your log has more than 12 entries, replace the oldest 8 with a 3 line summary under "Archive" for your member.
- **Merge conflicts:** keep both sides. Sections are separate so conflicts should be rare.

## Entry template

Copy this, fill it in, and paste it at the top of your own log.

```
### YYYY-MM-DD HH:MM | <member> | <task id> | <done | partial | blocked>
- Did: <1 to 3 short bullets: what changed>
- Files: <paths touched, grouped>
- Contract: <none | CHANGED: what and where>
- Decisions: <none | short>
- Next: <the very next action>
- Needs from others: <none | who and what>
```

## Current snapshot

Update only your own row.

| Member | Current task | Status | Next | Blockers |
|---|---|---|---|---|
| Adeel | M2.1 done | M2.2 next | grader retries, rubric draft, strictness preview | M2.2 | no LLM key configured yet |
| Majid | M4.2 done | independent implementation and demo recordings ready | integrate when owners publish dependencies | live viva, released results and teacher review embedding |
| Ismail | M2.4 | not started | teacher review queue | M2.1, M2.2, M2.3 |

## Integration status (golden path)

Updated by Adeel at each sync. Values: `not started`, `mock ok`, `real ok`, `broken (note)`.

| Step | Mock mode | Real mode | Notes |
|---|---|---|---|
| 1. Teacher sees assessment settings | not started | not started | |
| 2. Student writes (type and paste) and submits | not started | not started | |
| 3. Student takes the viva | not started | not started | |
| 4. Teacher reviews AI draft, flags, replay, approves and releases | not started | not started | |
| 5. Student sees result and feedback | not started | not started | |
| 6. Dashboard stats and graphs, grace marks | not started | not started | |

## Contract changes (append only, newest first)

No changes yet. Contract v1 is drafted in `docs/api-contract.md` and becomes frozen when `contract-v1` is tagged.

Format: `YYYY-MM-DD HH:MM | <member> | CONTRACT CHANGE | <what changed, which files> | <who must adapt>`

## Decisions (append only, newest first)

No new decisions yet. Standing decisions are in `docs/architecture.md` section 12.

Format: `YYYY-MM-DD HH:MM | <member> | <decision> | <why>`

## Needs from others (open requests)

None yet. Add a line here when you need a change in a file you do not own, and strike it through when done.

Format: `<from> to <owner>: <what> (task id)`

## Log: Adeel (newest first)

### 2026-10-10 13:51 | Adeel | M2.1 | done
- Did: Added quote repair retry to grader. Implemented `/rubric/draft` and `/strictness/preview` reusing `run_grader` and `apply_marks`. 
- Files: `backend/app/ai/grader.py`, `backend/app/routers/grading.py`, `backend/app/ai/rubric.py`, `backend/app/ai/prompts/rubric.md`
- Contract: none
- Decisions: Quotes repair retry handled in `run_grader` via a double `complete_json` pass; fallback to original if retry fails.
- Next: M2.2 (Feedback writer, `grade-all`, `grading-status`).
- Needs from others: none

### 2026-10-10 | Adeel | M1.1 | done
- Did: `complete_json` real provider path (openai, anthropic, openai_compatible; repair retry, 1 retry on timeout/429/5xx, cache). `ai/strictness.py` plus grader core (quote verification with UTF-16 offsets, flags, marks in code). `POST/GET /submissions/:id/grade` work in mock mode. `scripts/smoke.py` v0 covers the golden path.
- Files: `backend/app/{llm/client.py,ai/*,routers/grading.py,models/grading.py,schemas/grading.py,main.py,config.py}`, `backend/tests/*`, `fixtures/api/grade_s1.json`, `fixtures/api/llm/grader*.json`, `scripts/smoke.py`, `.env.example`
- Contract: none (added optional env `LLM_BASE_URL`, see `.env.example`)
- Decisions: `grades` and `viva_sessions` tables are created at app startup in `main.py`, so no reseed is needed for them.
- Checks: 43 tests pass, ruff clean on Adeel paths. Live smoke in mock mode: steps 0, 1, 2, 4 pass; viva, approve, result, stats fail with 501 (not built yet). No real LLM call made (no key configured).
- Next: M2.1 (retry on bad quotes, rubric draft, strictness preview), then M2.2.
- Needs from others: Ismail: call `app.ai.pipeline.grade_submission_by_id(session, id)` from `submit` when `GRADE_ON_SUBMIT=1`, and import `app.models.grading` in `models/__init__.py` or `seed.py`. Everyone: ruff fails on `seed.py`, `models/core.py`, `schemas/core.py`, `dump_fixtures.py` (not Adeel files).

### 2026-10-10 | Adeel | DESIGN | done
- Did: wrote `docs/design.md` (visual and interaction spec, tokens, screens, components, anti-slop rules, steering block). Proposed only; needs Adeel's answers to section 16 before anyone builds on it.
- Files: `docs/design.md`
- Contract: none
- Decisions: petrol accent, Newsreader plus Atkinson Hyperlegible (OFL), margin-note law (serif = people, sans = interface and AI), approve is never default or a shortcut
- Next: Adeel answers Q1 to Q7 (section 16); then tokens.css and `.kiro/steering/design.md` get created by the agreed owner
- Needs from others: Majid (restyle `routes.tsx` role bar, fix Tailwind 3 vs 4 setup, C1), Ismail (ui kit order, section 15)

### Archive (Adeel)

None yet.

## Log: Majid (newest first)

### 2026-10-10 13:51 | Majid | M4.2 | done
- Did: Recorded 3 real editor sessions (typed, pasted, retyped), persisted through local API and exported raw events plus server summaries. All reconstruct the exact saved 547-character answer. Typed/retyped have 0% paste; pasted has 100% with one surviving large chunk.
- Files: `fixtures/activity/demo_sessions.json`, `fixtures/api/activity_{events,summary}_s1.json`, backend activity tests, frontend replay tests; roadmap and this log.
- Contract: none. Comparison normalizes equivalent ISO timestamp precision before comparing summaries.
- Decisions: These are automated demo recordings, not the human pilot study. Retyping copied prose yields no paste signal, illustrating the signal's stated limit. No AI or grading claims made.
- Checks: Backend 54 tests and ruff pass; frontend 19 tests, typecheck, lint and build pass. Replay and summary agree on all 3 recordings and 7 independent fixtures. Large frontend bundle warning remains.
- Next: Wait for owner dependencies, then pull, read changed files and integrate live viva/results and review embedding. Full 10-minute round trip and team golden path remain unverified.
- Needs from others: Adeel viva endpoints; Ismail released result endpoint and teacher review detail embedding. Exports and fixtures are ready for both owners.


### 2026-10-10 13:47 | Majid | M3.2 | partial
- Did: One-question viva UI with persistent deadlines, timeout, blocked paste/drop, tab-switch counts and retry; fixture browser flow completed all 3 answers. Insights expose paste chunks, writing map, heatmap and replay with scrubber, speed, idle skipping and paste jumps.
- Files: `frontend/src/features/{student,insights}/`, `frontend/src/api/{student,activity}.ts`, `frontend/src/lib/replay-core/index.test.ts`, `frontend/src/routes.tsx`.
- Contract: none. Timeout sends an empty answer as specified. Blocked paste attempts do not claim pasted content was accepted; proposed design question remains unresolved.
- Decisions: Ismail can embed `ActivityInsights({submissionId})` or `InsightsView({activity,summary})` from `features/insights/ActivityInsights.tsx`. Keep current styling until proposed design is approved.
- Checks: Frontend 16 tests, typecheck, lint and build pass. Checkpoint seeking and idle/session boundaries covered. Build still warns about a large bundle.
- Next: Record typed, pasted and retyped sessions through the real editor and verify replay (M4.2).
- Needs from others: Adeel live viva (currently 501); Ismail released result API and teacher review detail embedding. M2.3/M3.2 remain unchecked until those integrations work.


### 2026-10-10 13:35 | Majid | M1.2 | done
- Did: Integrated latest Ismail endpoints and teacher routes. Real browser session typed, pasted, autosaved and submitted; teacher activity API returned all 146 characters, 54 events, 33.6% typed and 66.4% pasted with 100% paste survival.
- Files: `docs/roadmap.md`, `frontend/src/index.css`; narrow lint fixes in `backend/app/routers/{assessments,submissions}.py`, `backend/app/seed.py`, `backend/dump_fixtures.py`.
- Contract: none
- Decisions: User authorized teammate corrections. Replaced Tailwind 3 directives with Tailwind 4 import; extracted existing Depends defaults into singleton variables and formatted flagged Python files. No endpoint behavior changed.
- Checks: All backend tests and repo-wide ruff pass; frontend checks pass. Local DB seeded without deleting existing data. Real-mode frontend on port 5174; normal fixture frontend remains 5173.
- Next: M3.2 insights components and fixture-driven viva UI.
- Needs from others: Ismail result API; Adeel viva endpoints and approval of proposed design. Earlier missing submission endpoint request is resolved.

### 2026-10-10 13:31 | Majid | M2.3 | partial
- Did: Activity ingestion with authorization, duplicate retry and sequence validation; UTF-16 summary; pure replay core and 7 shared parity fixtures; released result and feedback UI.
- Files: `backend/app/{routers,models,schemas}/activity.py`, `backend/app/services/activity_summary.py`, `backend/tests/test_activity.py`, `fixtures/activity/cases.json`, `frontend/src/lib/replay-core/`, student result/API/routes.
- Contract: none. Shapes match v1. Paste declaration remains deferred P2.
- Decisions: User authorized teammate bug corrections. Added activity model import in `backend/app/seed.py` so seed/reset includes the new table; no other seed logic changed. Teacher consumers can call `load_activity(session, id)` then `summarize_activity(id, events, threshold)`.
- Checks: Backend 10 tests pass; owned Python files ruff clean. Frontend 12 tests, typecheck, lint and build pass. Both languages match expected shares exactly on all 7 fixtures.
- Next: M3.2 standalone insights and viva UI using fixture data, then integration once owners publish endpoints. Final M1.2/M2.3 checks wait for those endpoints.
- Needs from others: Ismail: live submission/result endpoints, UTC offsets on fixture timestamps, due_at in AssessmentCreate; Adeel: viva endpoints and approved design tokens. Seed currently lacks historical submission/grade rows promised by M0.3.

### 2026-10-10 13:22 | Majid | M1.2 | partial
- Did: Assessment list, CodeMirror markdown editor and preview, 3-second activity batching with persistent retries, autosave, reload recovery and submit lock. Browser mock flow verified.
- Files: `frontend/src/features/student/`, `frontend/src/api/{client,student,activity}.ts`, `frontend/src/routes.tsx`, package files; this log.
- Contract: none. User approved CodeMirror, react-markdown and Vitest dependencies plus package file updates.
- Decisions: Missing fixtures use a labelled browser-only demo store under student ownership. Real requests use X-User-Id; unload retains activity for retry because sendBeacon cannot set that header.
- Checks: Typecheck, frontend lint, 3 capture/upload tests and build pass. Browser verified typing, paste, preview, reload recovery and submit. Build warns about bundle size.
- Next: M2.3 activity persistence using Ismail's db, summary and shared parity fixtures. M1.2 stays unchecked until real events reach the database.
- Needs from others: Ismail: db/session helper, core models, assessment/submission endpoints and API fixtures. Existing teacher route remains a placeholder for Ismail integration.

### 2026-10-10 13:13 | Majid | M0.2 | done
- Did: Installed frontend lockfile dependencies and backend plus evaluation requirements in local `.venv`; created backend `.env` from example. Both servers respond locally.
- Files: `docs/progress.md`; local dependencies and backend `.env` are ignored.
- Contract: none
- Decisions: Development waits for the human's call. No feature code changed.
- Checks: Frontend build passes; lint has 2 existing warnings. Backend 2 tests pass; pip check passes; ruff has 2 existing E501 errors in Adeel files. Health smoke passes.
- Next: Human can run frontend `npm run dev` and backend `.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000` in their respective folders.
- Needs from others: Ismail's seed and API fixtures are absent; fixture client path needs fixing during M1.2.

### 2026-10-10 12:58 | Majid | M0.2 | done
- Did: Initialized Vite React TS app with Tailwind, React Router, role switcher and API types.
- Files: `frontend/`, `frontend/src/api/client.ts`, `frontend/src/api/types.ts`, `frontend/src/routes.tsx`
- Contract: none
- Decisions: none
- Next: M1.2 (Student editor and capture)
- Needs from others: none

### Archive (Majid)

None yet.

## Log: Ismail (newest first)

### 2026-10-10 13:24 | Ismail | M1.3 | done
- Did: Implemented Assessments and Submissions endpoints. Built Teacher UI with Assessment List, Detail, and Settings.
- Files: `backend/app/routers/assessments.py`, `backend/app/routers/submissions.py`, `backend/app/schemas/core.py`, `frontend/src/features/teacher/TeacherApp.tsx`, `frontend/src/routes.tsx`
- Contract: none
- Decisions: Deferred approve/result endpoints to not mock grading output based on human's call.
- Next: M2.4 (Teacher review queue)
- Needs from others: Adeel M2.1/M2.2, Majid M2.3 for the review UI.

### 2026-10-10 13:12 | Ismail | M0.3 | done
- Did: Implemented DB setup, core schemas, models, and seed script. Generated fixtures.
- Files: `backend/app/db.py`, `backend/app/models/core.py`, `backend/app/schemas/core.py`, `backend/app/seed.py`, `fixtures/api/users.json`, `fixtures/api/assessments.json`
- Contract: none
- Decisions: separated Pydantic schemas in schemas/core.py, dumped via python script to ensure contract parity.
- Next: M1.3 (Assessments and submissions endpoints, teacher UI)
- Needs from others: none

### Archive (Ismail)

None yet.





