# errors.json format (errors.v1)

Path: `current-task/specs/errors.json` under the active worktree.

Append-only diagnostic artifact — separate from task requirements spec and subtasks.

## Top-level

| Field | Required | Description |
|-------|----------|-------------|
| `meta` | Yes | `schema: errors.v1`, `worktree` slug |
| `failures` | Yes | Ordered list of failure entries |

## Failure entry

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique string; default ISO8601 UTC; numeric suffix on collision within same second |
| `recorded_at` | Yes | ISO8601 UTC timestamp |
| `script_route` | Yes | Failed harness script route from Shinobu |
| `input` | Yes | Structured invocation payload (args, stdin, or JSON) |
| `expected_output` | Yes | Contract description or required field list |
| `actual` | Yes | Object with `exit_code`, `stdout`, `stderr`, `validation_errors` (each nullable) |

## Append semantics

- Read existing file when present; append exactly one entry; write back.
- When absent, create with `meta` and a single-entry `failures` list.
- Never replace wholesale or delete prior entries.

## Example

```json
{
  "meta": {
    "schema": "errors.v1",
    "worktree": "sheep-fallback"
  },
  "failures": [
    {
      "id": "2026-07-02T15:30:00Z",
      "recorded_at": "2026-07-02T15:30:00Z",
      "script_route": "workflow-runtime/skills/shinobu/scripts/bootstrap-context.py",
      "input": {
        "argv": [
          "--worktree",
          "worktrees/shinobu-sheep-fallback",
          "--step",
          "execute"
        ]
      },
      "expected_output": {
        "required_fields": [
          "allowed",
          "sheep",
          "reason"
        ]
      },
      "actual": {
        "exit_code": 1,
        "stdout": "{\"allowed\": false}",
        "stderr": null,
        "validation_errors": [
          "missing field: reason"
        ]
      }
    }
  ]
}
```
