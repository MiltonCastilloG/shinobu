---
name: spec-maker
description: "Analyze a task and write a JSON spec. Defines what to build — not how."
---

# Spec Maker

Analyze a task and produce a **JSON spec**. The spec defines **what** to build — not **how**. No file paths, no create/modify steps.

Spec schema: [spec-format.md](spec-format.md) (single source of truth).

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Worktree path | Yes | Absolute or repo-relative (e.g. `worktrees/hero-section`) |
| Task description | Yes* | Whatever the prompt supplies — Gherkin, free text, or `task.original` |
| Output path | No | Default `current-task/specs/<slug>.json` under scope root; agent may override |
| `meta.context` | No | Optional traceability path; set only when the agent passes one |

\*When the description is missing or too vague to list testable requirements, return the question in `open_questions` and stop.

## Procedure

```
Task Progress:
- [ ] Resolve and validate worktree scope
- [ ] Parse task description (stop with a question if vague)
- [ ] Light context read (CONTRIBUTING if exists, project layout)
- [ ] Draft JSON spec
- [ ] Write spec file
- [ ] Report summary
```

### Step 1: Resolve worktree scope

1. Resolve the worktree path to an **absolute** path.
2. Confirm the directory exists.
3. Set the **scope root** to that absolute path. Derive `<slug>` from the final folder name (e.g. `worktrees/hero-section` → slug `hero-section`).
4. Default output: `current-task/specs/<slug>.json` relative to the scope root.
5. Infer `branch` from git when possible (e.g. `feature/hero-section`); omit if unknown.

**Scope rules (non-negotiable):**

- **Read** anywhere under the scope root and CONTRIBUTING.md.
- **Write** only to the spec output path (create parent directory if missing).
- Never edit `src/`, `app/`, config, tests, or any application files.
- Never modify files outside the scope root.

### Step 2: Parse task description

When the input is Gherkin (`Feature:`, scenarios, **As a / I want / So that**), derive requirements and acceptance from it. Set `meta.task` to the full story text.

Otherwise extract what the user wants built or fixed. Stop with a question if:

- The outcome is vague ("improve", "modernize", "clean up") with no measurable target
- Scope is unclear (which page, which component, which behavior)
- Multiple valid interpretations exist and the user has not chosen one
- A design fork affects requirements (CTA link, copy, visual approach)

**Stop, don't guess:** you cannot reach a human. Write no spec file while questions remain — return them in `open_questions`, naming the forks and their candidate answers, and stop. Your caller gets the answers and re-spawns you. When your prompt gave you a pause path, save what you explored first (`workflow-runtime/skills/pause-context/SKILL.md`) so the re-spawn does not repeat the work. Write only once `open_questions` is `[]`.

### Step 3: Light context read

Use read, grep, glob, or semantic_search **lightly** to bound scope realistically:

- Read the project's `CONTRIBUTING.md` when present — missing file OK; record assumptions inline in spec
- Skim top-level layout (`app/`, `src/components/`, `src/features/`) to know what areas exist
- Do **not** explore file-by-file or draft implementation steps

### Step 4: Draft the JSON spec

Follow the schema in [spec-format.md](spec-format.md). Output **JSON only**.

Include:

- `meta` — `worktree`, `generated_by: spec-maker`, `task`, optional `branch`, optional `context` when agent supplied
- `title` — short task name
- `type` — `feature`, `fix`, `chore`, `docs`, `refactor`, `test`, or `perf`
- `summary` — one-paragraph goal
- `requirements` — ordered, testable items with `id` and `description`
- `scope` — `in` / `out` lists bounding the work
- `constraints` — default to `no-commit` and `no-new-deps` unless the task requires otherwise
- `acceptance` — verifiable done criteria
- `assumptions` — defaults applied when the task was silent
- `open_questions` — empty list, or unresolved items

**Do not:**

- Name file paths or symbols
- Include create/modify/delete/run/verify steps
- Guess on design forks — return them in `open_questions` and stop

### Step 5: Write the spec file

Written file **must** include `open_questions: []` (Step 2 gate).

1. Create the output directory under the scope root if it does not exist.
2. Write the complete JSON to the output path.
3. Do not write any other files.

### Step 6: Report

Summarize:

- Scope root used
- Spec file path
- Task type and requirement count
- Scope in/out summary
- Constraints applied
- Any `open_questions` remaining

## Safety rules

- Never edit application code — only the spec JSON file
- Never modify files outside the scope root
- Never force-push, `reset --hard`, or delete worktrees/branches without explicit user approval
- Do not commit or push unless the user explicitly asks
- When in doubt, return the question in `open_questions` and stop — do not guess
