# global-status.json format

Workspace-root task registry. **JSON only.** Source of truth for which tasks exist and where per-task status lives.

**Write boundary:** register on start; unregister on close. Readers use [global-status-read.md](global-status-read.md).

Default path: `global-status.json` at Shinobu workspace root (repo root in single-repo mode).

## Top-level fields

| Field | Required | Description |
|-------|----------|-------------|
| `version` | Yes | Schema version; use `1` |
| `active_task` | No | Task id Shinobu or hook should prefer when user did not specify id |
| `tasks` | Yes | Map of task id → registry entry |

## Task registry entry

Each key in `tasks` is a stable string id scoped per project: `<project>:<id>` (e.g. `shinobu:3`, `tetris-clone-frp:1`). Task ids auto-increment per project.

| Field | Required | Description |
|-------|----------|-------------|
| `project` | Yes | Managed project name (e.g. `castlemill-landing`) |
| `slug` | Yes | Worktree folder slug (e.g. `hero-section`) |
| `worktree_path` | Yes | Repo-relative path to task worktree (e.g. `worktrees/shinobu-hero-section`) |
| `status_path` | Yes | Repo-relative path to per-task `status.json` |

## Example

```json
{
  "version": 1,
  "active_task": "castlemill-landing:1",
  "tasks": {
    "castlemill-landing:1": {
      "project": "castlemill-landing",
      "slug": "hero-section",
      "worktree_path": "worktrees/castlemill-landing-hero-section",
      "status_path": "worktrees/castlemill-landing-hero-section/current-task/status.json"
    }
  }
}
```

## Resolved defaults (status-architecture task)

| Decision | Choice |
|----------|--------|
| Task id | Per-project numeric string; registry key `<project>:<id>` |
| `active_task` | Present when multiple tasks may be open |
| Registry filename | `global-status.json` (not root `status.json`) |
| Close unregister | Remove entry after archive; clear or re-point `active_task` |

## Hook resolution

```bash
jq -r --arg id "42" '.tasks[$id].status_path' global-status.json
```
