#!/usr/bin/env python3
"""Write current-task/status.json from Shinobu summary JSON.

Required inputs:
  --worktree (CLI)
  --step (CLI) — pipeline step Shinobu dispatched; preferred over summary
    completed_step. When absent, summary may still supply completed_step or a
    position-only next_step.

Modes (--mode):
  normal — default; advances task.current_step / next_step from routing.
  jump   — skip ahead to --step: set next_step to the target; leave current_step
           untouched; no summary artifact required or materialized; log
           side_effects with artifact null. Shinobu then runs that sheep.

Both modes need a task. Ad-hoc work is a sheep invoked directly by the caller
and never reaches this script.

Optional summary fields (defaults applied):
  completed_step — overridden by --step; sets current_step / artifact pointer
  artifact — skip artifact pointer when absent or when the step has no
    routing artifact_key
  open_questions — default []; non-empty holds position instead of advancing
  next_step — when set, overrides routing after a completed step (Shinobu review
    outcomes); required for position-only writes with no completed step
  summary, task.* — ignored or derived

Success stdout: {"written": true, "path", "completed_step", "next_step", "mode", "blockers"}
  completed_step echoes --step (not a status.json field).
Input error stdout: {"written": false, "errors": [...]}
Exit 0 on success, 1 on input error or write failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from routing_write import MODES, load_routing, next_step_for

# Keys that are not status.artifacts pointers (status.json itself, etc.).
NON_ARTIFACT_KEYS = frozenset({"status", ""})


def _fail(errors: list[str]) -> None:
    print(json.dumps({"written": False, "errors": errors}))
    raise SystemExit(1)


def _read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _parse_summary(text: str, *, source_path: str | None) -> dict[str, Any]:
    suffix = Path(source_path).suffix.lower() if source_path else ".json"
    try:
        if suffix in {".yaml", ".yml"}:
            import yaml  # type: ignore

            obj = yaml.safe_load(text)
        else:
            obj = json.loads(text)
    except Exception as e:  # noqa: BLE001 — surface as input error
        _fail([f"summary parse error: {e}"])
    if not isinstance(obj, dict):
        _fail(["summary root must be a mapping/object"])
    return obj


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _init_status(
    worktree_path: str,
    slug: str,
    summary: dict[str, Any],
    completed_step: str | None,
    next_step: str | None,
) -> dict[str, Any]:
    task = summary.get("task") if isinstance(summary.get("task"), dict) else {}
    return {
        "meta": {"schema": "task-status.v2"},
        "task": {
            "slug": slug,
            "original": task.get("original") or slug,
            "title": task.get("title"),
            "type": task.get("type"),
            "current_step": completed_step if completed_step is not None else "start",
            "next_step": next_step,
        },
        "scope": {"worktree_path": worktree_path},
        "artifacts": {},
        "open_questions": [],
    }


def _artifact_key_for(step: str) -> str | None:
    """Routing's artifact_key for `step`, or None when the step writes no pointer."""
    cfg = ((load_routing().get("steps") or {}).get(step)) or {}
    key = cfg.get("artifact_key")
    if not key or key in NON_ARTIFACT_KEYS:
        return None
    return key


def _set_artifact_pointer(
    status: dict[str, Any], completed_step: str, artifact_path: str | None
) -> None:
    if not artifact_path or not completed_step:
        return

    key = _artifact_key_for(completed_step)
    if not key:
        return

    artifacts = status.setdefault("artifacts", {})
    if not isinstance(artifacts, dict):
        status["artifacts"] = {}
        artifacts = status["artifacts"]
    artifacts[key] = artifact_path


def _validate_required(
    summary: dict[str, Any], *, mode: str, completed_step: str | None
) -> None:
    errors: list[str] = []
    # Position-only normal write (no completed step) still needs next_step from
    # the summary. When a step completed, routing supplies next_step.
    if mode == "normal" and not completed_step:
        value = summary.get("next_step")
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append("missing required field: next_step")
        elif not isinstance(value, str):
            errors.append("required field must be a string: next_step")
    if mode == "jump" and not completed_step:
        errors.append("jump mode needs --step (target sheep step)")
    if mode == "jump" and completed_step in {"start", "close", "done"}:
        errors.append(f"jump mode cannot target {completed_step}")
    if errors:
        _fail(errors)


def _append_side_effect(
    status: dict[str, Any],
    step: str | None,
    artifact: str | None,
    *,
    mode: str,
) -> None:
    task = status.setdefault("task", {})
    effects = task.get("side_effects")
    if not isinstance(effects, list):
        effects = []
    effects.append(
        {
            "step": step,
            "mode": mode,
            "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "artifact": artifact,
        }
    )
    task["side_effects"] = effects


def _optional_completed_step(summary: dict[str, Any]) -> str | None:
    raw = summary.get("completed_step")
    if raw is None:
        return None
    if not isinstance(raw, str):
        _fail(["optional field must be a string when present: completed_step"])
    stripped = raw.strip()
    return stripped or None


def _derive_next_step(
    status: dict[str, Any],
    completed_step: str,
    open_questions: list[Any],
    summary: dict[str, Any],
) -> str | None:
    """Explicit next_step wins (Shinobu's review verdict); open questions hold
    position; otherwise routing advances."""
    task = status.get("task") or {}

    explicit = summary.get("next_step")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    existing = task.get("next_step")
    held = existing if isinstance(existing, str) and existing.strip() else completed_step
    if open_questions:
        return held

    derived = next_step_for(completed_step, status)
    return derived if derived is not None else held


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True, help="Repo-relative or absolute worktree path")
    parser.add_argument(
        "--json-path",
        help="Path to Shinobu summary JSON; if omitted with no --yaml-path, read stdin as JSON",
    )
    parser.add_argument(
        "--yaml-path",
        help="Deprecated: path to Shinobu summary YAML (in-flight only)",
    )
    parser.add_argument(
        "--step",
        help="Pipeline step Shinobu dispatched; overrides summary completed_step",
    )
    parser.add_argument(
        "--mode",
        default="normal",
        choices=MODES,
        help="normal advances; jump skips ahead to --step",
    )
    args = parser.parse_args()

    if not args.worktree.strip():
        _fail(["missing required field: worktree"])

    worktree_arg = args.worktree
    worktree = Path(worktree_arg)
    if not worktree.is_absolute():
        worktree = (Path.cwd() / worktree).resolve()

    slug = worktree.name
    status_path = worktree / "current-task" / "status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)

    source = args.json_path or args.yaml_path
    summary = _parse_summary(_read_text(source), source_path=source)

    completed_step = (args.step or "").strip() or _optional_completed_step(summary)
    _validate_required(summary, mode=args.mode, completed_step=completed_step)

    artifact = summary.get("artifact")
    open_questions = summary.get("open_questions", [])

    if artifact is not None and not isinstance(artifact, str):
        _fail(["optional field must be a string when present: artifact"])
    if not isinstance(open_questions, list):
        _fail(["optional field must be a list when present: open_questions"])

    # Placeholder until derived or taken from a position-only summary.
    next_step: str | None = summary.get("next_step") if isinstance(summary.get("next_step"), str) else None

    status = _load_json(status_path)
    if status is None:
        if args.mode == "jump":
            _fail(["jump mode needs an existing status.json"])
        # Derive before init when we already know the completed step.
        if completed_step is not None:
            if open_questions:
                next_step = completed_step
            else:
                next_step = next_step_for(
                    completed_step, {"task": {"slug": slug}, "artifacts": {}}
                )
                if next_step is None:
                    next_step = "spec" if completed_step == "start" else completed_step
        status = _init_status(
            str(Path(worktree_arg)),
            slug,
            summary,
            completed_step,
            next_step,
        )

    status["meta"] = {"schema": "task-status.v2"}

    task = status.setdefault("task", {})
    if not isinstance(task, dict):
        task = {}
        status["task"] = task
    task["slug"] = task.get("slug") or slug

    art = artifact if isinstance(artifact, str) else None

    if args.mode == "jump":
        # Position-only: set next_step to target; leave current_step untouched;
        # never materialize or require a summary artifact.
        assert completed_step is not None  # validated above
        task["next_step"] = completed_step
        next_step = completed_step
        _append_side_effect(status, completed_step, None, mode="jump")
    elif completed_step is not None:
        task["current_step"] = completed_step
        _set_artifact_pointer(status, completed_step, art)
        next_step = _derive_next_step(status, completed_step, open_questions, summary)
        task["next_step"] = next_step
    else:
        # Position-only: summary next_step is the authority.
        task["next_step"] = next_step
        existing = task.get("current_step")
        if not isinstance(existing, str) or not existing.strip():
            task["current_step"] = "start"

    # Drop legacy history list if present — position + artifacts are enough.
    task.pop("completed_steps", None)

    scope = status.setdefault("scope", {})
    if not isinstance(scope, dict):
        scope = {}
        status["scope"] = scope
    scope["worktree_path"] = scope.get("worktree_path") or str(Path(worktree_arg))

    if args.mode == "normal" or "open_questions" in summary:
        status["open_questions"] = open_questions

    try:
        status_path.write_text(
            json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError as e:
        _fail([f"failed to write status.json: {e}"])

    blockers: list[dict[str, Any]] = []
    for q in open_questions:
        if isinstance(q, dict):
            blockers.append(q)
        else:
            blockers.append({"step": next_step, "question": str(q), "blocks_next_step": True})

    print(
        json.dumps(
            {
                "written": True,
                "path": str(status_path),
                "completed_step": completed_step,
                "next_step": next_step,
                "mode": args.mode,
                "blockers": blockers,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
