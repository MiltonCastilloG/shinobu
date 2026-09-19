# Shinobu skills

Skills are **pure functionality** — portable operation manuals with no knowledge of the Shinobu pipeline.

| Layer | Owns | Who uses it |
|-------|------|-------------|
| **Skill** (`SKILL.md` + `*-format.md`) | How to perform one job: algorithms, schemas, safety, default output shape | Attach to do the job in your own context |
| **Sheep** (`workflow-runtime/agents/sheep-*.md`) | Workflow binding: run one skill in isolated context, return JSON | Shinobu on the pipeline; direct Task spawn for ad-hoc |
| **Shinobu** (`workflow-runtime/agents/shinobu.md`) | Full pipeline, transitions, user confirmations | User says `shinobu …` |

Pipeline leaf skills: `story-maker`, `spec-maker`, `review-execution`, …

## Invocation policy

1. **Ad-hoc work** — Task-spawn the sheep directly (instructions + output path, default `docs/adhoc/`), or attach the skill when you want the work in your own context. No task or status write either way.
2. **Shinobu-only sheep** — `sheep-start`, `sheep-close`, `sheep-status` own the registry and per-task status; never spawn them ad-hoc.
3. **Shinobu sends sheep** — full current-task workflow goes through Shinobu (`shinobu fetch`, `shinobu continue`, …).
4. **Workflow-only skills stay internal** — `current-task-update`, `close-task`, `close-scope`, `task-archive`, `hook-contract` keep `disable-model-invocation: true`.

## Rules

1. Leaf skills do **not** reference `status.json`, `global-status.json`, pipeline step names, or “send sheep next”.
2. Leaf skills accept **inputs from the sheep prompt** (paths, inline JSON, story text) — no implicit disk discovery.
3. Format files document **one artifact type** each — no multi-agent directory maps.
4. Sheep load skills and pass concrete inputs; sheep own auto-load paths and caller summary expectations.

## Exceptions (workflow skills)

These skills intentionally own task/workflow state or lifecycle:

- `current-task-update/` — per-task `status.json`
- `start-task/` — worktree creation; `register-global-status.sh` on register
- `close-task/`, `close-scope/`, `task-archive/` — archive, unregister, teardown
- `hook-contract/` — resolve task id → status for hooks

## Shared utilities

- `caveman/` — markdown voice (not workflow)
- `conflict-resolution/` — merge conflict protocol for sync and integrate
