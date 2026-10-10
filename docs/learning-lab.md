# Learning Lab, M6.1

Majid assigned the complete feature to this agent on 2026-10-11, extending the
original feature freeze. Existing grades and viva retain their original meaning.

The student applies a concept from their submitted assignment in a changed
situation, receives a targeted explanation, and tries a different scenario.
The teacher reviews both answers and suggested teaching priorities. Improvement
is reported only when the second response receives a higher level, never assumed.
This is formative practice, independent of grading and authorship detection.

## Additive API

Base /api/v1. Existing X-User-Id demo access convention applies.

| Method | Path | Result |
|---|---|---|
| POST | /submissions/{id}/learning-lab/start | LabState, create or resume |
| GET | /submissions/{id}/learning-lab | LabState, 404 before start |
| POST | /submissions/{id}/learning-lab/answer | LabState, advance one phase |
| GET | /assessments/{id}/learning-lab | LabReport, class teachers only |

Answer body: phase (challenge/recovery), answer_text (1 to 3,000 characters).
Whitespace-only answers fail. Identical answers replay safely. Replacement
answers and skipped phases return 409.

LabState: id, submission_id, assessment_id, concept, anchor_quote, phase
(challenge/recovery/complete), challenge {scenario, question}, recovery (same shape,
null before first answer), initial_answer, recovery_answer, initial, final,
mode (live/fixture), created_at (UTC ISO).

initial/final: nullable LabObservation with level (0/1/2), reasoning, suspected_gap,
answer_quote, teaching. Quotes are verified against the response before saving.
Level 2 clears suspected_gap. LabReport: assessment_id, sessions (LabState[]).
Private evaluation criteria stay server-side; the second question is hidden until
the first answer is saved. New table learning_lab_sessions is created on startup.
Atomic phase transitions prevent concurrent replacement answers. No student
identity or activity records go to the model.

## Demo

1. Sign in as student, submit the hash-table assignment, then select Learning Lab
   from its assessment card or result page.
2. Give a first answer that misses the mechanism. Read the explanation.
3. Reason through the second scenario correctly. Show the before/after evidence.
4. Sign out, sign in as teacher, open Learning Lab in navigation. Choose the same
   assessment and inspect the two actual answers and teaching priorities.

The second scenario in live mode is generated after the first answer, targeting
the observed gap and explanation rather than using the original plan unchanged.

Live mode uses the existing provider configuration, four model completions per
experiment plus grounding/repair retries. MOCK_LLM=1 and VITE_USE_FIXTURES=1 use a
declared hash-table scenario pair and limited keyword rubric, clearly labeled.
Browser fixtures persist in localStorage; live evidence persists in SQLite.
Fixtures demonstrate the flow, not model accuracy or measured learning gains.

Pitch: "We changed the conditions, taught the gap the answer revealed, and tested
a different situation. Here are the two responses for the teacher."

Do not claim invention of adaptive tutoring, lasting mastery, plagiarism detection,
or measured educational improvement from a staged demonstration.
