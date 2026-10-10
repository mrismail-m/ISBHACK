# Three-minute Learning Lab demonstration

## Opening, 25 seconds

"An assignment can be polished while a student still struggles to apply its ideas.
Our question is what to teach next. VivaGrade Learning Lab takes an idea from a
submission, changes the conditions, teaches the gap revealed by the answer, and
checks a different situation. Let us follow one student's reasoning."

## Demonstration, 100 seconds

1. Show the submitted hash-table explanation and its Learning Lab anchor quote.
2. Show the first scenario: many keys share one bucket. Enter a staged response
   that claims hashing always gives constant-time lookup.
3. Show the actual answer quote and observation. Read the short explanation:
   computing a bucket is different from searching inside it.
4. Show the second scenario: more buckets, same faulty mapping. Explain why
   resizing alone does not remove the crowded chain. Submit the response.
5. Show before/after reasoning. Switch to the teacher Learning Lab report and
   inspect the supporting answers. Point to the teaching priorities.

The offline demo uses a declared fixture pair and limited keyword rubric. State
that plainly. Live mode generates the second scenario AFTER the first answer,
targeting the observed gap. A controlled live-provider smoke result is saved in
docs/demo-assets/learning-lab-live-proof.json. It is not a student learning study.

## Close, 15 seconds

"The result is a teaching decision backed by two responses, not an accusation
about who wrote the assignment. We can show where the response improved and where
another teaching step is needed."

## Judge questions

"Is this a plagiarism checker?"
"This flow does not infer authorship. It gives an explanation and compares
reasoning on a different scenario; its output is learning evidence for the teacher."

"Couldn't I do this with prompts?"
"Yes. We coordinate each student's scenario, explanation, second attempt, and
class evidence in one workflow. The prototype demonstrates that complete loop."

"Is adaptive tutoring new?"
"Adaptive tutoring exists. We are demonstrating an assignment-based teaching
workflow with visible before/after evidence, not claiming to invent the field."

"Does this prove mastery?"
"Two responses are limited evidence. The teacher reviews them and decides what
to teach next; we would need a classroom pilot and delayed checks to measure learning."

## Cut list

During this pitch, skip AI detection, paste tracking, strictness controls, grace
marks, and generic analytics. Keep both scenarios and the teacher's actual evidence.
