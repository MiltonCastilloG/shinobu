---
name: current-task-update
description: "Update current-task/status.json from a compact Shinobu workflow summary. Status-update writer — never touches global-status.json. Use when Shinobu finishes a workflow step."
disable-model-invocation: true
---

# Status update (current-task-update)

Update per-task workflow state from Shinobu summary. Writes exactly one file: `current-task/status.json` under the task worktree.

**Never write `global-status.json`.** Registry write boundary: [global-status-format.md](global-status-format.md).

Schemas:

- Per-task: [status-format.md](status-format.md)
- Global registry (read only): [global-status-read.md](global-status-read.md)
- Legacy (deprecated): [current-task-context-format.md](current-task-context-format.md)

## When to use

- Shinobu completed `start`, `spec`, `gherkin`, `review`, `acceptance`, `sync`, or `integrate`.
- Shinobu needs next step, artifact pointers, or open questions persisted.
- Worktree exists; need init missing `current-task/status.json`.

## Required inputs

| Input | Required | Notes |
|-------|----------|-------|
| Worktree path | Yes | Absolute or repo-relative |
| Shinobu summary | Yes | Compact JSON summary of step result |

## Shinobu summary format

**Required:** none in the summary when Shinobu passes `--step` (position comes from
routing). Position-only writes (no completed step) still need `next_step`.

**Optional:** `completed_step` (overridden by `--step`), `artifact` (document
steps), `open_questions`, `summary`, `next_step` (Shinobu
override after review; otherwise routing supplies it when a step completed).
Position-only writes still need `next_step`.

**Blocked is not a field.** Non-empty `open_questions` holds `next_step` where it
was. Precedence on a completed step: an explicit summary `next_step` wins (Shinobu's
review verdict), then non-empty `open_questions` holds, then routing advances.

**CLI:** `--step <name>` names the dispatched step and wins over summary
`completed_step`. `--mode normal|jump` selects whether the write moves the task.
On `normal`, `next_step` is derived via `routing_write.next_step_for()` (including the
git tail and review readiness). On `jump`, `--step` is the **target** sheep step:
`next_step` becomes the target and `current_step` is left untouched — no summary
`artifact` required or materialized. Artifact pointers on normal writes use
routing's `artifact_key` (operational steps have none).

Minimal write (valid — advances next step only):

```json
{
  "next_step": "spec"
}
```

Full write (when a step completed):

```json
{
  "worktree": "projects/foo/worktrees/hero-section",
  "completed_step": "spec",
  "artifact": "current-task/specs/hero-section.json",
  "next_step": "gherkin",
  "open_questions": [],
  "summary": "Spec captured requirements and acceptance."
}
```

**`completed_step` semantics:** when present (or via `--step`), updates `task.current_step`,
may set artifact pointer, and derives `task.next_step` from routing on normal mode;
when absent, only advances `next_step` but **always writes `task.current_step`**
(preserve existing, or `"start"` on fresh init).

Also optional: `task` (slug, title, original, type), `git`, `artifacts`.

For gherkin: set `artifacts.story` from the summary `artifact` (usually `current-task/story.md`).

## Workflow

```
Task Progress:
- [ ] Resolve worktree scope
- [ ] Load existing status.json if present
- [ ] Parse Shinobu summary
- [ ] Validate transition
- [ ] Write current-task/status.json
- [ ] Report updated step and next step
```

### Step 1: Resolve scope

1. Resolve worktree to absolute path.
2. Derive `<slug>` from folder name.
3. Output: `current-task/status.json`.

**Scope rules:**

- Read `current-task/status.json` and artifact paths needed to validate.
- Write only `current-task/status.json`.
- **Never write `global-status.json`.**
- No shell commands.

### Step 2: Load and validate

- Validate against [status-format.md](status-format.md).
- `scope.worktree_path` must match command worktree.
- If missing: init from summary with `meta.schema: task-status.v2`.
- When the summary conflicts with existing status, write nothing: return the conflict as a question and stop.

### Step 3: Apply update

Emit simplified shape on every write. **Legacy migration:** when loading v1 status, drop `version`, `meta.generated_by`, `meta.updated_by`, `scope.worktree`, `task.story_artifact`, `artifacts.status`, `artifacts.review`, `task.last_completed_step`, `constraints`, and `history` — preserve essential routing fields and artifact pointers.

- `meta.schema: task-status.v2` only — do not write `meta.updated_by` or other ceremony fields
- `task.current_step`, `task.next_step` — drop legacy `task.completed_steps` if present
- Merge `artifacts`; review writes no file and sets no pointer
- **Describe:** replace `task.original` with slug or one-line title; set `artifacts.story`
- Acceptance: when `--step acceptance`, set `current_step` and derive `next_step` to `sync`; reject may populate `open_questions`
- **Jump (`--mode jump`):** set `next_step` to the target, leave `current_step` untouched, append one `task.side_effects` entry. Needs an existing `status.json` — jump never initialises a task.
- `open_questions` from summary; blocked when non-empty

### Step 4: Write and report

Report status path, completed step, next step, open questions.

## Safety rules

- Write only `current-task/status.json`.
- Never write `global-status.json`.
- Never write deprecated `status.json` for new tasks.
