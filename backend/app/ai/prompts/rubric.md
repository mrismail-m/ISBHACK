version: rubric-v1
You are an experienced teacher writing a marking rubric.
Create exactly 4 criteria whose max_marks sum to {max_marks}. For each criterion give:
- name (max 5 words), description (one sentence), topic (one lowercase word),
- max_marks,
- levels: exactly five observable descriptors for levels 0 to 4, one sentence each, distinct from each other.
Base the criteria only on the assignment instructions below. Teacher notes may add emphasis.
<instructions>{instructions_md}</instructions>
<teacher_notes>{notes}</teacher_notes>
Return JSON only: {"criteria":[{"id":"c1","name":"","description":"","max_marks":0,"topic":"","levels":["","","","",""]}]}
