"""--mode jump: position-only (next_step = target; current_step untouched)."""

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


def _put(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(root: Path) -> None:
    update = script(root, "workflow-runtime/skills/current-task-update/scripts/update-status.py")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        wt = tmpdir / "to-spec"
        wt.mkdir()
        _put(wt / "current-task/story.md", "# Story\n")
        seed = _summary(
            wt,
            "seed.json",
            {
                "completed_step": "gherkin",
                "artifact": "current-task/story.md",
                "task": {"original": "demo", "slug": "demo"},
            },
        )
        proc, _ = _write(update, root, wt, seed, "--step", "gherkin")
        if proc.returncode != 0:
            raise AssertionError(f"fail: seed: {proc.stdout}{proc.stderr}")

        before = _status(wt)
        before_current = (before.get("task") or {}).get("current_step")
        before_arts = dict(before.get("artifacts") or {})
        before_tree = {
            p.relative_to(wt).as_posix()
            for p in (wt / "current-task").rglob("*")
            if p.is_file()
        }

        # Jump back to spec (the spec was wrong): no summary artifact, jump still
        # succeeds, next_step is the target rather than routing's review, and
        # current_step is unchanged.
        jump = _summary(wt, "jump.json", {"open_questions": []})
        proc, out = _write(update, root, wt, jump, "--step", "spec", "--mode", "jump")
        if proc.returncode != 0 or out.get("written") is not True:
            raise AssertionError(f"fail: jump write: {proc.stdout}{proc.stderr}")
        if out.get("next_step") != "spec":
            raise AssertionError(f"fail: jump should set next_step to target: {out}")

        after = _status(wt)
        if (after.get("task") or {}).get("current_step") != before_current:
            raise AssertionError(
                f"fail: current_step must be byte-identical "
                f"({before_current!r} → {(after.get('task') or {}).get('current_step')!r})"
            )
        if (after.get("task") or {}).get("next_step") != "spec":
            raise AssertionError(f"fail: next_step should be spec: {after.get('task')}")
        if dict(after.get("artifacts") or {}) != before_arts:
            raise AssertionError("fail: jump must not register artifact pointers")

        after_tree = {
            p.relative_to(wt).as_posix()
            for p in (wt / "current-task").rglob("*")
            if p.is_file() and p.name != "status.json"
        }
        materialize_hits = [
            p
            for p in after_tree
            if (p.startswith("current-task/specs/") or p.startswith("current-task/executions/"))
            and p not in before_tree
        ]
        if materialize_hits:
            raise AssertionError(f"fail: jump must not copy files into current-task/: {materialize_hits}")

        effects = (after.get("task") or {}).get("side_effects") or []
        if not effects or effects[-1].get("mode") != "jump" or effects[-1].get("artifact") is not None:
            raise AssertionError(f"fail: jump side_effect should log artifact null: {effects}")

        # Jump to close still rejected.
        proc, out = _write(update, root, wt, jump, "--step", "close", "--mode", "jump")
        if proc.returncode != 1:
            raise AssertionError(f"fail: jump close should be rejected: {out}")

        # Operational normal write (review) with omitted artifact registers no
        # pointer and materializes no handoff file under current-task/.
        wt2 = tmpdir / "no-handoff"
        wt2.mkdir()
        seed2 = _summary(
            wt2,
            "seed.json",
            {
                "completed_step": "gherkin",
                "artifact": "current-task/story.md",
                "task": {"slug": "x", "original": "x"},
            },
        )
        _put(wt2 / "current-task/story.md", "- [ ] a\n")
        proc, _ = _write(update, root, wt2, seed2, "--step", "gherkin")
        if proc.returncode != 0:
            raise AssertionError(f"fail: seed2: {proc.stdout}{proc.stderr}")
        arts_before = dict(_status(wt2).get("artifacts") or {})
        tree_before = {p.relative_to(wt2).as_posix() for p in (wt2 / "current-task").rglob("*") if p.is_file()}
        rev = _summary(wt2, "review.json", {"open_questions": []})
        proc, out = _write(update, root, wt2, rev, "--step", "review")
        if proc.returncode != 0 or out.get("written") is not True:
            raise AssertionError(f"fail: review omit artifact: {proc.stdout}{proc.stderr}")
        if dict(_status(wt2).get("artifacts") or {}) != arts_before:
            raise AssertionError("fail: review must not set any artifact pointer")
        tree_after = {p.relative_to(wt2).as_posix() for p in (wt2 / "current-task").rglob("*") if p.is_file()}
        if tree_after != tree_before:
            raise AssertionError(f"fail: review must not create handoff files: {tree_after - tree_before}")

    print("smoke-jump-mode: ok")
