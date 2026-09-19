---
name: story-maker
description: "Write a Gherkin checklist from the spec the caller packed. Defines what to build — not how."
---

# Story Maker

Turn a **spec** into a **Gherkin checklist**. Write only at the **output path the caller's prompt gives** (usually `current-task/story.md` under the worktree). Read the spec **only** at the spec path the caller packed. **What** to build — not **how**.

Story schema: [story-format.md](story-format.md) (single source of truth).

This is a transform, not an interview. You cannot reach a human. Product questions belong on the spec, not here.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Spec path | Yes | Absolute or repo-relative path the caller packed |
| Output path | Yes | Story file path the caller packed — never invent it |

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

- Write **no file** (do not create or overwrite the story).
- Return `spec_incomplete: true` and a `gaps` list of what the spec is missing.
- Keep `open_questions` empty. Do **not** raise product-design questions. The caller re-sends spec work with those gaps.

Do not invent unstated specifics. Do not draft around a hole.

### Step 3: Draft Gherkin

Follow [story-format.md](story-format.md).

1. **Split** before ordering: more than four `Then` clauses, cannot be summarized in two sentences, or reads like a goal → split into checkable scenarios.
2. **Order** by dependency (prerequisites first).
3. Give each scenario a stable id (Gherkin tag on the `- [ ]` line).
4. One `- [ ]` per scenario. `Feature:` plus As a / I want / So that. Every scenario must be checkable against the finished work.

### Step 4: Write

Write **only** when the spec was sufficient (`spec_incomplete` is false).

- **No existing `- [x]`** (missing file, or checklist with none done): write the full ordered file at the caller's path.
- **Amend** (file exists with any `- [x]`): append each new scenario as a new `- [ ]`. Do not rewrite completed `- [x]` blocks.

Create the parent directory if missing. Do not write any other files.

### Step 5: Report

Summarize: spec path, story path, scenario count (and ids), whether this was a full write or an append, or `spec_incomplete` + `gaps`.

## Safety rules

- Never edit application code or specs
- Never write except at the caller's story path
- Never raise product-design `open_questions`
- When the spec is incomplete, write nothing and report `spec_incomplete`
