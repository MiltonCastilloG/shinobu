---
name: scenario-maker
description: "Write scenarios.json (an ordered array of Gherkin scenarios) from the spec the caller packed. Defines what to build — not how."
---

# Scenario Maker

Turn a **spec** into **`scenarios.json`**: an ordered array of scenarios, each holding one Gherkin `Scenario:` block. Write only at the **output path the caller's prompt gives** (usually `current-task/scenarios.json` under the worktree). Read the spec **only** at the spec path the caller packed. **What** to build — not **how**.

Scenario schema: [scenario-format.md](scenario-format.md) (single source of truth).

This is a transform, not an interview. You cannot reach a human. Product questions belong on the spec, not here.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Spec path | Yes | Absolute or repo-relative path the caller packed |
| Output path | Yes | `scenarios.json` path the caller packed — never invent it |

## Procedure

```
Task Progress:
- [ ] Read the spec at the packed path
- [ ] Stop without write if the spec cannot yield testable Gherkin
- [ ] Draft scenarios (split, then order by dependency)
- [ ] Write only at the caller's path (full write or append)
- [ ] Report summary
```

### Step 1: Read the spec

Read the spec file at the path the caller packed. Do not search for another spec. Do not interview. Do not load chat as the source of truth.

### Step 2: Incomplete spec → write nothing

The spec is incomplete when it lacks testable outcomes, bounded scope, or acceptance needed for checkable Gherkin — or when a requirement is too vague to turn into a scenario without inventing product specifics.

Then:

- Write **no file** (do not create or overwrite `scenarios.json`).
- Return `spec_incomplete: true` and a `gaps` list of what the spec is missing.
- Keep `open_questions` empty. Do **not** raise product-design questions. The caller re-sends spec work with those gaps.

Do not invent unstated specifics. Do not draft around a hole.

### Step 3: Draft scenarios

Follow [scenario-format.md](scenario-format.md).

1. **Split** before ordering: more than four `Then` clauses, cannot be summarized in two sentences, or reads like a goal → split into checkable scenarios.
2. **Order** by dependency (prerequisites first). Array order is the dependency order.
3. Give each scenario a stable, unique, kebab-case `id`, a `title`, and a `gherkin` string holding the full `Scenario:` block. Set `done: false`.
4. Fill `feature` with the title and one As a / I want / So that set. Every scenario must be checkable against the finished work.

### Step 4: Write

Write **only** when the spec was sufficient (`spec_incomplete` is false).

- **No scenario with `done: true`** (missing file, or a file with none done): write the full ordered JSON file at the caller's path.
- **Amend** (file exists with any `done: true`): append each new scenario as a new object with `done: false` at the end of `scenarios`. Do not rewrite, reorder, or touch any entry with `done: true`.

Create the parent directory if missing. The file must be valid JSON. Do not write any other files.

### Step 5: Report

Summarize: spec path, scenarios path, scenario count (and ids), whether this was a full write or an append, or `spec_incomplete` + `gaps`.

## Safety rules

- Never edit application code or specs
- Never write except at the caller's `scenarios.json` path
- Never set `done: true` — only the loop does
- Never raise product-design `open_questions`
- Never rewrite an entry with `done: true`
- When the spec is incomplete, write nothing and report `spec_incomplete`
