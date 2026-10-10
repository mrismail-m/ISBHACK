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
| Adeel | M4.1 partial | full eval run and report | approval for about 145 LLM calls, human raters, contract OK | human ratings missing |
| Majid | M2.3/M3.2 done | live API browser flow verified with mock AI | team real-AI golden path | timed recording deferred by user |
| Ismail | M4.3 done | wait for demo run | help with rehearsals | none |

## Integration status (golden path)

Updated at syncs; Majid corrected stale rows with user authorization. Mock AI through live APIs is distinguished from real-provider verification.

| Step | Mock mode | Real mode | Notes |
|---|---|---|---|
| 1. Teacher sees assessment settings | mock ok (API) | UI run pending | Settings implemented; full real-AI demo not signed off. |
| 2. Student writes (type and paste) and submits | mock ok (live API + UI) | full run pending | Actual capture, storage and replay verified; grading used mock AI. |
| 3. Student takes the viva | mock ok (live API + UI) | API checks reported by Adeel | Three answers completed in browser; real-provider viva reported in Adeel's log. |
| 4. Teacher reviews AI draft, flags, replay, approves and releases | mock ok (live API + UI) | full run pending | Paste highlight, replay and release verified with mock AI. |
| 5. Student sees result and feedback | mock ok (live API + UI) | full run pending | Browser release returned 13.8/20 and 69%; no full real-AI browser sign-off. |
| 6. Dashboard stats and graphs, grace marks | dashboard verified; grace UI pending | full run pending | Synthetic cohort populated, live and fixture dashboard checked. |


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

### 2026-10-10 15:10 | Adeel | M4.1 | partial
- Did: eval harness built and tested: `python -m eval.run_eval` (`--quick`, `--all`, section flags), pure Python MAE/QWK (matches sklearn), 6 bias probes, consistency, strictness ordering, editor signals from Majid's demo sessions, `GET /evaluation/trust-report` (404 until a report exists). Dataset: 15 answers (`fixtures/eval/answers_a1.json`) plus author-intended levels. Pilot with 15 real calls: AI vs author levels MAE 1.53 marks, QWK 0.87, AI about +0.9 marks more generous on average (c1 most). Strictness ordering passed, 0 violations.
- Files: `backend/eval/*`, `backend/app/routers/evaluation.py`, `backend/app/schemas/grading.py` (TrustReport), `backend/app/llm/client.py` (request counter, role `eval_polish`), `fixtures/eval/*`, `fixtures/api/llm/eval_polish.json`, `backend/tests/{test_eval,test_health}.py`, `docs/evaluation.md`
- Contract: PROPOSED, not applied: in `TrustReport`, `accuracy.*_mae/_qwk` become nullable (null = human ratings pending) and new optional fields are added (`accuracy.author_labels`, `consistency.n_answers/identical_level_pct`, extra probe fields, `strictness_ordering.n/mean_spread_marks`). `api-contract.md`, `types.ts` and the fixture are untouched until Adeel approves.
- Decisions: no human scores are invented. Human numbers show "pending" until two raters fill `fixtures/eval/human_scores_a1.template.csv`. Removed scikit-learn from `requirements-eval.txt` (not needed). Replaced the 501 test in `test_health.py` (the trust report was the last stub).
- Next: Adeel approves the full run (about 145 LLM calls) and the contract proposal; two teammates rate the 15 answers blind; then run `--all --yes`, commit the report, tick M4.1.
- Needs from others: Majid and Ismail (or any two people): blind-rate 15 answers x 4 criteria each (about 15 minutes) using the template. Ismail: trust report page (T09) can read the new optional fields once the contract is approved.

### 2026-10-10 14:50 | Adeel | M1.1 follow-up | done
- Did: LLM key pool with rotation and fallback (3 Groq keys, then 3 Gemini keys). Round-robin per call, cooldown on 429/5xx/timeout/bad key, then next provider. Keys live only in git-ignored `backend/.env`. Grade `model_id` now records the model that answered. Verified live: grade, feedback, rubric draft, viva start/answer/finish, and forced fallback (bad Groq keys went to Gemini).
- Fixed: `feedback.md` and `rubric.md` had no `---USER---` section, so the model got an empty user message. Feedback lists are trimmed to 3 (models returned 4). Added `rubric_draft.json` mock fixture and prompt render tests.
- Files: `backend/app/llm/client.py`, `config.py`, `ai/{feedback,rubric,grader}.py`, `ai/prompts/{feedback,rubric}.md`, `tests/{test_llm_client,test_prompts,conftest}.py`, `.env.example`, `docs/ai-spec.md`
- Contract: none. New optional env: `LLM_ORDER`, `LLM_GROQ_KEYS`, `LLM_GROQ_MODEL`, `LLM_GEMINI_KEYS`, `LLM_GEMINI_MODEL` (see `.env.example`). Models: `openai/gpt-oss-120b` (Groq; llama-3.3 is gone) and `gemini-3.5-flash` (2.5-flash is closed to new users).
- Finding: with real Groq the sample essay got 20/20 (all level 4, no minor errors). The mock fixture says 15.5. Grader looks generous. M4.1 accuracy run should check this; may need a stricter prompt or `reasoning_effort` medium.
- Next: M4.1 trust report on real data; tune the grader if the accuracy run shows inflation.
- Needs from others: everyone: `backend/.env` is local. Ask Adeel for the keys, do not paste them in chat or commits. Tests ignore `.env` keys on purpose.

### 2026-10-10 14:20 | Adeel | M3.1 | done
- Did: viva `start`, `answer`, `finish`, `GET viva`. Examiner writes questions; every `anchor_quote` is verified in the submission and failed ones are asked for again once. Scorer gets only question, the student's text excerpt and the answer. Understanding is the mean of 0, 0.5, 1 scores, computed in code.
- Files: `backend/app/ai/{viva.py,viva_service.py,prompts/examiner.md,prompts/scorer.md}`, `backend/app/routers/viva.py`, `backend/app/schemas/viva.py`, `backend/tests/test_viva.py`, `fixtures/api/{viva_start,viva_result,viva_detail_s1}.json`, `fixtures/api/llm/viva_*.json`
- Contract: none. `VivaDetail.understanding` is null and `status` is `in_progress` until finish (contract only showed `done`). `VivaDetail.score` is null until scored.
- Decisions: missing, empty or timed-out answers score 0 without an LLM call (timed out = `time_taken_s` over the limit plus 5 s grace). `GET viva` needs `X-User-Id` of a teacher (403 otherwise). Start is a resume if called twice, 409 after finish. In mock mode anchors are not verified (canned questions).
- Checks: 72 tests pass (1 failing test is Majid's `test_activity`, naive datetimes with sqlmodel 0.0.48 locally). Live smoke in mock mode: steps 0 to 3 and 4a, 4b pass; approve, result, stats are 501 (Ismail). MCQ grading (P2) not built. No real LLM call made yet.
- Next: wait for Ismail's M2.4 and M3.3, then run the full golden path; M4.1 trust report.
- Needs from others: Ismail: read `viva_sessions.understanding` (null until done) for the blend; call `grade_submission_by_id` from submit.

### 2026-10-10 14:00 | Adeel | M2.2 | done
- Did: Implemented LLM feedback writer (`generate_feedback`), verified its quotes, stripped explanations in hints mode. Implemented `grade-all`, `grading-status`, `feedback/regenerate` endpoints. Added `feedback.json` mock fixture.
- Files: `backend/app/ai/feedback.py`, `backend/app/ai/prompts/feedback.md`, `backend/app/ai/pipeline.py`, `backend/app/routers/grading.py`, `fixtures/api/llm/feedback.json`
- Contract: none
- Decisions: `grade-all` grades synchronously (no queue needed for demo scale). `grading-status` counts `ai_draft` and `approved` rows as graded.
- Next: M3.1 (viva: question generator, answer scorer, viva router).
- Needs from others: none

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

### 2026-10-10 | Majid | M4.2 demo roster and cleanup | done
- Did: Added fixed-credential demo login, 50 names/registrations, 150 synthetic writing sessions and offline fixtures. Dashboard selects students for heatmaps, paste evidence, authorship and replay.
- Files: `features/student/DemoLogin.tsx`, routes, teacher dashboard, client/demo store, `backend/app/demo_{seed,fixtures}.py`, analytics service/tests, `fixtures/demo/`, user/assessment fixtures.
- Contract: none. Registration numbers remain in a separate roster; existing user IDs and API schemas stay stable. Supplied marks were not imported.
- Decisions: User authorized dummy auth/data and shared cleanup. Removed unused concurrent package additions after backing them up in ignored cache; restored locked dependencies with npm ci. Existing DB work preserved.
- Checks: Seed reruns without duplicates; generated grades validate and all sessions replay exactly. Live and fixture browser login/dashboard verified, including invalid-password rejection. 104 backend tests, 20 frontend tests, lint/typecheck/build pass. Browser capture exported as an 83-second silent walkthrough.
- Next: Real-AI evaluation and full team golden path; shared status now distinguishes verified mock UI from reported real API checks.
- Needs from others: Adeel evaluation; grace UI sign-off. Ten-minute recording remains deferred by user.


### 2026-10-10 | Majid | M2.3/M3.2 | done
- Did: Verified editor, viva, review, replay, approval and released result through live APIs with mock AI. Captured 805 characters and 247 events; replay matched exactly, paste survival was 100%.
- Files: `fixtures/activity/integration_session.json`, replay parity test, submissions router/integration tests, teacher queue/dashboard, narrow Python lint corrections, roadmap.
- Contract: none. Queue now displays server-computed blended percentage; submission grading reads GRADE_ON_SUBMIT from configured settings.
- Decisions: User deferred ten-minute recording and assigned this chat ownership of Majid. Other session package edits are preserved separately. Credentials saved only in ignored backend/.env; real Groq connectivity succeeded.
- Checks: 102 backend tests and Ruff pass; 20 frontend tests, typecheck, lint and build pass. CodeMirror bundle warning remains. Released browser result: 13.8/20, 69%, understanding 50%.
- Next: Team real-provider golden path and evaluation. Reviewed new M4.3 pull, corrected seed lint and labeled sample trust-report fallback; browser integration used mock AI.
- Needs from others: Adeel owns real-AI evaluation. Timed recording is deferred, not verified.


### 2026-10-10 14:26 | Majid | M3.2 | partial
- Did: Lazy-loaded student, viva, result and teacher routes plus CodeMirror with visible loading states. Main bundle reduced from about 922 KB to 273 KB; editor is separate, about 502 KB, so one warning remains.
- Files: `frontend/src/routes.tsx`, `frontend/src/features/student/StudentApp.tsx`; narrow fixes in `frontend/src/features/teacher/TeacherReviewDetail.tsx`.
- Contract: none. User authorized teammate fixes.
- Decisions: Review now shows failed loads and a retry instead of an endless spinner, cancels stale updates and resets on submission change; approval controls disable during saving and show backend errors.
- Checks: Frontend 19 tests, typecheck, lint and build pass. Timed writing verification is running on isolated localhost ports 5175/8001 to preserve the user's active app session.
- Next: Finish the 10-minute editor session, verify viva and review/release in browser, then tick remaining Majid integration boxes.
- Needs from others: none for this path; real-model checks still require Adeel's provider setup.


### 2026-10-10 14:22 | Majid | M2.3/M3.2 | partial
- Did: Corrected seeded-role access on submission reads/writes, class queue, approval/results and viva POSTs; viva teacher reads are classroom-scoped. Starting work now requires a student in an open assessment's classroom.
- Files: `backend/app/routers/{submissions,viva}.py`, `backend/tests/{test_student_integration,test_viva,test_grading_api}.py`.
- Contract: none. Uses existing X-User-Id demo scheme and activity access helper, not production authentication.
- Decisions: User authorized teammate corrections. Tests provide seeded roles; wrong students, unknown users and other-class teachers cannot mutate or read another submission. Students cannot approve or list class work.
- Checks: Backend suite and ruff verified before push.
- Next: Browser integration and 10-minute editor recording.
- Needs from others: none for Majid integration; broader grading/assessment role review remains with owners.


### 2026-10-10 14:14 | Majid | M2.3/M3.2 | partial
- Did: Pulled and reviewed M2.1, M2.2, M2.4 and M3.1. Viva/result endpoints and review embedding now exist. Added integration checks through grade, viva, approval and released student result.
- Files: `backend/tests/test_student_integration.py`, narrow corrections in `backend/app/routers/submissions.py` and `frontend/src/features/teacher/TeacherReviewDetail.tsx`.
- Contract: none. Corrected invalid override acceptance: reject unknown/duplicate criteria and nonnumeric, negative or excessive marks; UI maximum uses the rubric criterion limit.
- Decisions: User authorized corrections to teammate mistakes. New tests verify rejection leaves results unreleased and understanding blends into the released result.
- Checks: Backend 78 tests and ruff pass; frontend 19 tests, typecheck and lint pass. No real LLM call. Browser integration and 10-minute recording are not yet verified.
- Next: Verify viva, teacher replay and released result in browser. Review remaining missing seeded-role checks on submission mutations, approval and viva POSTs before treating access restrictions as verified.
- Needs from others: None for Majid API integration now. Adeel still needs a real provider key for real-model evaluation; Ismail dashboard/grace remain in progress.


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

### 2026-10-10 14:35 | Ismail | M4.3 | done
- Did: Created `TrustReportPage.tsx` using `fallbackReport` for now until M4.1 is completed. Updated `backend/app/seed.py` to generate rich historical data across past assignments for 12 students to show a visible class trend, with specific falling patterns for attention-needing students. Polished up the teacher app routing.
- Files: `backend/app/seed.py`, `frontend/src/features/teacher/TrustReportPage.tsx`, `fixtures/api/trust_report.json`, `frontend/src/features/teacher/TeacherApp.tsx`
- Contract: none
- Decisions: Wrote mock fallback for Trust Report directly in the frontend since the backend is still 501.
- Next: Help with demo recording and wait for team
- Needs from others: Adeel to complete M4.1 (Trust Report JSON real).

### 2026-10-10 14:26 | Ismail | M3.3 | done
- Did: Implemented `AssessmentStats`, `OverrideStats`, `ClassPerformance`, `AttentionStudent`, and Grace Marks schemas and services. Built `TeacherDashboard.tsx` with Classroom and Assessment dashboards. Integrated into `TeacherApp.tsx`.
- Files: `backend/app/schemas/analytics.py`, `backend/app/services/analytics.py`, `backend/app/services/grace.py`, `backend/app/routers/analytics.py`, `frontend/src/features/teacher/TeacherDashboard.tsx`, `frontend/src/features/teacher/TeacherApp.tsx`
- Contract: none
- Decisions: Grace marks are appended to a ledger and `undo` marks them as undone. All `analytics` routes now successfully return data instead of 501.
- Next: M4.3 (Polish)
- Needs from others: none

### 2026-10-10 14:15 | Ismail | M2.4 | done
- Did: Implemented teacher review queue with flags and blind mode. Built review detail page with criteria overrides, overall notes, and activity insights integration. Added `services/scoring.py` and `services/flags.py`. Implemented strictness preview and rubric drafter in settings. Updated submission endpoints to calculate blended scores.
- Files: `backend/app/routers/submissions.py`, `backend/app/services/scoring.py`, `backend/app/services/flags.py`, `backend/app/schemas/core.py`, `frontend/src/features/teacher/TeacherApp.tsx`, `frontend/src/features/teacher/TeacherReviewDetail.tsx`
- Contract: none
- Decisions: Re-wrote submissions router to seamlessly use `load_activity` and `summarize_activity` to provide derived flags in `list_submissions`.
- Next: M3.3 (Dashboard, stat cards, grace marks)
- Needs from others: Adeel M3.1 for completed viva API (currently waiting).

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








