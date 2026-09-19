"""Position freeze rule + write-mode surface (normal / jump only)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.smoke._helpers import run_py, script


def _summary(tmp: Path, name: str, payload: dict) -> Path:
    path = tmp / name
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write(update: Path, root: Path, worktree: Path, summary: Path, *extra: str):
    proc = run_py(
        update, "--worktree", str(worktree), "--json-path", str(summary), *extra, cwd=root
    )
    out = json.loads(proc.stdout.strip()) if proc.stdout.strip() else {}
    return proc, out


def _status(worktree: Path) -> dict:
    return json.loads((worktree / "current-task/status.json").read_text(encoding="utf-8"))


def run(root: Path) -> None:
    update = script(root, "workflow-runtime/skills/current-task-update/scripts/update-status.py")

    # completed_status is deleted: a sheep that could not finish says so with
    # open_questions, and the outcome word is nobody's input.
    if "completed_status" in update.read_text(encoding="utf-8"):
        raise AssertionError("fail: completed_status is back in update-status.py")

    routing = json.loads(
        (root / "workflow-runtime/skills/shinobu/routing.json").read_text(encoding="utf-8")
    )
    contract = routing.get("sheep_return_contract") or {}
    if "completed_status" in json.dumps(contract):
        raise AssertionError("fail: completed_status is back in the sheep return contract")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # Empty open_questions advances by routing; non-empty holds the position
        # at the step that just ran. Both on a fresh worktree with no status yet.
        for name, questions, want_next in (
            ("clear", [], "gherkin"),
            ("held-string", ["CTA link /contact or /demo?"], "spec"),
            ("held-entry", [{"question": "CTA link?", "options": ["/contact", "/demo"]}], "spec"),
        ):
            wt = tmpdir / name
            wt.mkdir()
            s = _summary(wt, "summary.json", {"completed_step": "spec", "open_questions": questions})
            proc, out = _write(update, root, wt, s)
            if proc.returncode != 0 or out.get("written") is not True:
                raise AssertionError(f"fail: {name} should write: {proc.stdout}{proc.stderr}")
            task = _status(wt).get("task") or {}
            if "completed_steps" in task:
                raise AssertionError("fail: status must not write completed_steps")
            if task.get("current_step") != "spec":
                raise AssertionError(f"fail: {name} current_step {task.get('current_step')!r}")
            if task.get("next_step") != want_next:
                raise AssertionError(
                    f"fail: {name} next_step {task.get('next_step')!r} != {want_next!r}"
                )

        # An explicit summary next_step is Shinobu's verdict and outranks the hold.
        wt = tmpdir / "verdict"
        wt.mkdir()
        s = _summary(
            wt,
            "summary.json",
            {
                "completed_step": "review",
                "next_step": "acceptance",
                "open_questions": ["Should the empty state ship in this task?"],
            },
        )
        proc, out = _write(update, root, wt, s)
        if proc.returncode != 0 or out.get("next_step") != "acceptance":
            raise AssertionError(f"fail: explicit next_step must outrank the hold: {out}")

        # The held position is whatever next_step already said, not blindly the
        # completed step: a second blocked write does not walk the task backwards.
        wt = tmpdir / "rehold"
        wt.mkdir()
        seed = _summary(wt, "seed.json", {"completed_step": "execute"})
        proc, out = _write(update, root, wt, seed)
        if proc.returncode != 0 or out.get("next_step") != "review":
            raise AssertionError(f"fail: seed write: {out}{proc.stderr}")
        s = _summary(
            wt,
            "blocked.json",
            {"completed_step": "review", "open_questions": ["Is the flaky test in scope?"]},
        )
        proc, out = _write(update, root, wt, s)
        if proc.returncode != 0 or out.get("next_step") != "review":
            raise AssertionError(f"fail: hold should keep next_step at review: {out}")

        wt = tmpdir / "modes"
        wt.mkdir()
        seed = _summary(
            wt,
            "seed.json",
            {
                "completed_step": "execute",
                "next_step": "review",
            },
        )
        proc, _ = _write(update, root, wt, seed)
        if proc.returncode != 0:
            raise AssertionError(f"fail: seed write: {proc.stderr}")

        # Ad-hoc is a directly-invoked sheep, not a write mode — the CLI must refuse it.
        # Unknown modes go the same way: argparse rejects before anything is written.
        thin = _summary(wt, "thin.json", {"open_questions": []})
        for mode in ("adhoc", "sideways"):
            proc = run_py(
                update,
                "--worktree",
                str(wt),
                "--json-path",
                str(thin),
                "--step",
                "gherkin",
                "--mode",
                mode,
                cwd=root,
            )
            if proc.returncode == 0:
                raise AssertionError(f"fail: --mode {mode} should be rejected")

        if ((_status(wt).get("task")) or {}).get("side_effects"):
            raise AssertionError("fail: rejected modes must not log side effects")

        # With a completed step, next_step comes from routing — summary may omit it.
        s = _summary(wt, "no-next.json", {"completed_step": "spec", "artifact": "current-task/specs/x.json"})
        proc, out = _write(update, root, wt, s)
        if proc.returncode != 0 or out.get("next_step") != "gherkin":
            raise AssertionError(
                f"fail: completed step should derive next_step from routing: {out}"
            )

        # Position-only normal write (no completed step) still requires next_step.
        s = _summary(wt, "pos-only-bad.json", {"open_questions": []})
        proc, out = _write(update, root, wt, s)
        if proc.returncode != 1 or not any(
            "next_step" in e for e in out.get("errors", [])
        ):
            raise AssertionError("fail: position-only write must still require next_step")

    print("smoke-status-vocabulary: ok")
