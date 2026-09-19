---
name: task-archive
description: "Write <prefix>/docs/archive/<slug>/ (report.json, report.md, story.md); erase current-task spec."
disable-model-invocation: true
---

# Task Archive

Draft + write archive. Format: [archive-format.md](archive-format.md).

## Inputs

Caller-owned paths. You do not resolve a worktree via close-scope.

| Input | Req |
|-------|-----|
| `prefix` | yes — repo or project root that contains `docs/archive/` (workspace root or nested project) |
| `slug` | yes |
| `current-task/status.json` (and its artifact pointers) | when archiving a task |
| `source_document` | when archiving from a named document instead of a task |
| errors file path | optional — copy into the archive when the caller names one |

`archive_dir` is always `<prefix>/docs/archive/<slug>/`. Write only there.

## Steps

1. Resolve `archive_dir` = `<prefix>/docs/archive/<slug>/` from the prompt. Create it if needed.
2. Load inputs — task: handoffs via status `artifacts` and `task.side_effects` ([status-format.md](../current-task-update/status-format.md)). Source document: the path the prompt named.
3. Draft `report.json` — task, story, outcome, process (handoff rows, then one row per `side_effects` entry including null artifacts — see archive-format), decisions, open_questions, suggestions.
4. Draft `report.md` — terse per caveman; mirror report.json.
5. Write `report.json` and `report.md` under `archive_dir`.
6. Copy `artifacts.story` → `<archive_dir>/story.md` when present; when the caller named an errors file and it exists, copy it verbatim → `<archive_dir>/errors.json`; delete `artifacts.spec` from the worktree when present (cleanup — that pointed path only).
7. When archived `errors.json` exists, note harness errors were recorded in `report.json` / `report.md` and reference `<archive_dir>/errors.json` — do not paste full failure bodies.

(On the pipeline, commit and push via the next sync step.)
