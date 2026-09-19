"""Committed / installed host rule adapters must match install_common renderers."""

from __future__ import annotations

import tempfile
from pathlib import Path

from install_common import render_claude_md, render_cursor_rule

CURSOR_RULE = ".cursor/rules/shinobu-default.mdc"
CLAUDE_MD = "CLAUDE.md"


def run(root: Path) -> None:
    failures: list[str] = []

    expected_mdc = render_cursor_rule()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_mdc = Path(tmp) / "shinobu-default.mdc"
        tmp_mdc.write_text(expected_mdc, encoding="utf-8")
        committed = root / CURSOR_RULE
        if not committed.is_file():
            failures.append(f"fail: missing committed {CURSOR_RULE}")
        elif committed.read_bytes() != tmp_mdc.read_bytes():
            failures.append(
                f"fail: {CURSOR_RULE} drifts from install_common.render_cursor_rule()"
            )
        else:
            print(f"ok: {CURSOR_RULE} matches render_cursor_rule()")

    expected_claude = render_claude_md()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_claude = Path(tmp) / "CLAUDE.md"
        tmp_claude.write_text(expected_claude, encoding="utf-8")
        installed = root / CLAUDE_MD
        if not installed.is_file():
            failures.append(
                f"fail: missing installed {CLAUDE_MD} — run python3 install.py"
            )
        elif installed.read_bytes() != tmp_claude.read_bytes():
            failures.append(
                f"fail: {CLAUDE_MD} drifts from install_common.render_claude_md()"
            )
        else:
            print(f"ok: {CLAUDE_MD} matches render_claude_md()")

    if failures:
        raise AssertionError("\n".join(failures))
    print("smoke-rule-drift: ok")
