#!/usr/bin/env bash
# Extract the msgids (Python, Jinja, Vue/TypeScript), merge them into the .po files and
# compile them. Translate in project/translations/*/LC_MESSAGES/messages.po, then run
# this again (and `npm run i18n --prefix frontend` for the frontend's JSON).
set -euo pipefail
cd "$(dirname "$0")/.."

# `python -m` puts the repo root on sys.path, so babel.cfg finds scripts.babel_extract.
babel() { uv run python -m babel.messages.frontend "$@"; }

babel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -o messages.pot .
babel update -N -i messages.pot -d project/translations
babel compile -d project/translations
