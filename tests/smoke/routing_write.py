"""Write path derives next_step and document artifact keys from routing."""

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
    routing = json.loads(
        (root / "workflow-runtime/skills/shinobu/routing.json").read_text(encoding="utf-8")
    )
    steps = routing.get("steps") or {}

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        wt = tmpdir / "from-step"
        wt.mkdir()
        s = _summary(
            wt,
            "summary.json",
            {"artifact": "current-task/specs/foo.json"},
        )
        proc, out = _write(update, root, wt, s, "--step", "spec")
        if proc.returncode != 0 or out.get("written") is not True:
            raise AssertionError(f"fail: --step write: {proc.stdout}{proc.stderr}")
        if out.get("next_step") != steps["spec"]["default_next_step"]:
            raise AssertionError(f"fail: expected routing next_step, got {out}")
        if (_status(wt).get("artifacts") or {}).get("spec") != "current-task/specs/foo.json":
            raise AssertionError("fail: artifact_key from routing should set artifacts.spec")

        # Shinobu override: summary next_step wins when present (routing says review).
        s = _summary(
            wt,
            "override.json",
            {
                "next_step": "spec",
                "artifact": "current-task/story.md",
            },
        )
        proc, out = _write(update, root, wt, s, "--step", "gherkin")
        if out.get("next_step") != "spec":
            raise AssertionError(f"fail: summary next_step should win: {out}")
        if (_status(wt).get("artifacts") or {}).get("story") != "current-task/story.md":
            raise AssertionError("fail: artifact_key from routing should set artifacts.story")

        # Git tail: first sync → archive; second sync (archive set) → integrate.
        wt2 = tmpdir / "git-tail"
        wt2.mkdir()
        seed = _summary(wt2, "seed.json", {})
        proc, out = _write(update, root, wt2, seed, "--step", "acceptance")
        if proc.returncode != 0 or out.get("next_step") != "sync":
            raise AssertionError(f"fail: acceptance → sync: {out}")

        first = _summary(wt2, "sync1.json", {})
        proc, out = _write(update, root, wt2, first, "--step", "sync")
        if out.get("next_step") != "archive":
            raise AssertionError(f"fail: first sync → archive: {out}")
        if (_status(wt2).get("artifacts") or {}).get("sync"):
            raise AssertionError("fail: sync must not set artifacts.sync")

        status = _status(wt2)
        status["artifacts"]["archive"] = "docs/archive/foo/report.json"
        (wt2 / "current-task/status.json").write_text(
            json.dumps(status, indent=2) + "\n", encoding="utf-8"
        )

        second = _summary(wt2, "sync2.json", {})
        proc, out = _write(update, root, wt2, second, "--step", "sync")
        if out.get("next_step") != "integrate":
            raise AssertionError(f"fail: second sync → integrate: {out}")

        # Review defaults to acceptance; Shinobu can override to gherkin (new scenario).
        wt3 = tmpdir / "review"
        wt3.mkdir()
        seed = _summary(wt3, "seed.json", {"artifact": "current-task/story.md"})
        _write(update, root, wt3, seed, "--step", "gherkin")
        rev = _summary(wt3, "review.json", {})
        proc, out = _write(update, root, wt3, rev, "--step", "review")
        if out.get("next_step") != "acceptance":
            raise AssertionError(f"fail: review → acceptance: {out}")
        if (_status(wt3).get("artifacts") or {}).get("review_validation"):
            raise AssertionError("fail: review must not set review_validation")

        changes = _summary(wt3, "changes.json", {"next_step": "gherkin"})
        proc, out = _write(update, root, wt3, changes, "--step", "review")
        if out.get("next_step") != "gherkin":
            raise AssertionError(f"fail: Shinobu next_step override after review: {out}")

        # Open questions keep position.
        wt4 = tmpdir / "blocked"
        wt4.mkdir()
        seed = _summary(
            wt4,
            "seed.json",
            {"artifact": "current-task/specs/a.json"},
        )
        _write(update, root, wt4, seed, "--step", "spec")
        before = (_status(wt4).get("task") or {}).get("next_step")
        blocked = _summary(
            wt4,
            "blocked.json",
            {"open_questions": [{"question": "which CTA?"}]},
        )
        proc, out = _write(update, root, wt4, blocked, "--step", "gherkin")
        after = (_status(wt4).get("task") or {}).get("next_step")
        if after != before:
            raise AssertionError(f"fail: blocked must not advance next_step ({before} → {after})")

        # Fallback runs under the blocked step's --step and returns no artifact.
        # An errors-file artifact here would overwrite that step's pointer.
        spec_pointer = (_status(wt4).get("artifacts") or {}).get("spec")
        fallback = _summary(
            wt4,
            "fallback.json",
            {"open_questions": [{"question": "retry sheep-spec or skip?"}]},
        )
        _write(update, root, wt4, fallback, "--step", "spec")
        if (_status(wt4).get("artifacts") or {}).get("spec") != spec_pointer:
            raise AssertionError("fail: artifact-less write must leave the step pointer alone")

        declared = {
            name: cfg.get("artifact_key")
            for name, cfg in steps.items()
            if cfg.get("artifact_key")
        }
        if set(declared) != {"gherkin", "spec", "archive"}:
            raise AssertionError(f"fail: unexpected artifact_key map: {declared}")
        if declared.get("review") or declared.get("sync") or declared.get("integrate"):
            raise AssertionError("fail: operational steps must not declare artifact_key")

    print("smoke-routing-write: ok")
