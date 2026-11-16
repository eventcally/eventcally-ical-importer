---
description: Execute an implementation plan with validation loops
argument-hint: <path/to/plan.md>
---

# Implement Plan

**Plan**: $ARGUMENTS

## Your Mission

Execute the plan end-to-end with rigorous self-validation.

**Golden Rule**: If validation fails, fix it before moving on. Never accumulate broken state.

---

## Phase 1: LOAD

Read the plan: summary, patterns to mirror, files to change, tasks, validation commands
and the GitHub issue number, if any. If the plan is not found, stop and say so
(`/plan "feature description"` creates one).

## Phase 2: PREPARE

```bash
git branch --show-current
git status
```

| State | Action |
| ------- | -------- |
| On `main`, clean | Create a branch: `git checkout -b issue/{plan-name}` (prefix the name with the issue number if the plan has one) |
| On `main`, dirty | STOP: "Stash or commit changes first" |
| On a feature branch | Use it |

## Phase 3: EXECUTE

For each task in the plan:

1. **Verify assumptions**: read the target file, what it imports and what imports it. If
   the plan's references do not match the code, adapt and document the difference.
2. **Implement** following the MIRROR reference. Check the integration points:
   - BFF route or model changed → `uv run flask bff openapi > frontend/openapi.json && npm run gen:api --prefix frontend`
   - new page → shell in `project/views/configuration.py` and route in `frontend/src/apps/importer/router.ts`
   - schema change → Alembic migration
   - new Celery task → `project/celery_tasks.py`
   - every object is loaded through the user's organizations (`get_configuration_or_404`)
3. **Validate immediately** on the changed files:
   `uv run isort <files> && uv run black <files> && uv run flake8 <files>`
4. **Track progress** and document every deviation from the plan.

## Phase 4: VALIDATE

```bash
uv run isort . && uv run black . && uv run flake8
uv run pytest
# only if frontend/ or BFF models changed
npm run typecheck --prefix frontend && npm test --prefix frontend
git diff --exit-code frontend/openapi.json frontend/src/api/schema.d.ts   # after regenerating
```

Write tests for new code: every new route needs a test through the `client` fixture
including the foreign-organization case; every new page a spec. Update tests when behavior
changed.

**End-to-end**: start the app (`npm run build --prefix frontend`, `uv run flask run`),
exercise the new or changed behavior in the browser or with the route, and confirm it
works. Static checks and unit tests alone are never sufficient. Never start a real import
run against a production EventCally to test.

## Phase 5: REPORT

Summarize what was built, the files changed, the deviations from the plan, which checks
ran with their results, and what was verified end to end. Do not commit or open a PR
unless asked (`/pr` does that).
