# Task archive format

`task-archive` writes under `<prefix>/docs/archive/<slug>/`. The caller supplies `prefix` (workspace or nested-project root) and `slug`.

## Outputs

```
<prefix>/docs/archive/<slug>/report.json
<prefix>/docs/archive/<slug>/report.md
<prefix>/docs/archive/<slug>/story.md      # copy from artifacts.story when present
<prefix>/docs/archive/<slug>/errors.json   # verbatim copy when the caller named an errors path
```

The spec path from status is **not** archived — delete from worktree after copy (see [task-archive/SKILL.md](SKILL.md) step 6).

## Load inputs

Caller packs the paths. Task archive: read `current-task/status.json` — [status-format.md](../current-task-update/status-format.md) `artifacts` + `open_questions`; follow pointers; glob only if pointer missing. Source-document archive: read the path the prompt named. No status and no source path → return blocked `open_questions`; do not invent inputs.

**Process sourcing:** build `report.json` `process` in two passes. Do **not** invent history from `completed_steps`.

1. **Handoffs** — for each step with an artifact pointer, load the handoff and take a one-line summary from its `meta` or top-level summary fields.
2. **Side effects** — append one `process` row per `task.side_effects[]` entry (log order). Always include the row, even when `artifact` is null — a null still means the out-of-band run happened. Summary shape: `<mode> <step> at <at> — <artifact|no artifact>`.

| Step | Artifact pointer | Summary source |
|------|------------------|----------------|
| `gherkin` | `artifacts.story` | story exists → brief line from story title or slug |
| `spec` | `artifacts.spec` | `meta.summary` or spec `title` |
| `review` | (none — review writes no file) | verdict as relayed in chat |
| `sync` | (none) | branch pushed |
| `integrate` | (none) | target branch merged |

```json
"process": [
  {"step": "sync", "summary": "Feature branch pushed."},
  {"step": "review", "summary": "jump review at 2026-07-30T12:00:00Z — no artifact"}
]
```

Summarize handoffs — never paste full bodies, logs, diffs, transcripts, secrets.

## report.json

| Field | Req |
|-------|-----|
| `meta` | yes — `task-archive.v1`, `generated_by: task-archive` |
| `task` | yes — slug, title, original, type, branch |
| `story` | yes — keyword line of what shipped |
| `outcome` | yes — `target` and `pushed_branch`; both are facts by archive time |
| `process` | yes — step + one-line summary |
| `decisions` | yes — `[]` OK |
| `open_questions` | yes — `[]` OK |
| `suggestions` | yes — see below |

```json
{
  "meta": {
    "schema": "task-archive.v1",
    "generated_by": "task-archive"
  },
  "task": {
    "slug": "hero-section",
    "title": "Hero section redesign",
    "original": "redesign hero section with headline, subcopy, CTA",
    "type": "feature",
    "branch": "feature/hero-section"
  },
  "story": "headline · subcopy · CTA · responsive layout",
  "outcome": {
    "target": "main",
    "pushed_branch": "feature/hero-section"
  },
  "process": [
    {
      "step": "spec",
      "summary": "Requirements captured."
    },
    {
      "step": "integrate",
      "summary": "Branch merged into main and pushed."
    }
  ],
  "decisions": [],
  "open_questions": [],
  "suggestions": [
    {
      "area": "spec",
      "suggestion": "Put CTA in spec before gherkin.",
      "evidence": "open_questions had CTA during spec."
    }
  ]
}
```

## suggestions

Scan: `open_questions`, blockers, triage, review inputs, push/merge conflicts.

```json
{
  "suggestions": [
    {
      "area": "spec | gherkin | review | push | merge | orchestration",
      "suggestion": "One actionable next-time fix.",
      "evidence": "artifact path or short quote"
    }
  ]
}
```

Top items in `report.md` prose — may highlight 3–5.

## report.md

Terse prose per [caveman/SKILL.md](../caveman/SKILL.md) (lite default). Mirror `report.json`; `story` matches the story keyword line.

Sections:

1. Task — slug, title, branch
2. Story — same keyword line as `report.json`
3. Outcome — target branch and pushed branch
4. Process — short paragraph per step
5. Decisions — omit when none
6. Open questions — omit when empty
7. Suggestions — top items only; omit when none

No raw diffs/logs. Clear prose for irreversible warnings.

## Harness errors reference

When `<prefix>/docs/archive/<slug>/errors.json` was copied from a caller-named path, `report.json` or `report.md` may include a short note that harness errors were recorded and point to the archived errors file — never paste full failure bodies.

## Rules

- Compact — summarize, don't copy `current-task/` tree.
- `report.json` and `report.md` required before second sync (commit/push) and integrate. `story.md` is a copy, never a requirement — see the Outputs list.
- Always write under `<prefix>/docs/archive/<slug>/` — never invent another archive root.
