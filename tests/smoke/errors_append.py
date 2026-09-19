"""append-error.py creates errors.json and appends distinct entries."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.smoke._helpers import run_py, script

ENTRY_KEYS = ("id", "recorded_at", "script_route", "input", "expected_output", "actual")
ACTUAL_KEYS = ("exit_code", "stdout", "stderr", "validation_errors")


def _append(append: Path, root: Path, worktree: Path, *, route: str, stdout: str, errors: str) -> None:
    proc = run_py(
        append,
        "--worktree",
        str(worktree),
        "--script-route",
        route,
        "--input",
        '{"argv":["--worktree","worktrees/demo","--step","review"]}',
        "--expected-output",
        '{"required_fields":["active_task","status_path","current_step","next_step","sheep"]}',
        "--exit-code",
        "1",
        "--stdout",
        stdout,
        "--validation-errors",
        errors,
        cwd=root,
    )
    if proc.returncode != 0:
        raise AssertionError(f"fail: append-error exited {proc.returncode}: {proc.stderr}")


def run(root: Path) -> None:
    append = script(root, "workflow-runtime/skills/errors-recording/scripts/append-error.py")

    with tempfile.TemporaryDirectory() as td:
        worktree = Path(td) / "wt"
        (worktree / "current-task/specs").mkdir(parents=True)
        errors = worktree / "current-task/specs/errors.json"

        _append(
            append,
            root,
            worktree,
            route="workflow-runtime/skills/shinobu/scripts/bootstrap-context.py",
            stdout='{"active_task":"t-demo"}',
            errors='["missing field: next_step"]',
        )
        if not errors.is_file():
            raise AssertionError("fail: errors.json missing after first append")

        data = json.loads(errors.read_text(encoding="utf-8"))
        if data.get("meta", {}).get("schema") != "errors.v1":
            raise AssertionError(f"fail: expected errors.v1 schema, got {data.get('meta')}")
        if len(data["failures"]) != 1:
            raise AssertionError(f"fail: expected one entry, got {len(data['failures'])}")

        entry = data["failures"][0]
        missing = [k for k in ENTRY_KEYS if k not in entry]
        missing += [f"actual.{k}" for k in ACTUAL_KEYS if k not in entry.get("actual", {})]
        if missing:
            raise AssertionError(f"fail: entry missing keys: {missing}")
        print("ok: first append writes a complete errors.v1 entry")

        _append(
            append,
            root,
            worktree,
            route="workflow-runtime/skills/current-task-update/scripts/update-status.py",
            stdout="not json",
            errors='["stdout is not valid JSON"]',
        )
        data = json.loads(errors.read_text(encoding="utf-8"))
        if len(data["failures"]) != 2:
            raise AssertionError(f"fail: expected two entries, got {len(data['failures'])}")
        if len({f["id"] for f in data["failures"]}) != 2:
            raise AssertionError("fail: entries should have distinct ids")
        routes = [f["script_route"] for f in data["failures"]]
        if routes[0] == routes[1]:
            raise AssertionError("fail: second append should record its own script route")
        print("ok: second append preserves the first and records a distinct entry")

    print("smoke-errors-append: ok")
