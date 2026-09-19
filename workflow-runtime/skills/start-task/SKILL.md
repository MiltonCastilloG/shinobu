---
name: start-task
description: "Pull main and create git worktrees for parallel task work."
---

# Start Task

Set up git worktrees via `create-worktree.py`. Pull `main` first. All worktrees live at workspace-root `worktrees/<project>-<slug>` (single hyphen).

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Work items | Yes | One or more tasks — slug-level labels are enough |
| Project | Yes | Registry project id (`shinobu` for self-tasks, or managed project name) |
| Workspace root | Yes | Script must run from workspace root |

## Procedure

```
Task Progress:
- [ ] Parse work items from the user message
- [ ] Classify each item and choose branch prefix + slug
- [ ] Confirm ambiguous classifications with the user
- [ ] Run create-worktree.py once per work item
- [ ] Report structured JSON handoff
```

### Step 1: Parse work items

Split the message into distinct work items (comma-separated, line breaks, or explicit prefixes like `fix:` / `chore:`).

A work item may be **minimal** — enough to classify the branch and derive a slug (e.g. `hero-section`, `fix footer`). A full job description is not required at start.

If the user provides a fuller description, pass it through in the report as original task text.

### Step 2: Classify and name branches

Pick a prefix and kebab-case slug for each item:

| Type | Prefix | When to use | Example |
|------|--------|-------------|---------|
| Feature | `feature/` | New user-facing behavior or UI | `feature/hero-section` |
| Fix | `fix/` | Bug fix | `fix/footer-link-404` |
| Chore | `chore/` | Tooling, deps, config, housekeeping | `chore/update-eslint` |
| Docs | `docs/` | Documentation-only | `docs/contributing-worktrees` |
| Refactor | `refactor/` | Behavior-preserving restructure | `refactor/extract-footer` |
| Test | `test/` | Test-only additions/fixes | `test/hero-coverage` |
| Perf | `perf/` | Performance improvement | `perf/lazy-load-images` |

**Slug rules:** lowercase, hyphens, no spaces. Derive from the description (e.g. "footer bug" → slug `footer-bug`, branch `fix/footer-bug`).

**Worktree path:** `worktrees/<project>-<slug>` — single hyphen between project and slug (e.g. `worktrees/shinobu-create-worktree-py`, `worktrees/tetris-clone-frp-hero-section`). Never use double hyphens or legacy `projects/*/worktrees/<slug>`.

If classification is ambiguous, return the candidates as a question in `open_questions` and stop before creating worktrees.

### Step 3: Run the script

From **workspace root**, run one invocation per work item:

```bash
python3 workflow-runtime/skills/start-task/scripts/create-worktree.py \
  --project shinobu \
  --slug create-worktree-py \
  --type chore \
  --original "create-worktree.py scripted flow"
```

Managed project example:

```bash
python3 workflow-runtime/skills/start-task/scripts/create-worktree.py \
  --project tetris-clone-frp \
  --slug hero-section \
  --type feature
```

The script:

1. Checks out `main` and runs `git pull` in the project git root
2. Creates `worktrees/<project>-<slug>` (managed projects use `projects/<project>` as git root)
3. Copies registry-declared locals (skips missing with notice)
4. Runs `post_create` hooks from `shinobu-workspace.yaml`
5. Scaffolds `current-task/` with initial `status.json`
6. Registers in `global-status.json` via `register-global-status.py` (per-project task id)

On success, read JSON handoff from stdout — no manual path derivation.

On failure, read `scripts/WORKFLOW.md` and complete remaining steps manually.

### Step 4: Report

Summarize from structured JSON output:

- Whether `main` was updated (warnings in handoff)
- Created worktree path, branch, task id, status path
- Skipped copy sources (warnings)
- Per created worktree: path, slug, branch, original task text, task type

## Safety rules

- Never force-push, `reset --hard`, or delete worktrees/branches without explicit user approval
- If a worktree or branch already exists, script errors — do not overwrite
- Run only from workspace root
- Do not commit or push unless the user explicitly asks

## Examples

**Input:** `redesign hero section` for project `castlemill-landing`

**Command:**

```bash
python3 workflow-runtime/skills/start-task/scripts/create-worktree.py \
  --project castlemill-landing \
  --slug hero-section \
  --type feature \
  --original "redesign hero section"
```

**Handoff fields:** `worktree_path`, `branch`, `task_id`, `status_path`, `registry_key`

