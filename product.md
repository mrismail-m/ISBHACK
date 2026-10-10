---
inclusion: always
---

# Product: VivaGrade

Teacher copilot for grading. Tagline: grade the work, verify the learning. Built at Islamabad Hack 2026, track Education & Future of Work. Demo-first: a working golden path beats breadth.

## Users
- **Teacher:** sets up assessments (rubric, strictness, viva weight), reviews AI drafts, approves, reads the dashboard, adds grace marks.
- **Student:** writes in a markdown editor, takes a short viva, reads feedback (what went well, what to improve).

## Principles
1. AI drafts, the teacher decides. Nothing reaches a student before approval unless the teacher chose auto-release.
2. Evidence over scores: every criterion mark shows a verbatim quote from the student's work.
3. Consistency by construction: one locked rubric and strictness per assessment, names hidden from the AI, marks computed in code.
4. Verify learning, not authorship: no AI detectors. The viva and the writing-process record are evidence for a conversation, never an automatic penalty.
5. Privacy: record only inside the editor. No screen, webcam or off-app capture.

## Non-goals today
Logins, LMS integration, voice answers, plagiarism databases, mobile apps.

## Golden path
Defined in `AGENTS.md` section 7. It must work on `main` at every sync.

## Where to look
`docs/architecture.md`, `docs/api-contract.md`, `docs/ai-spec.md`, `docs/roadmap.md`, `docs/progress.md`
