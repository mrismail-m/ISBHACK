# VivaGrade

**Grade the work. Verify the learning.**

A teacher copilot built at Islamabad Hack 2026 (track: Education & Future of Work). AI drafts grades against the teacher's rubric and chosen strictness, students defend their own work in a short viva, and teachers can see how the work was written. The teacher always decides.

## Team

| Member | Slice |
|---|---|
| Adeel | AI core, integration, evaluation |
| Majid | Student app, writing evidence |
| Ismail | Teacher console, data and API |

## Quick start

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env            # set LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, or MOCK_LLM=1
python -m app.seed --reset
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env               # VITE_API_URL=http://localhost:8000
npm run dev                        # http://localhost:5173
```

Smoke test of the golden path (backend running): `python scripts/smoke.py`

All environment variables and commands: `.kiro/steering/tech.md`.

## Docs

| File | What it is |
|---|---|
| `AGENTS.md` | Rules for every coding agent: session protocol, ownership, git, briefs per member |
| `docs/architecture.md` | System design, data model, scoring rules, writing-process capture, decisions |
| `docs/api-contract.md` | The frozen API and event contract that lets three people build in parallel |
| `docs/ai-spec.md` | Grader, strictness table, feedback, viva, prompts, caching |
| `docs/evaluation.md` | How we measure accuracy, consistency and bias (the Trust report) |
| `docs/roadmap.md` | Milestones, tasks, cut lines, risks |
| `docs/progress.md` | Live log written by the agents, for context management |
| `docs/kiro-playbook.md` | How we use Kiro (steering, specs, hooks) and the evidence checklist |
| `docs/demo-script.md` | 4 minute pitch, live demo steps, fallbacks, Q&A prep |
| `.kiro/steering/` | Always-on Kiro context: product, tech, structure |

## Golden path

See `AGENTS.md` section 7. It must work on `main` at every sync.
