---
description: Create implementation plan with codebase analysis
argument-hint: <feature description | path/to/prd.md>
---

# Implementation Plan Generator

**Input**: $ARGUMENTS

## Objective

Transform the input into an implementation plan through codebase exploration and pattern extraction.

**Core Principle**: PLAN ONLY - no code written. Create a context-rich document that enables one-pass implementation.

**Order**: CODEBASE FIRST. Solutions must fit existing patterns.

---

## Phase 1: PARSE

| Input | Action |
| ------- | -------- |
| GitHub issue reference(s) (`11`, `#11`, `#11,#12`, issue URL), optionally followed by notes | `gh issue view <number> --json number,title,body,labels,state,comments` for each; use title, body and comments as the feature input, the notes as extra requirements |
| `.md` file | Read and extract the feature description |
| Free-form text | Use directly as feature input |
| Blank | Use conversation context |

Extract: the **problem**, the **user story**, the **type** (NEW_CAPABILITY / ENHANCEMENT /
REFACTOR / BUG_FIX), the **complexity** and, if available, the **GitHub issue** number (so
`/implement` can reference it).

---

## Phase 2: EXPLORE

Read `CLAUDE.md` and `AGENTS.md`, then find with file:line references:

1. **Similar implementations**: the closest existing route / page / task
2. **The flow** the change travels: Flask shell (`project/views/configuration.py`) →
   Vue page (`frontend/src/apps/importer/pages/`) → BFF route (`project/bff/`, `bff_route`
   + pydantic models in `schemas.py`) → models (`project/models.py`); or Celery task →
   `IcalImporter` → `ApiClient`
3. **Access rules**: how the existing routes scope data to the user's organizations
   (`get_configuration_or_404`)
4. **Test patterns**: `tests/conftest.py` fixtures, `tests/bff/`, the page specs and
   `mountPage` in the frontend

---

## Phase 3: DESIGN

- Which files are created, which modified, in which order?
- New or changed BFF model → regenerate `frontend/openapi.json` + `src/api/schema.d.ts`
- New page → shell route + router entry + BFF routes (never a server-rendered form)
- DB schema change → new Alembic migration (`uv run flask db migrate`, review it)
- New Celery task → `project/celery_tasks.py` (+ schedule in `setup_periodic_tasks`)
- New user-visible text → `t("...")` / `_("...")` and `./scripts/i18n.sh`
- Risks and how to mitigate them (the import talks to a live EventCally: what can a
  mistake create, change or delete there?)

---

## Phase 4: GENERATE

**Output path**: `.agents/plans/{YYYY-MM-DD}-{kebab-case-name}.plan.md` (date from
`date +%F`, never guessed; `mkdir -p .agents/plans`).

The plan contains: Summary, User Story, Metadata (type, complexity, systems affected,
GitHub issue), Patterns to Follow (actual snippets with `# SOURCE: file:lines`), Files to
Change (CREATE / UPDATE with purpose), Tasks (atomic, each with file, action, what to
implement, the pattern to mirror and a validation command), Validation and Acceptance
Criteria:

```bash
uv run isort . && uv run black . && uv run flake8
uv run pytest
npm run typecheck --prefix frontend && npm test --prefix frontend
```

---

## Phase 5: OUTPUT

Report the plan file, a 2-3 sentence summary, the scope (files to create / update, number
of tasks) and the key patterns. Always end with the implement command in a code block:

````markdown
```
/implement .agents/plans/{YYYY-MM-DD}-{name}.plan.md
```
````
