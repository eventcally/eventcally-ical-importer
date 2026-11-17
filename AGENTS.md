# AGENTS.md

Primary agent instructions live in [`CLAUDE.md`](CLAUDE.md). Read that first. This file supplements it with operational details.

## Lint order matters

Run in this order: each step may change files the next expects:
```
uv run isort . && uv run black . && uv run flake8
```
Or just: `uv run pre-commit run --all-files` (runs all hooks in the correct order).

## Tests

- `uv run pytest` needs only PostgreSQL: `TEST_DATABASE_URL` (from `.env` or the environment) must name a database whose name contains `test`. The suite creates the schema with `db.create_all()`, truncates every table after each test and drops the schema at the end.
- No Redis and no EventCally: Celery runs eagerly and the tests mock task calls (`mocker`) and HTTP (`requests_mock`).
- Key fixtures (`tests/conftest.py`): `app`, `db`, `client`, `seeder` (`setup_base()` → user, app installation, configuration ids), `utils` (`login(user_id)`, `post_json` / `put_json` with the CSRF token).
- A seeded user has a fresh `last_token_check` / `last_app_installations_sync`, so a request neither calls EventCally nor syncs; set them to `None` to test that path.
- **Tests mirror the source tree**: `project/bff/runs.py` → `tests/bff/test_runs.py`, `project/views/auth.py` → `tests/views/test_auth.py`.
- Test a route through the `client`, including the "foreign organization" case (expect 404).

## Frontend (Vue 3 + BFF)

See the "Frontend" section of `CLAUDE.md` for the rules. Workflow:

```bash
npm ci --prefix frontend
npm run dev --prefix frontend                              # Vite dev server on :5175
VITE_DEV_SERVER_URL=http://localhost:5175 uv run flask run --port 5002   # Flask serving the shells
npm run typecheck --prefix frontend && npm test --prefix frontend && npm run build --prefix frontend
uv run flask bff openapi > frontend/openapi.json && npm run gen:api --prefix frontend
```

- Page specs mock `@/shared/boot`, `@/shared/api` and `@/shared/notify` and mount with `mountPage` (`frontend/src/apps/importer/testing.ts`).
- `npm run build` writes to `project/static/dist/` (gitignored); without a build the shells render an empty page with a `vite entry ... not built` comment.

## Environment

- Entry point: `bootstrap.py` (set via `FLASK_APP` in `.flaskenv`); it imports the global `app` from `project/__init__.py`.
- Dev server: `uv run flask run --port 5002`.
- Docker Compose (`docker compose up --build`) runs everything: Postgres, Redis, Flask, Celery worker/beat, Flower; migrate with `docker compose exec web flask db upgrade` (the entrypoint only starts gunicorn).
- Debug stack: `docker compose -f docker-compose.yml -f docker-compose.debug.yml up --build` (bind-mounted source, debugpy on 5680 for Flask and 5681 for the worker, Vite dev server on 5175); VS Code attaches with "Docker: Flask/Celery" (`.vscode/launch.json`).
- Required env vars: `DATABASE_URL`, `EVENTCALLY_URL`, `EVENTCALLY_CLIENT_ID`, `EVENTCALLY_CLIENT_SECRET`, `EVENTCALLY_PRIVATE_KEY`, `EVENTCALLY_KID`, `EVENTCALLY_APP_ID`; optional `REDIS_URL`, `SECRET_KEY`, `SERVER_NAME`, `PREFERRED_URL_SCHEME`, `VITE_DEV_SERVER_URL`, `EVENTCALLY_SITE_NAME` (name of the EventCally instance in the UI texts, default `EventCally`). See `.env.example`.

## Common gotchas

- Regenerate `frontend/openapi.json` + `frontend/src/api/schema.d.ts` after changing BFF models; never hand-edit `schema.d.ts`; the SPA must not import Bootstrap CSS.
- `.env` holds real credentials (among them a multi-line private key): do not print it, and do not pass it to tools that echo parse errors (`uv run --env-file .env` does). Use the `flask` CLI or `dotenv run`.
- Throwaway debug output goes to `tmp/` (git and Docker ignored) or the session scratchpad, never the repo root; run `git status` before committing.
- flake8 ignores E501 (line length): Black handles formatting.

## Claude Code commands

`.claude/commands/`: `/prime` (load context), `/plan` → `/implement` (plan file in `.agents/plans/`, then build it), `/pr` (commit, push, open the PR, watch the checks), `/merge` (merge commit, back to `main`, delete the branch), `/release` (`scripts/release.sh`), `/ship` (plan → implement → PR → merge with a review gate after the plan and before the merge; uses the `planner` and `implementer` agents in `.claude/agents/`). The `agent-browser` skill (`.claude/skills/`) drives a browser through the `agent-browser` CLI, if it is installed.
