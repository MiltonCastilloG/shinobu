---
name: hook-contract
description: "Hook contract for resolving Shinobu task state from global-status.json and per-task status.json by task id. Use when writing Cursor hooks after Shinobu knows task number."
disable-model-invocation: true
---

# Hook contract — task status resolution

Hooks run after Shinobu knows **task id**. Resolve state with **JSON only** — no YAML parser.

## Resolution chain

```
task id → global-status.json → status_path → status.json → artifact paths
```

## Steps

1. Read `global-status.json` at workspace root.
2. Lookup `.tasks[<task_id>]`.
3. Read fields: `project`, `slug`, `worktree_path`, `status_path`.
4. Read per-task `status.json` at `status_path`.
5. Read `task.current_step`, `task.next_step`, `artifacts`, `open_questions`.

## jq examples

Registry route:

```bash
jq -r --arg id "$TASK_ID" '.tasks[$id].status_path' global-status.json
```

Full summary:

```bash
TASK_ID="42"
STATUS_PATH=$(jq -r --arg id "$TASK_ID" '.tasks[$id].status_path' global-status.json)
jq -r '.task | "\(.current_step) -> \(.next_step)"' "$STATUS_PATH"
```

Project + worktree:

```bash
jq -r --arg id "$TASK_ID" '.tasks[$id] | "\(.project) \(.worktree_path)"' global-status.json
```

## Rules

- Hooks **read only** — never write `global-status.json` during sheep steps.
- Task id must be explicit; do not infer from chat.
- Workflow position: `task.next_step` (document `artifacts.*` when present).

## Agent tool permissions

| File | Role |
|------|------|
| `.cursor/hooks/agent-permissions.json` | Canonical allowlist per agent |
| `.cursor/hooks/enforce-agent-tools.sh` | `preToolUse` hook — reads permissions, denies disallowed tools |
| `.cursor/hooks.json` | Registers the `preToolUse` hook |

Agent identity from `subagent_type` then `agent_type` only — **not** task/description text (avoids false match on words like `shinobu` in prompts). Unknown agent or unmapped tool → allow. Known agent + `false` permission → deny.

Smoke test: `python3 test.py` (includes agent-tools smoke)
