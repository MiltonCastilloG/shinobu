"""Shared host-adapter helpers for Cursor and Claude installers."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
RUNTIME_ROOT = REPO_ROOT / "workflow-runtime"
INVOCATION_RULE = RUNTIME_ROOT / "rules" / "shinobu-default.md"

# Cursor frontmatter for the generated .mdc adapter (not stored in the canonical rule).
CURSOR_RULE_FRONTMATTER = """\
---
description: Route to Shinobu when user addresses Shinobu by name (e.g. shinobu fetch)
alwaysApply: true
---

"""

# Claude-only vocabulary swaps applied when generating CLAUDE.md from the canonical rule.
CLAUDE_SUBSTITUTIONS: list[tuple[str, str]] = [
    (
        "invoke a **fresh** Task (`subagent_type: shinobu`) — never `resume`.",
        "invoke a **fresh** `shinobu` subagent via the Agent tool — never resume a prior Shinobu session.",
    ),
    (
        "keep invoking a fresh Task on every",
        "keep invoking a fresh `shinobu` subagent on every",
    ),
    ("**Never Task-spawn sheep**", "**Never spawn sheep**"),
    ("AskQuestion", "AskUserQuestion"),
]

_COPY_FALLBACK = False


def copy_fallback_used() -> bool:
    return _COPY_FALLBACK


def reset_copy_fallback() -> None:
    global _COPY_FALLBACK
    _COPY_FALLBACK = False


def apply_substitutions(body: str, table: list[tuple[str, str]]) -> str:
    for old, new in table:
        body = body.replace(old, new)
    return body


def read_invocation_rule_body() -> str:
    if not INVOCATION_RULE.is_file():
        print(
            f"error: {INVOCATION_RULE.relative_to(REPO_ROOT)} not found",
            file=sys.stderr,
        )
        sys.exit(1)
    raw = INVOCATION_RULE.read_text(encoding="utf-8")
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        return parts[2].lstrip("\n") if len(parts) >= 3 else raw
    return raw


def render_cursor_rule() -> str:
    """Cursor `.mdc` adapter: frontmatter + canonical rule body."""
    return CURSOR_RULE_FRONTMATTER + read_invocation_rule_body()


def render_claude_md() -> str:
    """Claude `CLAUDE.md` adapter: canonical body with host substitutions."""
    return apply_substitutions(read_invocation_rule_body(), CLAUDE_SUBSTITUTIONS)


def _expected_rel(dest: Path, src: Path) -> str:
    return os.path.relpath(src, start=dest.parent)


def _is_windows_symlink_placeholder(dest: Path, src: Path) -> bool:
    """True when git checked out a symlink as a text file containing the target path."""
    if dest.is_symlink() or dest.is_dir() or not dest.is_file():
        return False
    expected = _expected_rel(dest, src)
    try:
        content = dest.read_text(encoding="utf-8").strip().replace("\\", "/")
    except OSError:
        return False
    return content in {expected, expected.replace("\\", "/")}


def _same_link(dest: Path, src: Path) -> bool:
    """True when dest is already a correct relative directory symlink to src.

    Compares the stored link text (not resolve()), so a stale double-hop like
    `.claude/agents -> ../.cursor/agents` is repaired even when both paths
    resolve to the same directory. A Windows text-file checkout of a symlink
    is *not* the same — callers must repair it (remove + recreate link or copy).
    """
    if _is_windows_symlink_placeholder(dest, src):
        return False
    if not dest.is_symlink():
        return False
    try:
        actual = os.readlink(dest).replace("\\", "/")
        expected = _expected_rel(dest, src).replace("\\", "/")
        return actual == expected
    except OSError:
        return False


def _remove_dest(dest: Path) -> None:
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)
    elif dest.exists():
        dest.unlink()


def link_dir(src: Path, dest: Path) -> str:
    """Create-or-repair a relative directory symlink. Returns 'link' or 'copy'."""
    global _COPY_FALLBACK
    if not src.is_dir():
        print(f"error: {src.relative_to(REPO_ROOT)}/ not found", file=sys.stderr)
        sys.exit(1)
    if _same_link(dest, src):
        return "link"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink() or _is_windows_symlink_placeholder(dest, src):
        _remove_dest(dest)
    rel = _expected_rel(dest, src)
    try:
        dest.symlink_to(rel, target_is_directory=True)
        return "link"
    except OSError:
        shutil.copytree(src, dest)
        _COPY_FALLBACK = True
        return "copy"
