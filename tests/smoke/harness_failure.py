from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.smoke._helpers import json_line, run_py, script


def run(root: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        _run(root, Path(td) / "wt")


def _run(root: Path, worktree: Path) -> None:
    validate = script(root, "workflow-runtime/skills/shinobu/scripts/validate-harness-stdout.py")
    append = script(root, "workflow-runtime/skills/errors-recording/scripts/append-error.py")
    update = script(root, "workflow-runtime/skills/current-task-update/scripts/update-status.py")
    script_route = "workflow-runtime/skills/shinobu/scripts/bootstrap-context.py"
    (worktree / "current-task/specs").mkdir(parents=True)
    errors_json = worktree / "current-task/specs/errors.json"

    # Synthetic contract-invalid bootstrap stdout (missing required fields).
    bad_stdout = '{"active_task": "t-demo"}'
    val_proc = run_py(
        validate,
        "--script",
        "bootstrap-context.py",
        "--stdout",
        bad_stdout,
        "--exit-code",
        "0",
        cwd=root,
    )
    if val_proc.returncode != 1:
        raise AssertionError("fail: validator should reject contract")

    val_json = json_line(val_proc.stdout)
    if val_json.get("valid") is not False or not val_json.get("errors"):
        raise AssertionError(f"fail: expected contract-invalid, got {val_json}")
    print("contract-invalid:", val_json["errors"])

    # Real update-status input error: valid written:false contract.
    status_path = worktree / "current-task/status.json"
    status_path.write_text(
        json.dumps(
            {
                "meta": {"schema": "task-status.v2"},
                "task": {
                    "slug": "harness-fail",
                    "current_step": "spec",
                    "next_step": "gherkin",
                },
                "scope": {"worktree_path": str(worktree)},
                "artifacts": {},
                "open_questions": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary = worktree / "summary.json"
    summary.write_text("{}\n", encoding="utf-8")
    deny_proc = run_py(
        update,
        "--worktree",
        str(worktree),
        "--json-path",
        str(summary),
        "--mode",
        "normal",
        cwd=root,
    )
    if deny_proc.returncode != 1:
        raise AssertionError("fail: expected update-status input error exit 1")

    deny_val = run_py(
        validate,
        "--script",
        "update-status.py",
        "--stdout",
        deny_proc.stdout.strip(),
        "--exit-code",
        str(deny_proc.returncode),
        cwd=root,
    )
    deny_json = json_line(deny_val.stdout)
    if deny_json.get("valid") is not True:
        raise AssertionError(f"fail: written:false should have valid contract, got {deny_json}")
    print("update-status-input-error-valid-contract: ok")

    input_json = json.dumps(
        {
            "argv": [
                "--worktree",
                "worktrees/shinobu-sheep-fallback",
            ]
        }
    )
    validation_json = json.dumps(val_json["errors"])

    append_proc = run_py(
        append,
        "--worktree",
        str(worktree),
        "--script-route",
        script_route,
        "--input",
        input_json,
        "--expected-output",
        '{"required_fields":["active_task","status_path","current_step","next_step","sheep"]}',
        "--exit-code",
        "0",
        "--stdout",
        bad_stdout,
        "--validation-errors",
        validation_json,
        cwd=root,
    )
    if append_proc.returncode != 0:
        raise AssertionError(f"fail: append-error failed: {append_proc.stderr}")

    if not errors_json.is_file():
        raise AssertionError("fail: errors.json not created")

    data = json.loads(errors_json.read_text(encoding="utf-8"))
    assert data["meta"]["schema"] == "errors.v1"
    assert len(data["failures"]) >= 1
    last = data["failures"][-1]
    assert last["script_route"] == script_route
    assert "missing field" in " ".join(last["actual"]["validation_errors"] or [])
    print("errors.json harness entry: ok")
    print("smoke-harness-failure: ok")
