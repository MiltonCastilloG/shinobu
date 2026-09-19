"""Archive process must surface task.side_effects (flexibility step 8 / A5)."""

from __future__ import annotations

from pathlib import Path

FORMAT = "workflow-runtime/skills/task-archive/archive-format.md"
SKILL = "workflow-runtime/skills/task-archive/SKILL.md"
SHINOBU = "workflow-runtime/agents/shinobu.md"

# Contract needles — archive drafts from these docs, so prose is the authority.
# Sheep only points at the skill; side_effects language lives in skill + format.
NEEDLES = (
    (FORMAT, "task.side_effects"),
    (FORMAT, "<mode> <step> at <at>"),
    (FORMAT, "no artifact"),
    (FORMAT, "append one `process` row per"),
    (SKILL, "side_effects"),
    (SHINOBU, "--mode jump --step <target>"),
)


def run(root: Path) -> None:
    failures: list[str] = []
    for rel, needle in NEEDLES:
        text = (root / rel).read_text(encoding="utf-8")
        if needle not in text:
            failures.append(f"fail: {rel} missing {needle!r}")

    if failures:
        raise AssertionError("\n".join(failures))
    print("smoke-archive-side-effects: ok")
