# Deployment with Docker compose

## Build image

```sh
docker build -t eventcally/eventcally-ical-importer:latest .
```

## Configure

Copy `.env.example` to `.env` and enter values.

## Logs

The app, gunicorn and Celery write one JSON object per line (`LOG_FORMAT=json`, the
default; `console` for readable lines). Keep `LOG_LEVEL=INFO`: `DEBUG` writes the
requests to and responses from the EventCally API.

fluentd reads the logs of all containers on the host but keeps only those of the compose
project `FLUENTD_COMPOSE_PROJECT` (default `eventcally-ical-importer`, the `name` in
`docker-compose.yml`; set it when you start the stack with another `-p`). Docker adds the
project label to each log line (`x-logging` in `docker-compose.yml`); it applies to
containers created after the change, so recreate them with `docker compose up --detach`.
It writes to `FLUENTD_LOG_PATH`:

- `docker-error.*`: lines with an error level or worse. JSON records have `level`
  `error` or `critical`, with `event`, `logger`, `request_id` (web) or
  `task_id`/`task_name` (Celery) and the traceback in `exception`. Lines that are not
  JSON (PostgreSQL, Redis, `LOG_FORMAT=console`) keep their text in `log` and count by
  it: `[ERROR]`/`[CRITICAL]`, PostgreSQL `FATAL:`/`PANIC:`. Find a request's lines by its
  `X-Request-ID`: `grep '"request_id":"<id>"' docker-error.*`.

The errors are counted per day; the commented `mail` block at the end of
`fluentd-custom.config` sends the count with the messages.

`init.sh` copies `fluentd-custom.config` to `FLUENTD_CUSTOM_CONFIG_PATH`. After changing
it, copy it again and run `docker compose up --detach fluentd` (or `restart fluentd`).

## Initialize

```sh
./init.sh
```

## Start

```sh
docker compose up --force-recreate --detach
```

## Update app

Adjust `WEB_TAG` in .env if necessary.

```sh
./update.sh
```

## Execute commands in web container

```sh
docker compose exec -it web /bin/sh
```

## Worker active tasks

```sh
docker compose exec -it worker celery -A project.celery inspect active
```
