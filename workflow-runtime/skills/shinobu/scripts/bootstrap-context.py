#!/usr/bin/env python3
"""Emit Shinobu bootstrap orchestration context on stdout.

Usage:
  bootstrap-context.py --worktree worktrees/shinobu-my-task

Stdout JSON: active_task, status_path, current_step, next_step, sheep
Exit 0 on success. Registry / status failures exit 1 with stderr and empty stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from bootstrap_utils import load_routing, load_status, resolve_worktree, workspace_root


def load_global() -> dict[str, Any]:
    path = workspace_root() / "global-status.json"
    if not path.is_file():
        raise FileNotFoundError("global-status.json missing")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"global-status.json malformed: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("global-status.json must be an object")
    return data


def find_task(global_data: dict[str, Any], worktree: Path) -> tuple[str | None, dict[str, Any] | None]:
    for tid, entry in (global_data.get("tasks") or {}).items():
        if isinstance(entry, dict) and resolve_worktree(entry.get("worktree_path", "")) == worktree:
            return tid, entry
    return None, None


def bootstrap(worktree_arg: str) -> dict[str, Any]:
    worktree = resolve_worktree(worktree_arg)
    global_data = load_global()
    task_id, entry = find_task(global_data, worktree)
    if not entry:
        raise ValueError(f"no registry entry for worktree {worktree_arg}")

    status_path = entry.get("status_path")
    if not status_path:
        raise ValueError("status_path unresolvable")

    status = load_status(worktree)
    scope_wt = (status.get("scope") or {}).get("worktree_path")
    if not scope_wt or resolve_worktree(scope_wt) != worktree:
        raise ValueError(f"--worktree {worktree_arg!r} does not match scope.worktree_path")

    task = status.get("task") or {}
    next_step = task.get("next_step")
    if not next_step:
        raise ValueError("task.next_step missing")

    active_task = task_id
    if not active_task:
        at = global_data.get("active_task")
        ae = (global_data.get("tasks") or {}).get(at or "")
        if isinstance(ae, dict) and resolve_worktree(ae.get("worktree_path", "")) == worktree:
            active_task = at

    step_cfg = (load_routing().get("steps") or {}).get(next_step) or {}

    return {
        "active_task": active_task,
        "status_path": status_path,
        "current_step": task.get("current_step"),
        "next_step": next_step,
        "sheep": step_cfg.get("sheep"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Shinobu bootstrap context.")
    parser.add_argument("--worktree", required=True, help="Task worktree path")
    args = parser.parse_args()
    try:
        print(json.dumps(bootstrap(args.worktree)))
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
