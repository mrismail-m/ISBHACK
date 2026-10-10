# VPS deployment

VivaGrade runs at http://31.97.113.9:8088 in its own Docker Compose project.
The checkout is `/opt/vivagrade`. Existing host Nginx and other applications are unchanged.

The frontend serves the built React app and proxies `/api/` to the private backend.
SQLite and provider cache use the `vivagrade_data` and `vivagrade_cache` volumes.
Provider configuration is in `deploy/runtime.env`, mode 600, excluded from Git and image builds.

Run commands from `/opt/vivagrade`:

```sh
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d
docker compose -f deploy/compose.yaml logs --tail=100
```

For a fresh database only, run `docker compose -f deploy/compose.yaml run --rm backend python -c 'import app.models.grading; from app.seed import seed_db; seed_db()'`,
then `docker compose -f deploy/compose.yaml run --rm backend python -m app.demo_seed`.
The second command adds the 50-student cohort without deleting existing work.
Do not rerun the base seed on a populated database. Do not remove the data volume during updates.

Teacher login: `teacher`, password `Demo@123`. Students use their registration number with the same password.
Authentication remains the requested static login. This deployment uses HTTP on port 8088.
