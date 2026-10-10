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
| Adeel | M0.1 | not started | repo and backend skeleton | none |
| Majid | M1.2 | frontend mock flow verified, real integration pending | activity backend and parity fixtures (M2.3) | submission endpoints pending |
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

