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
| Majid | M1.2 | waiting for human start, local setup ready | student editor, capture, submit on human call | seed and API fixtures missing |
| Ismail | M0.3 | not started | db, seed, fixtures | none |

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

No entries yet.

### Archive (Adeel)

None yet.

## Log: Majid (newest first)

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

No entries yet.

### Archive (Ismail)

None yet.
