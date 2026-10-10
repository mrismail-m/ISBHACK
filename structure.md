---
inclusion: always
---

# Structure

## Repo map

```
vivagrade/
  AGENTS.md                    rules for every agent (ownership, protocol, git)
  README.md
  .env.example
  docs/                        architecture, api-contract, ai-spec, evaluation, roadmap, progress, kiro-playbook, demo-script
  .kiro/
    steering/                  product.md, tech.md, structure.md
    specs/                     one folder per feature, created by Kiro (requirements, design, tasks)
    hooks/                     created in the Kiro Agent Hooks panel
  fixtures/
    api/                       example response per endpoint (frontend fixture mode)
    api/llm/                   canned LLM outputs (MOCK_LLM=1)
    activity/                  sample event logs plus expected_summary.json (parity tests)
    eval/                      eval answers and human scores
  scripts/
    smoke.py                   golden path smoke test
  backend/
    requirements.txt
    app/
      main.py                  app factory and router registration (Adeel only)
      config.py, deps.py, db.py, seed.py
      models/                  core.py, grading.py, activity.py, __init__.py
      schemas/                 core.py, grading.py, viva.py, activity.py, analytics.py (the contract)
      llm/                     client.py, cache.py, mock.py
      ai/                      rubric.py, grader.py, strictness.py, feedback.py, viva.py, mcq.py, prompts/
      routers/                 assessments.py, submissions.py, grading.py, viva.py, activity.py, analytics.py
      services/                scoring.py, flags.py, analytics.py, grace.py, activity_summary.py
    eval/                      run_eval.py, probes.py, metrics.py, reports/
    tests/
  frontend/
    src/
      api/                     client.ts, types.ts, teacher.ts, student.ts, activity.ts
      lib/replay-core/         pure TypeScript: apply events, authorship, heatmap, timeline
      features/student/        editor, viva, result
      features/insights/       replay viewer, paste chunks, authorship map, heatmap
      features/teacher/        setup, review, dashboard, grace marks, trust report
      components/ui/           shared UI
      routes.tsx
```

## Ownership
See `AGENTS.md` section 3. Edit only paths your member owns.

## Session rules
- Start: `git pull --rebase origin main`, read `docs/progress.md` and the current milestone in `docs/roadmap.md`.
- End: append your entry to `docs/progress.md`, tick boxes in `docs/roadmap.md`, commit, push.
- Contract changes follow `AGENTS.md` section 5.
