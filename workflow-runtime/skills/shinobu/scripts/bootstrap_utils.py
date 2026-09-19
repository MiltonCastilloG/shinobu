"""Shared helpers for Shinobu bootstrap / harness read path."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROUTING_PATH = SCRIPT_DIR.parent / "routing.json"


def workspace_root() -> Path:
    override = os.environ.get("SHINOBU_WORKSPACE_ROOT")
    if override:
        return Path(override).resolve()
    p = SCRIPT_DIR
    for _ in range(12):
        git = p / ".git"
        if git.is_file():
            gitdir = Path(git.read_text(encoding="utf-8").split(":", 1)[1].strip())
            if "/worktrees/" in gitdir.as_posix():
                return gitdir.parent.parent.parent
        if (p / "worktrees").is_dir() and (p / "shinobu-workspace.example.yaml").exists():
            return p
        p = p.parent
    return SCRIPT_DIR.parent.parent.parent.parent


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_routing() -> dict[str, Any]:
    if not ROUTING_PATH.is_file():
        raise FileNotFoundError(f"routing missing: {ROUTING_PATH}")
    return load_json(ROUTING_PATH)


def resolve_worktree(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    return (workspace_root() / p).resolve()


def load_status(worktree: Path) -> dict[str, Any]:
    status_path = worktree / "current-task/status.json"
    if not status_path.is_file():
        raise FileNotFoundError("status.json missing in worktree")
    return json.loads(status_path.read_text(encoding="utf-8"))
