"""bootstrap-context.py: position contract without readiness."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from tests.smoke._helpers import json_line, run_py, script

SLUG = "bootstrap-soft"


def _put(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def _fixture(base: Path) -> tuple[Path, Path]:
    workspace = base / "workspace"
    worktree = workspace / "worktrees" / SLUG
    worktree.mkdir(parents=True)
    status_rel = "current-task/status.json"
    _put(
        worktree / status_rel,
        {
            "meta": {"schema": "task-status.v2"},
            "task": {
                "slug": SLUG,
                "original": "demo",
                "current_step": "review",
                "next_step": "acceptance",
            },
            "scope": {"worktree_path": str(worktree)},
            "artifacts": {},
            "open_questions": [],
        },
    )
    _put(
        workspace / "global-status.json",
        {
            "active_task": f"t-{SLUG}",
            "tasks": {
                f"t-{SLUG}": {
                    "worktree_path": str(worktree),
                    "status_path": status_rel,
                }
            },
        },
    )
    _put(workspace / "shinobu-workspace.example.yaml", {"name": "test"})
    return workspace, worktree


def run(root: Path) -> None:
    validate = script(root, "workflow-runtime/skills/shinobu/scripts/validate-harness-stdout.py")
    required = ("active_task", "status_path", "current_step", "next_step", "sheep")

    with tempfile.TemporaryDirectory() as td:
        workspace, worktree = _fixture(Path(td))
        boot = script(root, "workflow-runtime/skills/shinobu/scripts/bootstrap-context.py")
        proc = run_py(
            boot,
            "--worktree",
            str(worktree),
            env={**os.environ, "SHINOBU_WORKSPACE_ROOT": str(workspace)},
            cwd=workspace,
        )
        if proc.returncode != 0:
            raise AssertionError(f"fail: bootstrap exit {proc.returncode}: {proc.stderr}")
        out = json_line(proc.stdout)
        for key in required:
            if key not in out:
                raise AssertionError(f"fail: missing {key} in {out}")
        if "readiness" in out:
            raise AssertionError("fail: bootstrap must not emit readiness")
        if out.get("next_step") != "acceptance" or out.get("sheep") is not None:
            raise AssertionError(f"fail: unexpected bootstrap payload: {out}")

        v = run_py(
            validate,
            "--script",
            "bootstrap-context.py",
            "--stdout",
            json.dumps(out),
            cwd=root,
        )
        if v.returncode != 0:
            raise AssertionError(f"fail: validate harness: {v.stdout}{v.stderr}")

    print("smoke-bootstrap-contract: ok")
