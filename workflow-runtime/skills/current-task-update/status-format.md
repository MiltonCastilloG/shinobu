# Per-task status.json format

Per-task workflow state inside the active worktree. **JSON only.**

Path: `current-task/status.json` relative to task worktree root.

**Write boundary:** only `current-task-update`. Readers use [status-read.md](status-read.md).

Document bodies live as separate files; status holds **position**, document **pointers**, and **open_questions**. Operational steps (review / sync / integrate / close) do not use handoff files or status blobs — `task.next_step` is enough.

## Top-level fields

| Field | Required | Description |
|-------|----------|-------------|
| `meta` | Yes | Schema identifier only |
| `task` | Yes | Identity and step pointers |
| `scope` | Yes | Worktree path |
| `artifacts` | Yes | Paths to **document** files |
| `open_questions` | Yes | Blockers; empty array when unblocked |

## `meta`

| Field | Required | Description |
|-------|----------|-------------|
| `schema` | Yes | `task-status.v2` |

## `task`

| Field | Required | Description |
|-------|----------|-------------|
| `id` | No | Task id from global registry when known |
| `slug` | Yes | Worktree folder slug |
| `project` | No | Managed project name |
| `title` | No | Short title |
| `original` | Yes | Short slug or one-line title after gherkin; start slug until then |
| `type` | No | `feature`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf` |
| `current_step` | Yes | Step Shinobu is on or just completed |
| `next_step` | Yes | Next step Shinobu should propose — **workflow source of truth** |
| `side_effects` | No | Append-only log of jump runs |

Step values: `start`, `spec`, `gherkin`, `review`, `acceptance`, `sync`, `archive`, `integrate`, `close`, `done`.

Do **not** persist `completed_step` / `completed_steps` — consumers use `next_step`.

### `side_effects`

Jump sets `next_step` to the target, leaves `current_step`, logs `artifact: null`. Entries with `"mode": "adhoc"` appear in older files — ad-hoc is now a sheep invoked directly and writes nothing here.

```json
"side_effects": [
  {"step": "review", "mode": "jump", "at": "2026-07-30T12:00:00Z", "artifact": null}
]
```

## `scope`

| Field | Required | Description |
|-------|----------|-------------|
| `worktree_path` | Yes | Repo-relative or absolute worktree path |

## `artifacts`

Worktree-relative pointers to **document** outputs only. Gates resolve `worktree / artifacts.<key>`.

| Field | Required | Description |
|-------|----------|-------------|
| `story` | No | `current-task/story.md` |
| `spec` | No | Spec JSON path |
| `archive` | No | `docs/archive/<slug>/report.json` |

No `sync` / `integrate` / `review_validation` / `review_input` pointers.

## `open_questions`

Empty when Shinobu can continue. **Non-empty holds `next_step` where it was** — that is the whole blocked mechanism; there is no status field for it.

A sheep cannot reach a human, so this is also how it asks. One entry per question. `question` is the only required key; `options` lets the caller offer a choice instead of an essay prompt, and `context` says what the sheep found that raised it. No schema, no validator — the reader is an LLM.

```json
"open_questions": [
  {
    "step": "spec",
    "question": "Where should the hero CTA link?",
    "options": ["/contact", "/demo"],
    "context": "The spec names a CTA but no destination; both routes exist."
  }
]
```

A plain string is accepted too, for questions that need no options.

## Acceptance / review outcomes

Shinobu sets `next_step` from chat and the sheep summary (e.g. after review → `acceptance`, or `gherkin` / `spec` when changes are needed). No readiness file on disk.

## Example

```json
{
  "meta": { "schema": "task-status.v2" },
  "task": {
    "id": "42",
    "slug": "hero-section",
    "project": "castlemill-landing",
    "original": "hero-section",
    "type": "feature",
    "current_step": "gherkin",
    "next_step": "review"
  },
  "scope": {
    "worktree_path": "worktrees/castlemill-landing-hero-section"
  },
  "artifacts": {
    "story": "current-task/story.md",
    "spec": "current-task/specs/hero-section.json"
  },
  "open_questions": []
}
```
