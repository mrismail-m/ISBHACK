# Kiro playbook

"Meaningful use of Kiro" is worth 15 points, the same as Impact. The goal is real: Kiro should build most of the code, and we capture proof while we work. Use steering, specs, hooks and three parallel agents.

## 1. Setup (5 minutes, everyone)

1. Install Kiro from kiro.dev and sign in. The organizers will share how credits are activated today, so check the group.
2. Open the **repo root** as the workspace.
3. Confirm context is loaded. Ask Kiro: "Which steering files and AGENTS.md are you using?" You should see `AGENTS.md` plus `product.md`, `tech.md` and `structure.md`.
4. Create your first spec (section 3) and take a screenshot.

How context loads: Kiro picks up `AGENTS.md` from the workspace root automatically and always includes it. The three files in `.kiro/steering/` have `inclusion: always`. If someone uses a custom agent, steering is not included automatically: add `file://.kiro/steering/**/*.md` to that agent's resources.

## 2. How we work with Kiro

- One Kiro session per person. Each follows `AGENTS.md`.
- Start every session with the starter prompt in section 4.
- **Spec mode** for each big slice (section 3). Plain chat for small fixes.
- Read the generated requirements and design before running tasks. If they disagree with `docs/api-contract.md`, fix the spec. The contract wins.
- Reference docs by path, or with the file reference syntax `#[[file:docs/api-contract.md]]` inside specs and chat.
- Run tasks one at a time. Commit after each task with its ID (`AGENTS.md` section 8).
- `docs/progress.md` is the cross-session memory. Always update it.

## 3. Spec prompts (paste into Kiro spec mode)

Kiro writes `.kiro/specs/<name>/requirements.md`, `design.md` and `tasks.md`. Commit the spec folders.

| Member | Specs (in order) |
|---|---|
| Adeel | `ai-grading-core`, `viva-examiner` |
| Majid | `student-editor-capture`, `replay-and-insights`, `student-viva-and-result` |
| Ismail | `seed-data`, `assessment-setup-and-review`, `dashboard-and-grace-marks` |

### Adeel: ai-grading-core
```
Create a spec named ai-grading-core. Implement the AI grading core from #[[file:docs/ai-spec.md]] sections 2 to 5 and the endpoints rubric/draft, strictness/preview, grade, grade-all, grading-status and feedback/regenerate in #[[file:docs/api-contract.md]]. Requirements must cover: level-based scoring with the strictness table, verbatim evidence verification with UTF-16 offsets, the injection guard, grader flags and confidence rules, disk caching, MOCK_LLM mode, and unit tests for monotonic strictness and quote verification. Out of scope: viva, quizzes, frontend.
```

### Adeel: viva-examiner
```
Create a spec named viva-examiner. Implement viva question generation and answer scoring from #[[file:docs/ai-spec.md]] section 6 and the endpoints viva/start, viva/answer, viva/finish and GET viva in #[[file:docs/api-contract.md]]. Requirements: questions anchored to verified quotes, per-question time limits from the assessment, scores 0, 0.5 and 1, understanding as the mean, missing answers score 0, the scorer never receives timing or paste data, MOCK_LLM fixtures. Out of scope: UI.
```

### Majid: student-editor-capture
```
Create a spec named student-editor-capture. Build the student assessment list, a CodeMirror 6 markdown editor with preview, and the writing-process capture from #[[file:docs/architecture.md]] sections 7.1 to 7.3: userEvent mapping, event schema, batching every 3 seconds with sendBeacon on pagehide, a visible "what is recorded" banner, autosave and submit. Include the backend ingestion endpoint and activity_summary.py from section 7.4 with UTF-16 handling, plus the parity fixtures in fixtures/activity. Out of scope: replay UI, viva.
```

### Majid: replay-and-insights
```
Create a spec named replay-and-insights. Build lib/replay-core (applyEvent, docAt, authorshipAt, buildTimeline, heatmap) and the insights components (paste chunk list, authorship map, heatmap, replay viewer with scrubber, speed, idle skipping and jump to next paste) from #[[file:docs/architecture.md]] section 7.5. Requirements: typed and pasted percentages match activity_summary.py within 1 percentage point on every fixture, checkpoints every 200 events, vitest tests against fixtures/activity. Out of scope: backend.
```

### Majid: student-viva-and-result
```
Create a spec named student-viva-and-result. Build the student viva screen (one question at a time, per-question timer, paste blocked, tab switches counted and sent with each answer) and the result screen (final score, understanding, strengths, improvements, next step) against the viva and result endpoints in #[[file:docs/api-contract.md]]. It must work with VITE_USE_FIXTURES=1. Out of scope: backend.
```

### Ismail: seed-data
```
Create a spec named seed-data. Build db.py, models/core.py and seed.py with a --reset flag: 1 classroom, 1 teacher, 12 students, assessment A1 open with a 4 criterion rubric, and 3 completed earlier assessments with finalized grades so the dashboard shows a visible trend and a few students needing attention. Add matching fixtures in fixtures/api for /users and /assessments, following #[[file:docs/architecture.md]] section 4 and #[[file:docs/api-contract.md]].
```

### Ismail: assessment-setup-and-review
```
Create a spec named assessment-setup-and-review. Build the assessments and submissions endpoints from #[[file:docs/api-contract.md]], services/scoring.py and services/flags.py from #[[file:docs/architecture.md]] section 5, and the teacher UI: assessment settings (strictness, viva weight, feedback mode, release mode, AI policy, paste threshold), rubric editor with a Draft rubric button, strictness preview panel, review queue with blind mode, and review detail with per-criterion marks, evidence highlights, override, approve and release. Include tests for the score blend. Out of scope: dashboard.
```

### Ismail: dashboard-and-grace-marks
```
Create a spec named dashboard-and-grace-marks. Build the analytics endpoints (stats, performance, attention, override-stats, grace preview, apply and undo) following #[[file:docs/architecture.md]] section 5 and #[[file:docs/api-contract.md]], and the dashboard UI with Recharts: stat cards, histogram, per-topic bars, class trend, attention list with reasons, graded versus pending, override stats widget, and grace marks with preview and undo. Grace is a separate ledger capped at max marks. "final" only when every submitted work is approved.
```

The Trust report page (M4.3) is small: do it in plain chat.

## 4. Starter prompt for every agent session

Replace `<MEMBER>` with Adeel, Majid or Ismail.

```
You are the coding agent for <MEMBER> on the VivaGrade repo. Follow AGENTS.md exactly (session protocol, ownership map, golden rules). First run git pull --rebase origin main, then read docs/progress.md (Current snapshot, Integration status, and my last 5 entries) and the current milestone in docs/roadmap.md. Then tell me in 5 lines or fewer: task ID, files you will touch, what you will mock, first step. Print DONE or BLOCKED after every step. Stop and ask before anything listed in AGENTS.md section 11. At the end, write my progress.md entry and tick the roadmap boxes.
```

## 5. Hooks

Create these in the Kiro Agent Hooks panel (they are saved under `.kiro/hooks/`). Hooks fire on saves made inside Kiro's editor, so save from Kiro. Keep each one cheap and read-only.

| Hook | Trigger | What it does | Owner |
|---|---|---|---|
| Contract guard | Save of `docs/api-contract.md` or `backend/app/schemas/**` | Checks that schemas, `frontend/src/api/types.ts` and fixtures agree with the contract. Lists mismatches. Changes nothing | Adeel |
| Grading regression | Save in `backend/app/ai/prompts/**` or `backend/app/ai/strictness.py` | Runs the strictness tests and `eval.run_eval --quick`, then reports | Adeel |
| Replay parity | Save in `frontend/src/lib/replay-core/**` or `backend/app/services/activity_summary.py` | Runs vitest and pytest against `fixtures/activity` and reports typed and pasted differences | Majid |
| Typecheck on save | Save of `frontend/src/**/*.ts` or `*.tsx` | Runs `npm run typecheck` and summarizes errors | Ismail |
| Progress reminder (optional) | Task completion or manual trigger, if your Kiro build offers it | Drafts a progress entry from the diff using the template and asks you to confirm | all |

Example hook prompt (Contract guard):

```
When I save the API contract or a schema file, check that docs/api-contract.md, backend/app/schemas/*, frontend/src/api/types.ts and fixtures/api/*.json agree on field names and types. List every mismatch with file and field. Do not change any file.
```

## 6. Evidence checklist for the pitch

Capture while building, not afterwards.

- [ ] Steering panel showing `AGENTS.md` plus `product.md`, `tech.md`, `structure.md`.
- [ ] One spec with `requirements.md` (acceptance criteria), `design.md` and `tasks.md` with ticked tasks (one screenshot each).
- [ ] A hook firing and reporting a result.
- [ ] An agent session starting by reading `docs/progress.md` and stating its task ID.
- [ ] The git log showing task-ID commits from all three members.
- [ ] One moment where Kiro saved real time or caught a bug (one sentence plus a screenshot).
- [ ] Numbers: specs created, tasks completed by Kiro, hooks configured.

One slide with four boxes: **Steering** (shared rules), **Specs** (requirements to tasks), **Hooks** (guard rails), **Parallel agents** (3 members, 1 contract).

One sentence for the pitch: "Three of us ran three Kiro agents in parallel, all bound by the same steering and a frozen API contract, with specs driving each slice and hooks guarding the contract and the grading."

## 7. Troubleshooting

- Kiro ignores the rules: ask it to list loaded steering. Confirm `AGENTS.md` is in the workspace root. For custom agents, add the steering resource.
- Credits running low: use spec mode for the big slices only, and plain chat for small edits.
- Hook not firing: save from inside Kiro and check the hook is enabled in the panel.
- Spec drifts from the contract: fix the spec. The contract wins.
- Other tools are allowed, but the Kiro score needs real Kiro-built work. Build the core slices with Kiro.
