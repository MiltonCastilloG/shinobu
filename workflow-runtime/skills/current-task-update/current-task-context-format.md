# Current task context format (deprecated)

> **Deprecated.** Use [status-format.md](status-format.md) (`current-task/status.json`) and [global-status-format.md](global-status-format.md) (`global-status.json`). Do not write this file for new tasks.

`current-task/current-task-context.json` was the legacy task-local workflow context. It stores task identity, worktree scope, artifact paths, the current workflow step, blockers, and history so Shinobu can orchestrate sheep without relying on chat memory.

The file lives inside the worktree:

```
current-task/
  status.json
  specs/<slug>.json
  subtasks/<slug>.md
  reviews/<slug>.json
  review-validations/rN-validation.json
  review-inputs/rN-review.json
  next-steps/*.json
  syncs/<slug>.json
  integrates/<slug>.json
```

`current-task-update` is the only writer for this file. Artifacts should reference it with `meta.context` when their schema allows metadata.

## Top-level fields

| Field | Required | Description |
|-------|----------|-------------|
| `meta` | Yes | Schema and writer metadata |
| `task` | Yes | Task identity and workflow step pointers |
| `git` | No | Branch/base information when known |
| `scope` | Yes | Worktree slug and path |
| `artifacts` | Yes | Known task artifact paths |
| `constraints` | No | Constraints inherited by downstream agents |
| `open_questions` | Yes | Blockers or user decisions needed before continuing |
| `history` | Yes | Append-only workflow events |

## `meta`

| Field | Required | Description |
|-------|----------|-------------|
| `schema` | Yes | Always `current-task-context.v1` |
| `generated_by` | Yes | Always `current-task-update` |
| `updated_by` | Yes | Always `current-task-update` |

## `task`

| Field | Required | Description |
|-------|----------|-------------|
| `slug` | Yes | Worktree folder slug, e.g. `hero-section` |
| `title` | No | Short task title |
| `original` | Yes | Raw user task text from start (may be slug-level only) |
| `story` | No | Gherkin-style user story — required before `spec`; written during the `describe` step |
| `type` | No | `feature`, `fix`, `chore`, `docs`, `refactor`, `test`, or `perf` |
| `current_step` | Yes | Step Shinobu is preparing or just handed off |
| `next_step` | Yes | Next step Shinobu should propose |
| `last_completed_step` | No | Latest completed step |

Do not add a broad task-level `state` enum. `current_step`, `next_step`, `last_completed_step`, `open_questions`, and `history[].status` are the source of truth.

### `task.story` (Gherkin user story)

Set during the `describe` step, after the worktree and context file exist. Use a multi-line string with this shape:

```json
{
  "story": "Feature: Hero section redesign\n\nAs a site visitor\nI want to see a clear headline, subcopy, and call-to-action on the home page\nSo that I understand the product and know what to do next\n\nScenario: Home page hero displays key content\n  Given I am viewing the home page\n  When the page loads above the fold\n  Then I see a prominent headline\n  And I see supporting subcopy beneath the headline\n  And I see a primary call-to-action button\n"
}
```

Rules:

- Include `Feature:` and the classic **As a / I want / So that** user story.
- Add at least one `Scenario:` with `Given` / `When` / `Then` (and `And` as needed).
- Keep scenarios testable and specific to the task outcome — not implementation steps.
- Do not proceed to `spec` until `task.story` is present and the user has approved it.

Step values:

- `start`
- `describe`
- `spec`
- `subtasks`
- `execute`
- `review`
- `triage`
- `fix`
- `commit`
- `push`
- `merge`
- `close`
- `done`

## `scope`

| Field | Required | Description |
|-------|----------|-------------|
| `worktree` | Yes | Worktree slug |
| `worktree_path` | Yes | Repo-relative or absolute worktree path |

The command worktree path remains the hard scope source of truth. If an existing context file has a conflicting `scope.worktree_path`, stop and ask before writing.

## `artifacts`

Use paths relative to the worktree root.

| Field | Required | Description |
|-------|----------|-------------|
| `context` | Yes | `current-task/status.json` |
| `spec` | No | `current-task/specs/<slug>.json` |
| `subtasks` | No | `current-task/subtasks/<slug>.md` |
| `review` | No | `current-task/reviews/<slug>.json` |
| `review_validation` | No | Latest `current-task/review-validations/rN-validation.json` |
| `review_input` | No | Latest `current-task/review-inputs/rN-review.json` |
| `next_steps` | No | List of follow-up specs under `current-task/next-steps/` |
| `sync` | No | `current-task/syncs/<slug>.json` |
| `integrate` | No | `current-task/integrates/<slug>.json` |
| `archive` | No | `docs/archive/<slug>/report.json` (worktree / project repo) |

## `open_questions`

Use an empty list when Shinobu can continue safely.

```json
{
  "open_questions": []
}
```

When blocked, keep entries compact and actionable:

```json
{
  "open_questions": [
    {
      "step": "subtasks",
      "question": "Should the CTA link to /contact or /demo?",
      "blocks_next_step": true
    }
  ]
}
```

## `history`

Append one event per workflow result.

| Field | Required | Description |
|-------|----------|-------------|
| `step` | Yes | Step value |
| `status` | Yes | `complete`, `blocked`, `failed`, or `skipped` |
| `artifact` | No | Primary artifact produced |
| `summary` | Yes | One-line result summary |

## JSON example

```json
{
  "meta": {
    "schema": "current-task-context.v1",
    "generated_by": "current-task-update",
    "updated_by": "current-task-update"
  },
  "task": {
    "slug": "hero-section",
    "title": "Hero section redesign",
    "original": "redesign hero section",
    "story": "Feature: Hero section redesign\n\nAs a site visitor\nI want to see a clear headline, subcopy, and call-to-action on the home page\nSo that I understand the product and know what to do next\n\nScenario: Home page hero displays key content\n  Given I am viewing the home page\n  When the page loads above the fold\n  Then I see a prominent headline\n  And I see supporting subcopy beneath the headline\n  And I see a primary call-to-action button\n",
    "type": "feature",
    "current_step": "subtasks",
    "next_step": "execute",
    "last_completed_step": "spec"
  },
  "git": {
    "branch": "feature/hero-section",
    "base": "main"
  },
  "scope": {
    "worktree": "hero-section",
    "worktree_path": "worktrees/hero-section"
  },
  "artifacts": {
    "context": "current-task/status.json",
    "spec": "current-task/specs/hero-section.json",
    "subtasks": "current-task/subtasks/hero-section.md",
    "review": "current-task/reviews/hero-section.json",
    "review_validation": "current-task/review-validations/r1-validation.json",
    "sync": "current-task/syncs/hero-section.json",
    "integrate": "current-task/integrates/hero-section.json"
  },
  "constraints": [
    "no-commit",
    "no-new-deps"
  ],
  "open_questions": [],
  "history": [
    {
      "step": "start",
      "status": "complete",
      "artifact": "current-task/status.json",
      "summary": "Worktree was created and task context initialized."
    },
    {
      "step": "describe",
      "status": "complete",
      "summary": "Gherkin user story captured and approved."
    }
  ]
}
```
