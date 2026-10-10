# API contract (v1)

Additive Learning Lab contract (M6.1, full feature assigned by Majid): see
[learning-lab.md](learning-lab.md). Existing grading and viva fields are unchanged.

Frozen at M0. Change only through the protocol in `AGENTS.md` section 5. Pydantic models in `backend/app/schemas/` and `frontend/src/api/types.ts` mirror this file exactly. Fixtures in `fixtures/api/` are valid example responses for every endpoint.

## Conventions

- Base path `/api/v1`. JSON only. `snake_case`. IDs are opaque strings. Timestamps are ISO 8601 UTC.
- No auth. The client sends `X-User-Id` (from the role switcher). `GET /users` lists seeded users.
- Criterion marks and work totals are multiples of 0.5. Blended final marks have 1 decimal. Percentages are floats with 1 decimal (0 to 100). Understanding and confidence are 0 to 1.
- Errors: HTTP status plus `{ "error": { "code": "...", "message": "..." } }`. Codes: `not_found`, `validation_error`, `forbidden`, `conflict`, `already_submitted`, `not_released`, `llm_unavailable`.
- LLM-backed endpoints answer within 30 seconds or fail with `llm_unavailable`. The UI shows progress.
- Student-facing responses never include `answer_key`, `model_answer_md`, other students' data, or the AI's internal notes.
- Shapes below use `//` comments for explanation only. Real JSON has none.
- Priority tags: unmarked is P0, P1 and P2 are marked.

## Endpoints

### Users and assessments (provider: Ismail)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/users` | | `User[]` |
| GET | `/me` | | `User` |
| GET | `/assessments?classroom_id=&status=` | | `Assessment[]` |
| POST | `/assessments` | `AssessmentCreate` | `Assessment` |
| GET | `/assessments/:id` | | `Assessment` |
| PATCH | `/assessments/:id` | partial `AssessmentCreate` | `Assessment` |
| POST | `/assessments/:id/publish` | | `Assessment` (status `open`) |
| POST | `/assessments/:id/close` | | `Assessment` (status `closed`) |
| GET | `/assessments/:id/questions` (P1) | | `Question[]` |

### Submissions and results (provider: Ismail)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/assessments/:id/submissions` | | `SubmissionRow[]` (teacher only) |
| POST | `/assessments/:id/submissions` | | `Submission` (idempotent: returns the student's existing one) |
| GET | `/submissions/:id` | | `Submission` |
| PUT | `/submissions/:id` | `{ content_md?, answers? }` | `Submission` (autosave; 409 `already_submitted` after submit) |
| POST | `/submissions/:id/submit` | | `Submission`. Starts background grading when `GRADE_ON_SUBMIT=1` |
| POST | `/submissions/:id/approve` | `ApproveRequest` | `Grade` |
| GET | `/submissions/:id/result` | | `StudentResult` (403 `not_released` until released) |

### AI setup and grading (provider: Adeel)

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/assessments/:id/rubric/draft` | `{ notes?: string }` | `Rubric` |
| POST | `/assessments/:id/strictness/preview` | `{ answer_text: string }` | `StrictnessPreview` |
| POST | `/submissions/:id/grade` | `{}` | `Grade` |
| POST | `/assessments/:id/grade-all` | `{}` | `{ queued: number }` |
| GET | `/assessments/:id/grading-status` | | `{ total, graded, in_progress, failed }` |
| GET | `/submissions/:id/grade` | | `Grade` or 404 |
| POST | `/submissions/:id/feedback/regenerate` (P2) | | `Feedback` |

### Viva (provider: Adeel)

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/submissions/:id/viva/start` | | `VivaStart` |
| POST | `/submissions/:id/viva/answer` | `VivaAnswer` | `{ ok: true, answered: number, remaining: number }` |
| POST | `/submissions/:id/viva/finish` | | `VivaResult` |
| GET | `/submissions/:id/viva` | | `VivaDetail` (teacher only) |

### Writing activity (provider: Majid)

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/submissions/:id/activity` | `ActivityBatch` | `{ received: number, last_seq: number }` |
| GET | `/submissions/:id/activity/summary?bucket=auto` | | `ActivitySummary` |
| GET | `/submissions/:id/activity/events` | | `ActivityEvents` |
| POST | `/submissions/:id/activity/paste-declaration` (P2) | `{ session_id, event_seq, source, note? }` | `{ ok: true }` |

### Analytics (provider: Ismail)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/assessments/:id/stats` | | `AssessmentStats` |
| GET | `/classrooms/:id/performance` | | `ClassPerformance` |
| GET | `/classrooms/:id/attention` | | `AttentionStudent[]` |
| POST | `/assessments/:id/grace/preview` | `{ marks, reason? }` | `GracePreview` |
| POST | `/assessments/:id/grace/apply` | `{ marks, reason }` | `GraceState` |
| POST | `/assessments/:id/grace/undo` | `{ entry_id? }` (default: latest) | `GraceState` |
| GET | `/assessments/:id/override-stats` | | `OverrideStats` |

### Evaluation (provider: Adeel)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/evaluation/trust-report` | | `TrustReport` (reads `backend/eval/reports/trust_report.json`) |

## Types

### User
```json
{ "id": "u_student_3", "name": "Ayesha K.", "role": "student", "classroom_id": "cl_1" }
```
`role`: `teacher` or `student`.

### Assessment
```json
{
  "id": "a_1",
  "classroom_id": "cl_1",
  "kind": "assignment",                        // assignment | quiz | exam
  "title": "A1: Hash table collisions",
  "instructions_md": "Explain how a hash table handles collisions in about 300 words.",
  "max_marks": 20,
  "pass_mark_pct": 50,
  "rubric": { "criteria": [] },                // Rubric, or null until drafted
  "model_answer_md": null,                     // null for students
  "strictness": "normal",                      // lenient | normal | strict | very_strict
  "viva_enabled": true,
  "viva_weight": 0.3,                          // 0 to 1, share of the final grade
  "viva_question_count": 3,
  "viva_time_limit_s": 90,                     // per question
  "feedback_mode": "full",                     // hints | full
  "release_mode": "after_approval",            // after_approval | auto
  "ai_policy": "allowed_with_disclosure",      // not_allowed | allowed_with_disclosure | allowed
  "paste_flag_chars": 500,
  "topics": ["hashing", "collisions", "complexity", "communication"],
  "status": "open",                            // draft | open | closed
  "due_at": "2026-10-12T18:00:00Z",
  "created_at": "2026-10-10T05:00:00Z"
}
```
`AssessmentCreate` is the same without `id`, `status`, `created_at`.

### Rubric
```json
{
  "criteria": [
    {
      "id": "c1",
      "name": "Concept accuracy",
      "description": "Explains what a collision is and why it happens, correctly.",
      "max_marks": 5,
      "topic": "hashing",
      "levels": [                              // exactly 5 strings, index = level 0..4
        "Absent or wrong",
        "Mentions the idea, mostly inaccurate",
        "Partly correct with clear gaps",
        "Mostly correct, minor gaps",
        "Correct, complete and precise"
      ]
    }
  ]
}
```
`max_marks` of all criteria MUST sum to `assessment.max_marks`.

### Question (P1, quiz and exam)
```json
{ "id": "q_1", "assessment_id": "a_2", "kind": "mcq", "text": "Which strategy stores colliding keys in a list?",
  "options": ["Linear probing", "Chaining", "Double hashing", "Cuckoo hashing"],
  "answer_key": 1, "marks": 1, "topic": "collisions" }
```
`answer_key` is never returned to students.

### Submission
```json
{
  "id": "s_1", "assessment_id": "a_1", "student_id": "u_student_3",
  "content_md": "# Collisions\n...", "answers": [],
  "status": "submitted",                       // draft | submitted | graded | approved | released
  "started_at": "2026-10-10T07:12:03Z", "submitted_at": "2026-10-10T07:40:10Z"
}
```
`answers` (quiz and exam): `[{ "question_id": "q_1", "choice": 1, "text": null }]`.

### SubmissionRow (teacher list)
```json
{
  "submission_id": "s_1",
  "label": "Student 03",                       // stable anonymous label for blind mode
  "student_id": "u_student_3",
  "student_name": "Ayesha K.",
  "status": "graded",
  "submitted_at": "2026-10-10T07:40:10Z",
  "ai_total": 15.5, "final_total": null, "max_marks": 20,
  "understanding": 0.35,                       // null if viva not done
  "score_pct": 64.8, "score_is_final": false,  // best available blended score
  "overall_confidence": 0.74,
  "flags": ["weak_viva", "paste_heavy"]        // derived on read, see architecture section 5
}
```

### Grade
```json
{
  "id": "g_1", "submission_id": "s_1",
  "status": "ai_draft",                        // ai_draft | approved
  "strictness_used": "normal",
  "prompt_version": "grader-v1", "model_id": "provider-model-name",
  "max_marks": 20,
  "criteria": [
    {
      "criterion_id": "c1",
      "level": 3, "minor_errors": 1, "ambiguous": false,
      "ai_marks": 4.0, "final_marks": 4.0,     // final_marks differs only after a teacher override
      "evidence": [
        { "quote": "a collision happens when two keys map to the same index", "start": 120, "end": 177, "verified": true }
      ],
      "reasoning": "Defines collisions correctly but does not mention the load factor.",
      "confidence": 0.82,
      "teacher_note": null
    }
  ],
  "ai_total": 15.5, "final_total": 15.5,
  "overall_confidence": 0.78,
  "grader_flags": ["low_confidence"],          // low_confidence | evidence_unverified | injection_attempt | needs_manual_grading
  "feedback": { "mode": "full", "strengths": [], "improvements": [], "next_step": "", "topics": [] },
  "teacher_note": null, "approved_at": null, "released_at": null
}
```
`start` and `end` are UTF-16 offsets into `content_md` (same as JavaScript).

### Feedback
```json
{
  "mode": "full",                              // hints | full
  "strengths": [
    { "criterion_id": "c1", "text": "You defined a collision clearly and used a good example.", "quote": "two keys map to the same index" }
  ],
  "improvements": [
    { "criterion_id": "c3", "text": "Your complexity discussion stays at the average case.",
      "quote": "lookups are fast", "hint": "What happens to lookup time when the table is almost full?",
      "explanation": "As the load factor approaches 1, chains grow or probe sequences lengthen, so lookups degrade toward O(n)." }
  ],
  "next_step": "Rewrite your complexity paragraph to compare the average and worst case for both strategies.",
  "topics": [ { "tag": "hashing", "level": "strong" }, { "tag": "complexity", "level": "weak" } ]
}
```
`topics[].level`: `strong`, `ok`, `weak`. `explanation` is present only when `mode` is `full`. At most 3 strengths and 3 improvements.

### StrictnessPreview
```json
{
  "levels": [
    { "strictness": "lenient",     "total": 17.5, "criteria": [ { "criterion_id": "c1", "marks": 4.5 } ] },
    { "strictness": "normal",      "total": 15.5, "criteria": [ { "criterion_id": "c1", "marks": 4.0 } ] },
    { "strictness": "strict",      "total": 14.0, "criteria": [ { "criterion_id": "c1", "marks": 3.5 } ] },
    { "strictness": "very_strict", "total": 11.0, "criteria": [ { "criterion_id": "c1", "marks": 2.5 } ] }
  ],
  "note": "One grading pass, four strictness policies."
}
```
Totals MUST be non-increasing from lenient to very_strict.

### ApproveRequest
```json
{
  "criteria_overrides": [ { "criterion_id": "c2", "marks": 3.5, "note": "Chaining example is incomplete." } ],
  "teacher_note": "Good work overall.",
  "feedback_edits": { "next_step": "..." },    // optional, replaces those feedback fields
  "release": true
}
```
Approve sets status `approved`. `release: true` also sets `released_at`. With `release_mode: auto` the grade is released automatically once approved.

### StudentResult
```json
{
  "submission_id": "s_1", "assessment_id": "a_1", "max_marks": 20,
  "work_marks": 15.5, "understanding": 0.72, "viva_weight": 0.3,
  "final_marks": 15.2, "grace_marks": 2.0, "final_with_grace": 17.2, "final_pct": 86.0,
  "feedback": { "mode": "full", "strengths": [], "improvements": [], "next_step": "", "topics": [] },
  "released_at": "2026-10-10T09:00:00Z"
}
```

### Viva
```json
// VivaStart
{ "session_id": "v_1",
  "questions": [ { "id": "vq_1", "kind": "justify",       // explain | change | defend | trace
                   "text": "You said open addressing slows down when the table fills up. Why does that happen?",
                   "topic": "complexity", "time_limit_s": 90 } ],
  "total_time_limit_s": 270 }

// VivaAnswer (request)
{ "question_id": "vq_1", "answer_text": "Because probes ...", "time_taken_s": 41, "pasted": false, "tab_switches": 0 }

// VivaResult (student sees only understanding)
{ "understanding": 0.72, "answered": 3, "total": 3 }

// VivaDetail (teacher)
{ "status": "done", "understanding": 0.72,
  "items": [ { "question_id": "vq_1", "text": "...", "answer_text": "...", "score": 1.0, "note": "Explains probe length growth clearly.",
               "time_taken_s": 41, "pasted": false, "tab_switches": 0 } ] }
```
Per-question `score` is 0, 0.5 or 1. A missing or timed-out answer scores 0. `pasted` and `tab_switches` are shown to the teacher only and are never given to the scorer.

### Activity events
```json
// ActivityEvent
{ "seq": 57, "t": 421000, "k": "paste", "from": 812, "to": 812, "text": "Hash tables are ..." }
```

| Field | Meaning |
|---|---|
| `seq` | integer, strictly increasing within a session, starts at 0 |
| `t` | milliseconds since session start (monotonic) |
| `k` | `start`, `end`, `type`, `paste`, `drop`, `cut`, `del`, `undo`, `redo`, `blur`, `focus`, `hidden`, `visible` |
| `from`, `to` | replace `doc[from:to]` with `text`. UTF-16 code units, in the document just before this event |
| `text` | inserted text. Empty for deletions and non-edit events |

Capture rules and the CodeMirror mapping: `docs/architecture.md` section 7.

```json
// ActivityBatch (request)
{ "session_id": "sess_a1", "session_started_at": "2026-10-10T07:12:03Z", "events": [ { "seq": 0, "t": 0, "k": "start", "from": 0, "to": 0, "text": "" } ] }

// ActivityEvents (response)
{ "sessions": [ { "session_id": "sess_a1", "started_at": "2026-10-10T07:12:03Z" } ],
  "events": [ { "session_id": "sess_a1", "seq": 0, "t": 0, "k": "start", "from": 0, "to": 0, "text": "" } ] }
```
Ingestion is idempotent: events with `seq` at or below the stored last `seq` for that session are ignored.

### ActivitySummary
```json
{
  "submission_id": "s_1",
  "final_chars": 3120,
  "typed_pct": 41.2, "pasted_pct": 58.8,
  "paste_chunks": [
    { "session_id": "sess_a1", "event_seq": 57, "at": "2026-10-10T07:19:04Z", "t": 421000,
      "chars": 1240, "survived_chars": 1180, "survived_pct": 95.2, "major": true, "declared_source": null }
  ],
  "revision_ratio": 0.18,
  "active_minutes": 34, "span_minutes": 190,
  "tab_switches": 7, "sessions": 2,
  "bucket": "minute",                          // minute | hour
  "heatmap": [ { "bucket_start": "2026-10-10T07:12:00Z", "edits": 42, "typed_chars": 180, "pasted_chars": 0 } ]
}
```

### AssessmentStats
```json
{
  "assessment_id": "a_1",
  "enrolled": 12, "submitted": 12, "graded": 12, "approved": 9, "released": 9, "pending_review": 3,
  "final": false,                              // true only when every submitted work is approved
  "avg_pct": 63.4, "median_pct": 65.0, "pass_rate_pct": 83.3, "highest_pct": 92.0, "lowest_pct": 31.0,
  "histogram": [ { "bin": "0-9", "count": 0 }, { "bin": "10-19", "count": 0 }, { "bin": "90-100", "count": 1 } ],
  "topic_averages": [ { "topic": "collisions", "avg_pct": 58.2, "n": 12 } ],
  "criterion_averages": [ { "criterion_id": "c1", "name": "Concept accuracy", "avg_pct": 71.0 } ],
  "grace_marks_applied": 0
}
```
`histogram` always has 10 bins: `0-9`, `10-19`, ..., `90-100`.

### ClassPerformance and AttentionStudent
```json
// ClassPerformance
{ "classroom_id": "cl_1",
  "assessments": [ { "assessment_id": "a_2", "title": "Quiz 1", "kind": "quiz", "due_at": "2026-09-20T00:00:00Z", "avg_pct": 71.0, "pass_rate_pct": 91.7 } ],
  "students": [ { "student_id": "u_student_3", "name": "Ayesha K.", "scores_pct": [72, 65, 64.8] } ] }

// AttentionStudent
{ "student_id": "u_student_9", "name": "Bilal R.",
  "reasons": ["below_pass_recent", "falling_trend"],   // below_pass_recent | falling_trend | low_understanding | missing_work
  "recent_scores_pct": [58, 49, 41], "last_understanding": 0.3 }
```

### Grace marks
```json
// request for preview: { "marks": 2, "reason": "Question 4 was ambiguous" }
// GracePreview
{ "marks": 2, "affected_students": 12, "capped_count": 1,
  "before": { "avg_pct": 63.4, "pass_rate_pct": 83.3 },
  "after":  { "avg_pct": 71.4, "pass_rate_pct": 91.7 } }

// GraceState
{ "total_marks": 2,
  "entries": [ { "id": "gr_1", "marks": 2, "reason": "Question 4 was ambiguous", "applied_at": "2026-10-10T10:00:00Z", "undone_at": null } ] }
```
Grace never exceeds `max_marks` for any student and never overwrites stored scores.

### OverrideStats
```json
{ "graded": 12, "overridden": 3, "override_rate_pct": 25.0,
  "mean_abs_delta_marks": 1.0, "mean_signed_delta_marks": -0.5,
  "by_criterion": [ { "criterion_id": "c2", "override_rate_pct": 33.3, "mean_signed_delta_marks": -0.5 } ] }
```
Delta is `final_marks - ai_marks`.

### TrustReport
```json
{
  "generated_at": "2026-10-10T11:00:00Z", "model_id": "provider-model-name", "prompt_version": "grader-v1",
  "dataset": { "assignment": "A1: Hash table collisions", "n_answers": 15, "n_raters": 2 },
  "accuracy": { "ai_vs_human_mae": 0.9, "human_vs_human_mae": 1.1, "ai_vs_human_qwk": 0.78, "human_vs_human_qwk": 0.74 },
  "consistency": { "runs": 5, "mean_range_marks": 0.3, "max_range_marks": 1.0 },
  "bias_probes": [ { "name": "padding", "n": 15, "mean_abs_delta_marks": 0.1, "max_abs_delta_marks": 0.5, "threshold_marks": 1.0, "passed": true } ],
  "strictness_ordering": { "passed": true, "violations": 0 },
  "editor_signals": { "samples": 9, "typed_flagged": 0, "pasted_flagged": 3, "retyped_flagged": 0 },
  "limitations": ["15 answers is a pilot, not proof"]
}
```
Numbers above are placeholders. The real values come from `docs/evaluation.md`.

## Fixtures

Every endpoint has an example response in `fixtures/api/` named after the endpoint. The frontend reads them when `VITE_USE_FIXTURES=1`. The backend returns the files in `fixtures/api/llm/` when `MOCK_LLM=1`.

| Fixture | Owner |
|---|---|
| `users.json`, `assessments.json`, `assessment_a1.json`, `submissions_a1.json`, `submission_s1.json`, `stats_a1.json`, `class_performance.json`, `attention.json`, `grace_preview.json`, `grace_state.json`, `override_stats.json`, `result_s1.json` | Ismail |
| `llm/rubric_draft.json`, `llm/grader_s1.json`, `llm/feedback_s1.json`, `llm/viva_questions_s1.json`, `llm/viva_scores_s1.json`, `grade_s1.json`, `strictness_preview.json`, `viva_start.json`, `viva_result.json`, `viva_detail_s1.json`, `trust_report.json` | Adeel |
| `activity_summary_s1.json`, `activity_events_s1.json`, plus `fixtures/activity/*` | Majid |
