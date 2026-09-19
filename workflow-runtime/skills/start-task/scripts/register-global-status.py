#!/usr/bin/env python3
"""Register a task in global-status.json with per-project task id auto-increment.

Usage:
  register-global-status.py <workspace_root> <project> <slug> <worktree_path> [task_id]

When task_id is omitted, assigns the next incremental id for that project.
Registry keys use format <project>:<id> (e.g. shinobu:3, tetris-clone-frp:1).

Stdout: human line plus JSON handoff on last line.
Only sheep-start should invoke this script (registry write boundary).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_global(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"version": 1, "tasks": {}}


def next_task_id(data: dict[str, Any], project: str) -> str:
    tasks = data.get("tasks") or {}
    max_id = 0
    for key, entry in tasks.items():
        entry_project = (entry or {}).get("project")
        if entry_project != project:
            continue
        raw_id = key.split(":", 1)[-1] if ":" in key else key
        try:
            max_id = max(max_id, int(raw_id))
        except ValueError:
            continue
    return str(max_id + 1)


def registry_key(project: str, task_id: str) -> str:
    return f"{project}:{task_id}"


def register(
    workspace: Path,
    project: str,
    slug: str,
    worktree_path: str,
    task_id: str | None,
) -> dict[str, str]:
    global_path = workspace / "global-status.json"
    data = load_global(global_path)
    tasks = data.setdefault("tasks", {})

    if task_id is None:
        task_id = next_task_id(data, project)

    key = registry_key(project, task_id)
    status_path = f"{worktree_path}/current-task/status.json"

    if key in tasks:
        print(f"skip: task {key} already registered")
        handoff = {
            "status": "skipped",
            "registry_key": key,
            "task_id": task_id,
            "status_path": status_path,
        }
        print(json.dumps(handoff))
        return handoff

    tasks[key] = {
        "project": project,
        "slug": slug,
        "worktree_path": worktree_path,
        "status_path": status_path,
    }
    data["active_task"] = key
    data["version"] = 1

    global_path.parent.mkdir(parents=True, exist_ok=True)
    global_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"registered: task {key} -> {status_path}")
    handoff = {
        "status": "registered",
        "registry_key": key,
        "task_id": task_id,
        "status_path": status_path,
        "worktree_path": worktree_path,
    }
    print(json.dumps(handoff))
    return handoff


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "Usage: register-global-status.py "
            "<workspace_root> <project> <slug> <worktree_path> [task_id]",
            file=sys.stderr,
        )
        return 1
    workspace = Path(sys.argv[1]).resolve()
    project = sys.argv[2]
    slug = sys.argv[3]
    worktree_path = sys.argv[4]
    task_id = sys.argv[5] if len(sys.argv) > 5 else None
    register(workspace, project, slug, worktree_path, task_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
