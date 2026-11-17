#!/bin/bash
set -e

docker compose up --detach web
docker compose exec web flask db upgrade
docker compose up --detach
