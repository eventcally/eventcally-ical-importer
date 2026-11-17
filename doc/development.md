# Development

Requirements: [uv](https://docs.astral.sh/uv/), Node 22, PostgreSQL, Redis (optional:
without `REDIS_URL` Celery tasks run eagerly in the web process).

```sh
uv sync                        # creates .venv with runtime + dev deps
cp .env.example .env           # then fill in the EventCally app credentials
uv run flask db upgrade
npm ci --prefix frontend
npm run build --prefix frontend
uv run flask run --port 5002
```

Dependencies live in `pyproject.toml` + `uv.lock`. Add one with `uv add <pkg>`
(`uv add --dev <pkg>` for a dev tool); never edit `uv.lock` by hand.

## Frontend (Vue 3 + BFF)

The pages are thin Flask shells (`project/views/configuration.py`) that mount the Vue app
of `frontend/`; the app reads and writes through the JSON routes under `/bff`
(`project/bff/`).

```sh
npm run dev --prefix frontend                              # Vite dev server on :5175
VITE_DEV_SERVER_URL=http://localhost:5175 uv run flask run --port 5002
npm run typecheck --prefix frontend && npm test --prefix frontend && npm run build --prefix frontend
```

After changing a BFF route or pydantic model regenerate the contract and commit both files
(pytest and CI check the drift):

```sh
uv run flask bff openapi > frontend/openapi.json && npm run gen:api --prefix frontend
```

## Tests

The tests need a PostgreSQL database that `TEST_DATABASE_URL` points to (its name must
contain `test`; every test truncates all tables). No Redis and no EventCally needed.

```sh
createdb eventcally_ical_importer_tests
uv run pytest
uv run pytest --cov=project --cov-report=term-missing
```

## Lint

```sh
uv run pre-commit run --all-files
# equivalently:
uv run isort . && uv run black . && uv run flake8
```

## Docker

### Compose (including dependencies)

Running at [http://127.0.0.1:5002]
Celery Flower at [http://127.0.0.1:5557]

```sh
docker compose up --build
```

### Compose with debugger and Vite dev server

With `docker-compose.debug.yml` the source is bind-mounted, Flask (port 5680) and the
Celery worker (port 5681) listen for a debugger and the Vite dev server runs as the `vite`
service (port 5175, hot reload), so no local Python or Node is needed:

```sh
docker compose -f docker-compose.yml -f docker-compose.debug.yml up --build
```

The overlay also makes the login against a local EventCally work (the eventcally dev stack
on host port 5000): keep `EVENTCALLY_URL=http://127.0.0.1:5000` in `.env`; the
`web-eventcally` and `worker-eventcally` services forward that address from inside the
containers to the host. The redirect URI of the OAuth client in EventCally is
`http://127.0.0.1:5002/authorize`. The plain `docker compose up` has no such forwarding.

Attach with the VS Code launch configuration "Docker: Flask/Celery". Without Docker, the
compounds "Flask/Vite" and "Flask/Celery" start Flask, the Vite dev server and the worker
locally.

## Logging

The app, gunicorn and Celery log through one structlog formatter
(`app_logging.py`). `LOG_FORMAT=json` (the default, used by the deployment's
fluentd) writes one JSON object per line; `console` writes readable lines. `.flaskenv`
and the dev compose set `console`. `LOG_LEVEL` (default `INFO`; the dev compose uses
`DEBUG`) applies to all loggers. Each web line carries the `request_id` (`X-Request-ID`,
echoed in the response), and each Celery line the `task_id`/`task_name` (plus the
`request_id` of the request that queued the task). Pass structured fields with
`extra=`, e.g. `app.logger.info("imported", extra={"configuration_id": 1})`.

## Database

```sh
uv run flask db migrate
uv run flask db upgrade
```

## i18n

<https://python-babel.github.io/flask-babel/>

The Babel `.po` files are the single source, also for the frontend: use literal
`t("English msgid")` calls in `.vue`/`.ts` files.

### Extract new msgid's, merge them into the \*.po files and compile

```sh
./scripts/i18n.sh
```

Translate in `project/translations/<locale>/LC_MESSAGES/messages.po`, then run the script
again. `npm run i18n --prefix frontend` (part of `npm run build`) turns the `.po` files
into the frontend's `src/locales/*.json`.

### Add locale

```sh
uv run python -m babel.messages.frontend init -i messages.pot -d project/translations -l en
```

## Celery

```sh
uv run celery -A project.celery worker --loglevel=info
uv run celery -A project.celery beat --loglevel=info
uv run celery -A project.celery purge
```
