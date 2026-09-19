from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.smoke._helpers import run_py, script


def run(root: Path) -> None:
    update = script(root, "workflow-runtime/skills/current-task-update/scripts/update-status.py")
    validate = script(root, "workflow-runtime/skills/shinobu/scripts/validate-harness-stdout.py")

    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp)

        json_ok = fixture / "summary-ok.json"
        json_ok.write_text(
            json.dumps(
                {
                    "completed_step": "spec",
                    "next_step": "subtasks",
                    "artifact": "current-task/specs/foo.json",
                    "open_questions": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        proc = run_py(
            update, "--worktree", str(fixture), "--json-path", str(json_ok), cwd=root
        )
        if proc.returncode != 0:
            raise AssertionError(f"fail: valid summary: {proc.stderr}")
        out = json.loads(proc.stdout.strip())
        if out.get("written") is not True:
            raise AssertionError("fail: expected written true")
        if out.get("completed_step") != "spec" or out.get("next_step") != "subtasks":
            raise AssertionError("fail: unexpected step fields")

        val = run_py(
            validate,
            "--script",
            "update-status.py",
            "--stdout",
            proc.stdout.strip(),
            "--exit-code",
            "0",
            cwd=root,
        )
        if val.returncode != 0:
            raise AssertionError("fail: harness contract validation")

        status_path = fixture / "current-task/status.json"
        if not status_path.is_file():
            raise AssertionError("fail: status.json not written")

        json_acc = fixture / "summary-acc.json"
        json_acc.write_text(
            json.dumps({"completed_step": "acceptance", "next_step": "sync"}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        proc_acc = run_py(
            update, "--worktree", str(fixture), "--json-path", str(json_acc), cwd=root
        )
        if proc_acc.returncode != 0:
            raise AssertionError(f"fail: acceptance without artifact: {proc_acc.stderr}")
        if json.loads(proc_acc.stdout.strip()).get("written") is not True:
            raise AssertionError("fail: acceptance should write")

        # next_step-only on a fresh worktree: always write current_step ("start")
        fresh = fixture / "fresh-next-only"
        fresh.mkdir()
        json_next = fresh / "summary-next-only.json"
        json_next.write_text(
            json.dumps({"next_step": "spec"}, indent=2) + "\n", encoding="utf-8"
        )
        proc_next = run_py(
            update, "--worktree", str(fresh), "--json-path", str(json_next), cwd=root
        )
        if proc_next.returncode != 0:
            raise AssertionError(f"fail: next_step only: {proc_next.stderr}")
        out_next = json.loads(proc_next.stdout.strip())
        if out_next.get("written") is not True:
            raise AssertionError("fail: next_step only should write")
        if out_next.get("next_step") != "spec":
            raise AssertionError("fail: next_step only should update next_step")
        if out_next.get("completed_step") is not None:
            raise AssertionError("fail: next_step only completed_step should be null")
        status_next = json.loads(
            (fresh / "current-task/status.json").read_text(encoding="utf-8")
        )
        task_next = status_next.get("task") or {}
        if task_next.get("next_step") != "spec":
            raise AssertionError("fail: status next_step not updated")
        if task_next.get("current_step") != "start":
            raise AssertionError("fail: fresh next_step-only current_step should be start")
        if "completed_steps" in task_next:
            raise AssertionError("fail: status must not write completed_steps")

        status_before = status_path.read_text(encoding="utf-8")

        json_bad = fixture / "summary-bad.json"
        # Missing required next_step (optional fields alone must not write)
        json_bad.write_text(
            json.dumps({"open_questions": []}, indent=2) + "\n", encoding="utf-8"
        )
        proc_bad = run_py(
            update, "--worktree", str(fixture), "--json-path", str(json_bad), cwd=root
        )
        if proc_bad.returncode != 1:
            raise AssertionError("fail: expected exit 1 for missing next_step")
        bad = json.loads(proc_bad.stdout.strip())
        if bad.get("written") is not False:
            raise AssertionError("fail: expected written false")
        errors = bad.get("errors", [])
        if not any("next_step" in e for e in errors):
            raise AssertionError("fail: error should name next_step")
        if any("completed_step" in e for e in errors):
            raise AssertionError("fail: bad case errors must name next_step only")
        if status_path.read_text(encoding="utf-8") != status_before:
            raise AssertionError("fail: status.json changed on input error")

    print("smoke-status-update: ok")
