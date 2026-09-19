#!/usr/bin/env python3
"""Post-clone bootstrap for the Shinobu repository (Cursor + Claude host adapters)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from install_common import (
    REPO_ROOT,
    RUNTIME_ROOT,
    link_dir,
    render_claude_md,
    render_cursor_rule,
    reset_copy_fallback,
)

REGISTRY_PATH = REPO_ROOT / "shinobu-workspace.yaml"
WORKTREES_DIR = REPO_ROOT / "worktrees"
CURSOR_DIR = REPO_ROOT / ".cursor"
CURSOR_AGENTS = CURSOR_DIR / "agents"
CURSOR_SKILLS = CURSOR_DIR / "skills"
CURSOR_RULE = CURSOR_DIR / "rules" / "shinobu-default.mdc"
CLAUDE_DIR = REPO_ROOT / ".claude"
CLAUDE_AGENTS = CLAUDE_DIR / "agents"
CLAUDE_SKILLS = CLAUDE_DIR / "skills"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

REGISTRY_STUB = """version: 1

projects:
  shinobu:
    path: .
    git:
      default_branch: main
      remote: origin
    copy: []
    post_create: []
"""


def check_git_prereq() -> None:
    git = shutil.which("git")
    if git is None:
        print("error: git is required but was not found on PATH", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run([git, "--version"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("error: git is required but could not determine version", file=sys.stderr)
        sys.exit(1)
    print(result.stdout.strip())


def ensure_worktrees() -> None:
    if WORKTREES_DIR.exists():
        return
    WORKTREES_DIR.mkdir(parents=True)
    (WORKTREES_DIR / ".gitkeep").touch()


def write_registry() -> None:
    if REGISTRY_PATH.exists():
        print("shinobu-workspace.yaml already exists — registry skipped")
        return
    REGISTRY_PATH.write_text(REGISTRY_STUB)


def verify_cursor_runtime() -> tuple[int, str, str]:
    """Repair committed .cursor/agents and .cursor/skills links into workflow-runtime/."""
    agent_mode = link_dir(RUNTIME_ROOT / "agents", CURSOR_AGENTS)
    skill_mode = link_dir(RUNTIME_ROOT / "skills", CURSOR_SKILLS)
    agent_count = len(list((RUNTIME_ROOT / "agents").glob("*.md")))
    return agent_count, agent_mode, skill_mode


def write_cursor_rule() -> None:
    """Generate .cursor/rules/shinobu-default.mdc from the canonical rule + Cursor frontmatter."""
    CURSOR_RULE.parent.mkdir(parents=True, exist_ok=True)
    CURSOR_RULE.write_text(render_cursor_rule(), encoding="utf-8")


def install_claude_runtime() -> tuple[int, str, str]:
    """Link .claude/agents and .claude/skills into workflow-runtime/."""
    agent_mode = link_dir(RUNTIME_ROOT / "agents", CLAUDE_AGENTS)
    skill_mode = link_dir(RUNTIME_ROOT / "skills", CLAUDE_SKILLS)
    agent_count = len(list((RUNTIME_ROOT / "agents").glob("*.md")))
    return agent_count, agent_mode, skill_mode


def write_claude_md() -> None:
    """Generate CLAUDE.md from the canonical rule via the Claude substitution table."""
    CLAUDE_MD.write_text(render_claude_md(), encoding="utf-8")


def _mode_label(agent_mode: str, skill_mode: str) -> str:
    return "copies" if agent_mode == "copy" or skill_mode == "copy" else "links"


def print_success(
    cursor_modes: tuple[str, str],
    claude_modes: tuple[str, str],
) -> None:
    cursor_fallback = cursor_modes[0] == "copy" or cursor_modes[1] == "copy"
    claude_fallback = claude_modes[0] == "copy" or claude_modes[1] == "copy"
    if cursor_fallback or claude_fallback:
        hosts = []
        if cursor_fallback:
            hosts.append("Cursor")
        if claude_fallback:
            hosts.append("Claude")
        which = " and ".join(hosts)
        print(
            f"warning: directory symlinks unavailable for {which}; "
            "copied agents/skills — re-run install.py after runtime edits",
            file=sys.stderr,
        )

    cursor_kind = _mode_label(*cursor_modes)
    claude_kind = _mode_label(*claude_modes)
    print(f"Cursor:  .cursor/agents, .cursor/skills -> workflow-runtime/ ({cursor_kind})")
    print(f"         {CURSOR_RULE.relative_to(REPO_ROOT)} written (committed)")
    print(f"Claude:  .claude/agents, .claude/skills -> workflow-runtime/ ({claude_kind})")
    print("         CLAUDE.md written (gitignored)")
    print("Edit runtime under workflow-runtime/. Re-run install.py after editing")
    print("workflow-runtime/rules/*.md and commit the refreshed .mdc.")
    print()
    print("Next steps:")
    print("  1. Open this repository in Cursor or Claude Code.")
    print("  2. Invoke Shinobu to start or continue a task:")
    print("       shinobu start my-task")
    print("       shinobu continue")
    print()
    print(
        "Note: Claude Code does not replicate Cursor hooks; "
        "Shinobu pipeline work uses the installed agents and skills only."
    )


def main() -> None:
    reset_copy_fallback()
    check_git_prereq()
    ensure_worktrees()
    write_registry()
    _, cursor_agent_mode, cursor_skill_mode = verify_cursor_runtime()
    write_cursor_rule()
    _, claude_agent_mode, claude_skill_mode = install_claude_runtime()
    write_claude_md()
    print_success(
        (cursor_agent_mode, cursor_skill_mode),
        (claude_agent_mode, claude_skill_mode),
    )


if __name__ == "__main__":
    main()
