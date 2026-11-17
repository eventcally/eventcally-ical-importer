# CLAUDE.md

Guidance for Claude when working in this repository.

> This is the primary agent instruction file. [`AGENTS.md`](AGENTS.md) supplements it with
> operational details (lint order, test setup, frontend workflow).

## Project Overview

**EventCally iCal importer** is an [EventCally](https://github.com/eventcally/eventcally)
app: organization admins log in with their EventCally account (OAuth), configure iCal feed
URLs per organization and map the feed's fields with Jinja templates; a Celery beat job
imports every feed once a day and creates, updates and deletes the events through the
EventCally REST API.

## Tech Stack

- **Runtime**: Python 3.12 (`.python-version`); deps in `pyproject.toml` + `uv.lock`, managed by uv; venv in `.venv/`
- **Web**: Flask 3 (Flask-SQLAlchemy, Flask-Migrate, Flask-WTF for CSRF, flask-babel), one global `app` in `project/__init__.py` (no factory)
- **Frontend**: Vite + TypeScript + Vue 3 + bootstrap-vue-next in `frontend/`, fed by the BFF (`/bff`, pydantic models → OpenAPI 3.1 → `openapi-fetch` types)
- **Tasks**: Celery 5 (Redis broker, celery beat; eager without `REDIS_URL`)
- **DB**: PostgreSQL via psycopg2 + SQLAlchemy 2 (JSONB columns); Alembic migrations in `migrations/`
- **EventCally access**: Authlib (user login via OAuth, app / app-installation access via a JWT bearer grant signed with the app's private key)
- **iCal**: `ics` 0.7.2 with `tatsu` pinned to 5.15.1 (newer versions crash the import on Python 3.12)
- **Server**: gunicorn
- **Tests**: pytest (pytest-mock, requests-mock); vitest for the frontend
- **Lint/format**: isort, black, flake8, pre-commit

## Commands

```bash
# Setup
uv sync                                        # creates .venv with runtime + dev deps
npm ci --prefix frontend

# Run locally (needs DATABASE_URL, EVENTCALLY_URL, EVENTCALLY_CLIENT_ID/_SECRET,
#              EVENTCALLY_PRIVATE_KEY, EVENTCALLY_KID, EVENTCALLY_APP_ID; see .env.example)
uv run flask db upgrade
npm run build --prefix frontend                # or the dev server, see AGENTS.md § Frontend
uv run flask run --port 5002
docker compose up --build                      # full stack: Postgres, Redis, Flask, Celery, Flower

# Test (needs TEST_DATABASE_URL: a PostgreSQL database whose name contains "test")
uv run pytest
uv run pytest tests/bff/test_runs.py::test_preview -v
npm test --prefix frontend                     # needs Node 22+

# After changing a BFF route or model
uv run flask bff openapi > frontend/openapi.json && npm run gen:api --prefix frontend

# Lint / format: order matters, run before commit
uv run pre-commit run --all-files
# equivalently:
uv run isort . && uv run black . && uv run flake8

# i18n: extract (Python, Jinja, Vue/TS), update the .po files, compile
./scripts/i18n.sh
```

## Structure

- `project/__init__.py`: creates the global `app`, `db`, `celery`, `csrf`, `oauth` and imports the routes at the end (module order matters; `from project import app, db` everywhere)
- `project/models.py`: `User` (EventCally tokens), `AppInstallation` (an organization that installed the app), `Configuration` (feed URL + mapper templates), `Run` + `LogEntry` (one import run), `ImportedEvent` (vevent UID ↔ EventCally event)
- `project/ical_importer.py`: `IcalImporter.perform(configuration)`: the import itself; `dry = True` only maps the feed and logs (the form's preview)
- `project/api_client.py`, `project/json_client.py`, `project/oauth_access.py`: the EventCally REST client
- `project/celery_init.py`, `project/celery_tasks.py`: Celery app and the periodic tasks (daily runs, installation sync, cleanup of old runs)
- `app_logging.py`: structlog formatter for the app, gunicorn (`GunicornLogger`) and Celery (`LOG_FORMAT=json|console`, `LOG_LEVEL`), log context helpers; `project/request_id.py`: `X-Request-ID` per request
- `project/utils.py`: `check_session_user` / `login_required` and the app-installation sync
- `project/bff/`: JSON for the Vue frontend under `/bff` (session + CSRF auth)
  - `routing.py`: `bff_route(...)` registers a view with pydantic query/body/response models and records it for OpenAPI
  - `schemas.py`: every pydantic model; `openapi.py`: the document (`flask bff openapi`)
  - `configurations.py`, `runs.py`: the routes; `get_configuration_or_404` scopes everything to the current user's organizations
- `project/views/`: `auth.py` (login, OAuth callback, logout), `root.py` (index, `/up` health check for the compose deployment), `configuration.py` (GET-only page shells of the Vue app)
- `project/vite.py`: the Jinja global `vite_entry(name)` (built bundle from `project/static/dist/`, or the dev server when `VITE_DEV_SERVER_URL` is set)
- `project/templates/`: `layout.html` (Bootstrap 5 frame with the navbar), `shell.html` (mount point + boot JSON), `index.html`
- `frontend/`: `src/apps/importer/` (entry `main.ts`, `router.ts`, `pages/`), `src/shared/` (boot, api client, i18n, toasts, formatting), `src/api/schema.d.ts` (generated)
- `scripts/`: `release.sh` (GitHub release of `main`; the tag triggers the Docker push; use `/release`), `i18n.sh`, `babel_extract.py` (extracts `t("...")` msgids from `.vue`/`.ts`)
- `tests/`: `conftest.py` (`app`, `db`, `client`, `seeder`, `utils`), `bff/`, `views/`; tests mirror the source tree
- `deployment/`, `doc/`

## Frontend (Vue 3 + BFF)

- Every page URL has a Flask shell in `project/views/configuration.py` and the same path in `frontend/src/apps/importer/router.ts`. The shell keeps the endpoint name (the navbar and redirects use `url_for`) and the login / 404 guard; the data comes from `/bff`. New pages add a shell plus BFF routes, never a server-rendered form.
- The Jinja frame provides Bootstrap 5 CSS/JS and the navbar; the SPA must not import Bootstrap CSS (only `bootstrap-vue-next`'s component styles, see `shared/boot.ts`).
- BFF routes are declared with `bff_route(...)`. The whole blueprint needs a session user (401 JSON otherwise; the frontend then sends the browser to the login) and checks the CSRF token (`X-CSRFToken`, from the boot JSON) on every unsafe method.
- Datetimes are stored as naive UTC; the BFF sends them with an offset (`UtcDateTime`), the frontend shows them in Europe/Berlin (`shared/format.ts`).
- Translations: the Babel `.po` files stay the single source. Use literal `t("English msgid")` calls in `.vue`/`.ts` (dynamic keys are not extracted). The form and run-count labels are field names on purpose (the mapper templates refer to them).
- A new Vite entry is registered in `frontend/vite.config.ts` and `project/vite.py:ENTRIES`.

## Pitfalls

- After changing BFF pydantic models regenerate `frontend/openapi.json` and `frontend/src/api/schema.d.ts` and commit both; never hand-edit `schema.d.ts`. `tests/bff/test_openapi.py` and the Frontend workflow fail on drift.
- Importing `project` needs `DATABASE_URL`, `EVENTCALLY_URL` and `EVENTCALLY_PRIVATE_KEY` in the environment (the `flask` CLI loads `.env`; plain `python` does not).
- Authorization is by organization: always go through `get_configuration_or_404` (and filter child objects by the configuration) instead of loading by primary key.
- `Configuration` writes go through `ConfigurationForm` (`extra="forbid"`); never `setattr` request data onto a model directly.
- The preview applies the form values to the loaded configuration and rolls back; keep it free of commits (`IcalImporter` does not commit, its callers do).
- New Celery tasks go into `project/celery_tasks.py`; `setup_periodic_tasks` holds the schedule.
- Run job ids are `run-<configuration id>-<uuid>`: the status route only answers for the configuration in its URL.
- Never hand-edit `uv.lock`: use `uv add <pkg>` / `uv add --dev <pkg>` / `uv lock --upgrade-package <pkg>`. CI and Docker run `uv sync --locked`, so commit `uv.lock` together with `pyproject.toml`.
- black, isort and flake8 are pinned in `pyproject.toml` in lockstep with `.pre-commit-config.yaml`; bump both together. Dependabot (`.github/dependabot.yml`) does not touch them, nor the setup-node `node-version`, the setup-uv `version` or the uv `COPY --from` tag in the `Dockerfile`.
- flake8 ignores E501/E203 (Black owns formatting).
- The frontend tests need Node 22+ (vitest 5); CI and the Docker build use Node 22.

## Key Files

- Wiring: `project/__init__.py`, `bootstrap.py` (`FLASK_APP` set in `.flaskenv`), `gunicorn.conf.py`, `entrypoint.sh`
- Import: `project/ical_importer.py`, `project/celery_tasks.py`
- BFF: `project/bff/__init__.py`, `project/bff/routing.py`, `project/bff/schemas.py`
- Frontend: `frontend/src/apps/importer/router.ts`, `frontend/src/shared/boot.ts`, `frontend/src/shared/api.ts`
- Tests: `tests/conftest.py`
- CI: `.github/workflows/{lint,test,frontend,docker-build}.yml`
- Docs: `doc/development.md`, `doc/deployment.md`, `README.md`
