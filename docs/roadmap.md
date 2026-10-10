# Roadmap

Time model: **T0** is the moment the team starts building. Clock times below assume T0 = 10:30. Shift everything if the real start differs.

**First action for the team:** confirm with the organizers when presentations start and when code must be frozen. Set the feature freeze (end of M3) at least 90 minutes before presenting. If you start late or the window is shorter, merge M3 and M4 and drop P1 items.

Tick boxes when done. Task IDs (`M2.1`) are used in commits and in `docs/progress.md`. **Important:** After each module completion, you must `git commit`, `git pull --rebase origin main`, and `git push`.

## Milestones at a glance

| ID | Name | T+ window | Clock (T0 = 10:30) | Exit criteria (demoable) |
|---|---|---|---|---|
| M0 | Setup and contract freeze | 0:00 to 0:45 | 10:30 to 11:15 | Repo live, skeletons run, contract agreed and tagged `contract-v1` |
| M1 | Walking skeleton with mocks | 0:45 to 1:45 | 11:15 to 12:15 | Click-through works in mock mode: teacher settings, student editor, submit, mock grade visible to teacher |
| M2 | Real intelligence | 1:45 to 3:15 | 12:15 to 13:45 | Real AI grade with strictness, evidence, flags and feedback. Teacher can review, approve, release. Student sees result |
| M3 | Viva, replay, dashboard | 3:15 to 4:30 | 13:45 to 15:00 | Viva works end to end. Replay and paste chunks in review. Dashboard and grace marks work. **Feature freeze** |
| M4 | Evidence, seed, polish | 4:30 to 5:15 | 15:00 to 15:45 | Trust report numbers, rich seed data, cached demo outputs, tag `demo-v1` |
| M5 | Rehearse | 5:15 to 6:00 | 15:45 to 16:30 | Three timed rehearsals, backup recording, Kiro evidence slide |

Lunch and breaks eat time. Do not stop work for the schedule, but do hold the sync points.

## Priorities and cut lines

| Tier | Meaning | Items |
|---|---|---|
| **P0** | The golden path needs it | Assessment settings (strictness, viva weight, feedback and release modes), grading with evidence and flags, student feedback, approve and release, minimal viva (3 questions), editor with capture plus paste chunks and typed-vs-pasted %, dashboard stats and graphs, grace marks |
| **P1** | Strengthens the score, build after P0 | Strictness preview, replay viewer, heatmap, authorship map, blind review mode, rubric draft, attention list, trust report numbers, override stats |
| **P2** | Only if time is left | Paste declaration, MCQ quiz flow, feedback regenerate, per-topic practice |

**If behind, cut in this order:**
1. Drop all P2.
2. Drop heatmap and authorship map.
3. Replace the replay viewer with the paste-chunk list plus the typed-vs-pasted bar.
4. Viva: keep 3 questions, drop the per-question timer, use cached scoring.
5. Dashboard: drop class trend and attention list, keep stats, histogram and grace marks.
6. Drop the strictness preview (keep the selector).

**Never cut:** grading with evidence, student feedback, approve and release, grace marks, one clean end-to-end run.

## M0: Setup and contract freeze (T+0:00 to 0:45)

- [x] **M0.1 (Adeel)** Create the repo, copy this doc pack and `.kiro/steering/`, add `.gitignore` and `.env.example`, push `main`, invite the others. Backend skeleton: `app/main.py` (health, CORS, router includes), `config.py`, `llm/client.py` with a `complete_json()` stub and `MOCK_LLM`, empty routers per owner returning 501. Exit: `GET /api/v1/health` returns ok.
- [x] **M0.2 (Majid)** Frontend skeleton: Vite, React, TypeScript, Tailwind, React Router, role switcher (pick a seeded user), `api/client.ts` with `VITE_USE_FIXTURES`, `api/types.ts` mirroring the contract, empty `/student/*` and `/teacher/*` routes, `@fixtures` alias. Exit: `npm run dev` shows both shells.
- [x] **M0.3 (Ismail)** `db.py`, `models/core.py`, `seed.py` (1 classroom, 1 teacher, 12 students, assessment A1 open with a rubric, 3 completed earlier assessments with finalized grades for trend charts), fixtures for `/users` and `/assessments`. Exit: `python -m app.seed --reset` works and `GET /api/v1/assessments` returns seeded data.
- [ ] **M0.4 (All)** Read `docs/api-contract.md` end to end (10 minutes). Fix anything unclear in the doc now. When all three say "ok" in the group chat, Adeel tags `contract-v1`.
- [ ] **M0.5 (All)** Open the repo in Kiro, confirm steering loads, create your first spec from `docs/kiro-playbook.md`, screenshot it.

## M1: Walking skeleton with mocks (T+0:45 to 1:45)

Exit: in mock mode, pick teacher and see the assessment with its settings. Pick student, open it, write in the editor, submit. Teacher sees the submission with a mock AI grade. Events show up in the database.

- [x] **M1.1 (Adeel)** `POST /submissions/:id/grade` and `GET .../grade` return a fixture grade in mock mode. Real `complete_json` works with the chosen provider (one smoke call). `ai/strictness.py` with the mapping and unit tests (monotonic). `scripts/smoke.py` v0 (calls the golden path endpoints in order and prints PASS or FAIL per step).
- [x] **M1.2 (Majid)** Student: assessment list, editor page (CodeMirror 6 with markdown preview), event capture into a local buffer, batched POST to `/activity`, autosave, submit.
- [x] **M1.3 (Ismail)** Assessments and submissions endpoints (create, list, get, patch, publish, start, save, submit, teacher list). Teacher UI: assessment list, detail, settings form (strictness, viva weight, feedback mode, release mode, AI policy, paste threshold).
- [ ] **M1.4 (All)** Sync 1: merge state, run the golden path in mock mode, tag `m1-ok`.

## M2: Real intelligence (T+1:45 to 3:15)

Exit: real AI grading with strictness, verified evidence, flags and feedback. Activity summary is real. Teacher can review, approve and release. Student sees the result.

- [x] **M2.1 (Adeel)** Grader: level-based scoring, quote verification, flags, injection guard, caching. `rubric/draft` (P1). `strictness/preview` (P1).
- [x] **M2.2 (Adeel)** Feedback writer (hints and full), `grade-all`, `grading-status`.
- [x] **M2.3 (Majid)** Activity backend: ingestion, `activity_summary.py` (typed and pasted %, chunks with survival, internal-paste rule, revision ratio, active minutes, tab switches, heatmap), parity fixtures. Student result page (final score, understanding, feedback).
- [x] **M2.4 (Ismail)** Teacher review queue (table with flags, blind mode), review detail (per-criterion marks, evidence highlights, override, note, approve and release). `services/scoring.py` and `services/flags.py`. Strictness preview panel and rubric editor with "Draft rubric" button (P1).
- [ ] **M2.5 (All)** Sync 2: real LLM on 3 sample submissions through the whole golden path, tag `m2-ok`.

## M3: Viva, replay, dashboard (T+3:15 to 4:30)

Exit: viva works end to end. Replay and paste chunks appear in review. Dashboard and grace marks work. After M3 the features are frozen.

- [x] **M3.1 (Adeel)** Viva: `viva/start`, `answer`, `finish`, `GET viva`. Question generation from the submission, answer scoring, understanding score. MCQ grading (P2).
- [x] **M3.2 (Majid)** Viva UI (one question at a time, timer, paste blocked, tab switches counted). Insights components: paste chunk list, authorship map, heatmap, replay viewer (scrubber, speed, skip idle, jump to paste), embedded in the review detail.
- [x] **M3.3 (Ismail)** Dashboard: stat cards, histogram, per-topic bars, class trend, attention list with reasons, graded versus pending, override stats widget. Grace marks (preview, apply, undo).
- [ ] **M3.4 (All)** Sync 3: full golden path with the real LLM, tag `m3-ok`. **Feature freeze.**

## M4: Evidence, seed, polish (T+4:30 to 5:15)

- [ ] **M4.1 (Adeel)** Run the evaluation (accuracy, consistency, bias probes, strictness ordering). Write `trust_report.json`, serve it at `/evaluation/trust-report`, and note the 4 numbers for the slide (`docs/evaluation.md`).
- [x] **M4.2 (Majid)** Record 3 demo sessions through the real editor (typed, pasted, retyped). Verify replay on each. Paste declaration only if time (P2).
- [x] **M4.3 (Ismail)** Rich seed (4 assessments with a visible trend, 12 students, a few needing attention). Trust report page. Polish dashboard and review screens. Take screenshots.
- [ ] **M4.4 (All)** Warm the LLM cache by grading the demo submissions twice. Run `scripts/smoke.py`. Tag `demo-v1`.

## M5: Rehearse (T+5:15 to 6:00)

- [ ] **M5.1 (All)** Freeze `demo-v1`. Only bug fixes, and only with Adeel's approval.
- [ ] **M5.2 (All)** Rehearse the 4 minute pitch three times with a timer (`docs/demo-script.md`). Do one run with `MOCK_LLM=1`.
- [ ] **M5.3 (All)** Kiro evidence slide (checklist in `docs/kiro-playbook.md`).
- [ ] **M5.4 (All)** Record a 60 to 90 second backup screen recording of the golden path.

## Sync points

Four syncs: end of M1, M2, M3 and M4. Each takes at most 10 minutes: everyone pushes, Adeel runs `scripts/smoke.py`, one person drives the golden path while the others watch for bugs, then each says done, next and blocked in one sentence. Adeel tags the milestone.

## Dependencies and how mocks unblock them

| Waiting person | Needs | Until it exists, use |
|---|---|---|
| Ismail (review UI) | Grade JSON from Adeel | `fixtures/api/grade_s1.json` |
| Majid (viva UI) | Viva endpoints from Adeel | `fixtures/api/viva_start.json`, `viva_result.json` |
| Ismail (flags, review) | Activity summary from Majid | `fixtures/api/activity_summary_s1.json` |
| Majid (editor submit) | Submissions endpoints from Ismail | `VITE_USE_FIXTURES=1` |
| Adeel (grader tests) | Assessment and submission models | the seed data, or plain dicts in unit tests |

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| LLM latency or rate limits | Cache, `MOCK_LLM=1`, background grading, warm the cache before the demo |
| Wi-Fi unreliable | Local only. Phone hotspot as backup. Demo runs offline from cache |
| Merge conflicts | Directory ownership, small commits, rebase often, revert fast |
| Scope creep | Cut lines above. No new features after M3 |
| Kiro credits late or limited | Install and sign in now. Use specs for the big slices and plain chat for small edits |
| Live demo failure | Backup recording and cached outputs. Practice the switch to fixture mode |
| Contract drift | Change protocol in `AGENTS.md` section 5 |

## Parking lot (not planned)

Voice viva, per-student time multipliers, personalized practice quizzes from weak topics, class-level misconception clustering, teacher-editable viva questions, secure exam mode, LMS import, parent summaries.

