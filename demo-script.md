# Demo script

Rules: exactly 4 minutes including the live demo and judges' questions. Split: 1 minute problem and solution, 2 minutes live demo, 1 minute Q&A. Final score is the average across judges. Ties break on Prototype and Execution, then Impact, then Problem.

## Roles (suggested, swap freely)

| Role | Who | Does |
|---|---|---|
| Presenter | Adeel | Problem and solution (1:00), the close, Q&A on AI, bias and evaluation |
| Driver | Majid | Runs the laptop during the demo, narrates the student side |
| Teacher-side voice | Ismail | Narrates teacher screens, Q&A on dashboard, privacy and product, watches the clock |

One laptop, one driver. Everyone else stays still and quiet while the driver clicks.

## Minute 1: problem and solution (about 130 words)

> Marking is slow, inconsistent, and now polluted by AI. Teachers lose hours, marks drift with mood, and when students and teachers both lean on AI, learning fades.
>
> VivaGrade is a copilot, not a replacement. The teacher locks a rubric and picks a strictness. AI drafts the grade, and every mark comes with a quote from the student's own work. Then the student defends that work in a three question viva, and the teacher can see how it was written: what was typed, what was pasted, and a replay.
>
> AI drafts, the teacher decides, and students get feedback they can act on. We measured our own bias in a Trust report. And we built all of it today with three parallel Kiro agents, using specs, steering and hooks. Let me show you.

## Minutes 2 and 3: live demo (exactly 2:00)

| Time | Screen and clicks | Say | Proves |
|---|---|---|---|
| 0:00 to 0:15 | Teacher: open assessment A1 settings. Run **strictness preview** on a sample answer | "The teacher locks the rubric and picks strictness. Same answer at four levels: 17.5, 15.5, 14, 11. One AI pass, transparent rules." | Customization, consistency |
| 0:15 to 0:45 | Student: open A1, type two lines, paste the prepared block, submit. Start the viva, answer Q1, show the timer | "Students write in our editor. It records the writing process, only inside the editor. Then they defend their own work in a short viva." | Execution, learning is verified |
| 0:45 to 1:20 | Teacher: review queue in **blind mode**. Open the paste-heavy submission: marks with evidence quotes, flags (`paste_heavy`, `weak_viva`), replay jumping to the paste. Flip to the genuine submission for contrast. Approve and release | "Names are hidden by default. Every mark shows a verified quote. Flags are signals, not verdicts. The teacher approves." | Evidence, fairness, human in the loop |
| 1:20 to 1:35 | Student: result screen | "The student sees what went well, what to improve, and one next step." | Feedback, impact |
| 1:35 to 2:00 | Teacher: dashboard (stats, histogram, per-topic bars, attention list). Grace marks: preview, then apply +2. Flash the Trust report page | "Class stats, who needs attention and why. Grace marks with a preview and undo. And our own measured agreement with human markers." | Practicality, trust |

### Pre-staged state (set up before going on)

- [ ] `python -m app.seed --reset` run. Two submissions on A1 already created and graded with the cache warm: one genuine (typed, understood), one paste-heavy.
- [ ] A third student session ready for live typing. The paste block is in the clipboard. Viva answers are written down.
- [ ] Teacher tab and student tab open, browser zoom at 125%, notifications off, battery above 50% and charger in.
- [ ] You know how to switch to fixture mode (`VITE_USE_FIXTURES=1` or `MOCK_LLM=1`) in under 20 seconds.
- [ ] Phone hotspot ready as the network backup.
- [ ] Backup screen recording open in another window.

## Minute 4: Q&A prep

Keep every answer to two sentences.

| Question | Answer |
|---|---|
| Can't students just use AI for the viva? | We cannot make that impossible, but we raise the cost: questions are about their own text, timed, with paste blocked, and the teacher sees every answer and flag. Voice answers are the next step. |
| Is the AI biased? | We measured it: a human baseline, consistency over repeated runs, and six probes including AI-polished text and prompt injection. The numbers are on screen, and where it is worse than humans we say so. |
| What if the AI is wrong? | It is a draft. Every mark has a verified quote, low-confidence work is flagged, the teacher overrides, and we track override rates live. |
| What about privacy? | We record only inside the editor, with a visible banner. No screen or webcam capture, and student names never reach the model. |
| Isn't tracking pastes unfair? | They are signals for a conversation, never an automatic penalty. Moving your own text is excluded, and the teacher decides. |
| What about nervous students or non-native speakers? | The scorer judges understanding, not fluency. The viva weight is teacher-set, and per-student extra time is on our roadmap. |
| Why not use an AI detector? | Detectors are unreliable and accusatory. We verify understanding instead. |
| How does this save teacher time? | Teachers review flagged and low-confidence work and approve the rest quickly. Our estimate: 120 scripts at 5 minutes each is 10 hours of marking, and review replaces most of it (label it an estimate). |
| What did Kiro actually do? | Specs drove each slice, steering kept three agents aligned, and hooks guarded the contract and grading. Show the evidence slide. |
| How is this different from existing auto-graders? | We pair rubric-grounded, evidence-backed grading with a check of understanding and a writing-process record, and we publish our own bias measurements. The teacher stays in control. |
| What next? | Pilot with one class, add LMS import and a voice viva. |

## Fallbacks

| If | Do |
|---|---|
| LLM is slow or fails | Switch to the cached outputs (cache is warm) or `MOCK_LLM=1`. Say "this run is from cached results" and keep going |
| Backend crashes | Restart (`uvicorn`), `seed --reset` if needed, or switch to fixture mode. If it takes over 30 seconds, play the backup recording |
| Wi-Fi drops | Everything runs locally. Use the hotspot only if the LLM is needed live |
| The paste step misbehaves | Use the pre-staged paste-heavy submission instead of live typing |
| Time is running out | Skip the student result screen first, then the grace marks apply step (keep the preview) |

## Scoring map

| Criterion (points) | What judges see |
|---|---|
| Problem and Relevance (20) | Three pains in the first 30 seconds: time, inconsistency, AI eroding learning |
| Creativity and Innovation (20) | Grade the work, then verify the learning. No AI detector. Writing-process replay |
| Prototype and Execution (20) | A full golden path working live, built today |
| Impact and Practicality (15) | Teacher hours saved (estimate), consistent marks, dashboard, grace marks |
| Meaningful Use of Kiro (15) | Evidence slide and the one-sentence pitch line from `docs/kiro-playbook.md` |
| Presentation and Clarity (10) | Timed run, one driver, clear narration, honest answers |

## Slides (maximum 3)

1. **Problem.** Three pains and the marking-time estimate (labelled as an estimate). Shown only during minute 1.
2. **Solution and Kiro.** One architecture picture plus the four-box Kiro evidence. Backup for Q&A.
3. **Trust report.** The four numbers and the limitations. Backup for Q&A.

## Rehearsal plan

Do three timed runs: one normal, one with `MOCK_LLM=1`, one where the driver deliberately recovers from a failure. Stop each at 4:00 sharp and trim words, not the demo.
