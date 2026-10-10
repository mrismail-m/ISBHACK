# Local demo

Teacher: `/login/teacher`, username `teacher`, password `Demo@123`.
Students: `/login/student`, username is any registration in `fixtures/demo/roster.json`, password `Demo@123`.
Example: `FA23-BAI-045` (MUHAMMAD MAJID ALI).

This is static demo authentication, not production authentication. Backend uses its existing seeded user header.
Only names and registration numbers were imported. All practice grades, viva scores and activity are synthetic.

From backend, run `python -m app.seed` on an empty database, then `python -m app.demo_seed`.
The demo installer updates the roster and adds three practice assessments without deleting existing work.
Run `python -m app.demo_fixtures` to regenerate isolated synthetic offline snapshots.
Start backend with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
Start frontend with `VITE_USE_FIXTURES=0` and `VITE_API_URL=http://127.0.0.1:8000` for live mode, or `VITE_USE_FIXTURES=1` for offline mode.

Teacher login opens the classroom dashboard. Select a student to inspect writing evidence or follow the review link.
Three completed practice assessments show 50 released synthetic submissions each. A1 is populated only where no existing submission exists; existing work is preserved. A2 stays open for new student writing. Teacher adjustments are seeded for selected practice records to populate override statistics.

Browser video and screenshot artifacts live locally in ignored `.cache/`; no provider credentials or database files are committed. Published demo media is in docs/demo-assets/.
