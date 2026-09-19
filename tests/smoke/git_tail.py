"""Git tail structure: the sync/integrate sheep exist, the retired per-verb sheep do not."""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED = (
    "workflow-runtime/agents/sheep-sync.md",
    "workflow-runtime/skills/sync-task/SKILL.md",
    "workflow-runtime/agents/sheep-integrate.md",
    "workflow-runtime/skills/integrate-task/SKILL.md",
)

RETIRED = (
    "workflow-runtime/agents/commit-task.md",
    "workflow-runtime/agents/push-task.md",
    "workflow-runtime/agents/merge-task.md",
    "workflow-runtime/agents/publish-task.md",
)

# Routing must keep a sheep for each git-tail step, since Shinobu spawns from that value.
TAIL_SHEEP = {
    "sync": "sheep-sync",
    "archive": "sheep-archive",
    "integrate": "sheep-integrate",
    "close": "sheep-close",
}


def run(root: Path) -> None:
    failures: list[str] = []

    for rel in REQUIRED:
        if not (root / rel).exists():
            failures.append(f"fail: missing {rel}")
    for rel in RETIRED:
        if (root / rel).exists():
            failures.append(f"fail: {rel} should be removed")

    steps = (
        json.loads((root / "workflow-runtime/skills/shinobu/routing.json").read_text(encoding="utf-8")).get(
            "steps"
        )
        or {}
    )
    for step, sheep in TAIL_SHEEP.items():
        got = (steps.get(step) or {}).get("sheep")
        if got != sheep:
            failures.append(f"fail: routing {step}.sheep is {got!r}, expected {sheep!r}")
        else:
            print(f"ok: {step} → {sheep}")

    # Decision 4: sheep hold no workflow knowledge — no Gate: prose, no next_step.
    banned = ("**Gate:**", "next_step:", '"next_step"', "completed_step:")
    for path in sorted((root / "workflow-runtime/agents").glob("sheep-*.md")):
        if path.name == "sheep-status.md":
            continue  # documents the write CLI, may mention the fields by name
        text = path.read_text(encoding="utf-8")
        for needle in banned:
            if needle in text:
                failures.append(f"fail: {path.name} still contains workflow text {needle!r}")

    if failures:
        raise AssertionError("\n".join(failures))

    print("smoke-git-tail: ok")
