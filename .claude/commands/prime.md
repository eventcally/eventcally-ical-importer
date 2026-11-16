---
description: Prime agent with codebase understanding
argument-hint: [github-issues]
---

# Prime: Load Project Context

**Input**: $ARGUMENTS

## Objective

Build comprehensive understanding of this Flask + SQLAlchemy + Celery codebase with a
Vue 3 frontend (the EventCally iCal importer, an EventCally app that imports iCal feeds
through the EventCally REST API) by analyzing structure and key files.

## Process

### Step 0: Load External Context (if provided)

The argument is an optional GitHub issue reference or comma-separated list (e.g. `11` or
`#11,#12`, or a full issue URL).

If issues are provided, for each one run:

```bash
gh issue view <number> --json number,title,body,labels,state,comments
```

Use the issue title, body, labels, and comments to understand what work is expected. If the
repo has no GitHub remote configured, note that and continue with codebase analysis only.

### Step 1: Analyze the Codebase

1. Read `CLAUDE.md` and `AGENTS.md` for conventions and pitfalls
2. Study the app wiring: `project/__init__.py` (global `app`, `db`, `celery`, `oauth`),
   `bootstrap.py` (entrypoint)
3. Study the import: `project/models.py`, `project/ical_importer.py`,
   `project/api_client.py` / `project/json_client.py`, `project/celery_tasks.py`
4. Study the delivery: `project/bff/` (JSON for the frontend, `bff_route`, pydantic
   schemas), `project/views/` (login and the page shells), `frontend/src/apps/importer/`
5. Check recent commits with `git log --oneline -5`

## Output

Produce a scannable summary of what you learned:

- **Project Purpose**: One sentence
- **Tech Stack**
- **Data Model**: Core entities (from `project/models.py`)
- **Key Patterns**: page shell + BFF route + Vue page; organization-scoped access;
  dry run vs. real run of `IcalImporter`
- **Current State**: Recent commits, current branch, any issue context loaded

Use bullet points. Keep it concise.
