"""Every path string in the scanned runtime surface must resolve to an existing path."""

from __future__ import annotations

import json
import re
from pathlib import Path

# Capture the full token (incl. * and <>); exclusions run on the whole token after.
# Bound by whitespace, backtick, quote, paren, or bracket — not by * or <>.
PATH_RE = re.compile(
    r"(?:workflow-runtime|\.cursor|\.\./)"
    r"[^\s`\"'()\[\]]+"
)

TRAIL_PUNCT = ".,;:)]}\"'"


def _skip_file(path: Path) -> bool:
    parts = set(path.parts)
    return "fixtures" in parts or "__pycache__" in parts


def _excluded_path(raw: str) -> bool:
    if "<" in raw or ">" in raw or "*" in raw:
        return True
    if raw.startswith("current-task/") or "/current-task/" in raw:
        return True
    if raw.startswith("docs/archive/") or "/docs/archive/" in raw:
        return True
    if raw.startswith("docs/adhoc/") or "/docs/adhoc/" in raw:
        return True
    return False


def _normalize_match(raw: str) -> str:
    path = raw.strip()
    while path and path[-1] in TRAIL_PUNCT:
        path = path[:-1]
    return path


def _iter_md_paths(text: str) -> list[tuple[int, str]]:
    """Return (1-based line number, path) for each match shape in markdown."""
    found: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in PATH_RE.finditer(line):
            path = _normalize_match(match.group(0))
            if path and not _excluded_path(path):
                found.append((lineno, path))
    return found


def _resolve(root: Path, source: Path, path: str) -> Path:
    if path.startswith("../"):
        return (source.parent / path).resolve()
    return (root / path).resolve()


def _check(root: Path, source: Path, lineno: int, path: str, failures: list[str]) -> None:
    try:
        target = _resolve(root, source, path)
    except (OSError, ValueError):
        failures.append(f"{source.relative_to(root)}:{lineno}: unresolved {path!r}")
        return
    # Anchor-agnostic: .cursor/… may be a symlink; resolve() follows it.
    if not target.exists():
        failures.append(f"{source.relative_to(root)}:{lineno}: unresolved {path!r}")


def _scan_markdown(root: Path, failures: list[str]) -> None:
    agents = sorted((root / "workflow-runtime" / "agents").glob("*.md"))
    skills = sorted((root / "workflow-runtime" / "skills").rglob("*.md"))
    for source in agents + skills:
        if _skip_file(source):
            continue
        for lineno, path in _iter_md_paths(source.read_text(encoding="utf-8")):
            _check(root, source, lineno, path, failures)


def _scan_routing(root: Path, failures: list[str]) -> None:
    source = root / "workflow-runtime" / "skills" / "shinobu" / "routing.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    scripts = ((data.get("harness_failure") or {}).get("scripts")) or {}
    text = source.read_text(encoding="utf-8")
    for _name, entry in scripts.items():
        route = (entry or {}).get("route")
        if not isinstance(route, str) or _excluded_path(route):
            continue
        lineno = 1
        needle = f'"{route}"'
        for i, line in enumerate(text.splitlines(), start=1):
            if needle in line:
                lineno = i
                break
        _check(root, source, lineno, route, failures)


def _scan_permissions(root: Path, failures: list[str]) -> None:
    source = root / ".cursor" / "permissions.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    allow = data.get("terminalAllowlist") or []
    text = source.read_text(encoding="utf-8")
    for entry in allow:
        if not isinstance(entry, str):
            continue
        tokens = entry.split()
        if len(tokens) < 2 or "/" not in tokens[1]:
            continue
        path = _normalize_match(tokens[1])
        if not path.startswith(("workflow-runtime/", ".cursor/", "../")):
            continue
        if _excluded_path(path):
            continue
        lineno = 1
        for i, line in enumerate(text.splitlines(), start=1):
            if path in line:
                lineno = i
                break
        _check(root, source, lineno, path, failures)


def _scan_hooks(root: Path, failures: list[str]) -> None:
    source = root / ".cursor" / "hooks.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    commands = ((data.get("hooks") or {}).get("preToolUse")) or []
    text = source.read_text(encoding="utf-8")
    for entry in commands:
        command = (entry or {}).get("command")
        if not isinstance(command, str):
            continue
        path = _normalize_match(command.split()[0] if command.split() else command)
        if not path.startswith(("workflow-runtime/", ".cursor/", "../")):
            continue
        if _excluded_path(path):
            continue
        lineno = 1
        for i, line in enumerate(text.splitlines(), start=1):
            if path in line:
                lineno = i
                break
        _check(root, source, lineno, path, failures)


def run(root: Path) -> None:
    failures: list[str] = []
    _scan_markdown(root, failures)
    _scan_routing(root, failures)
    _scan_permissions(root, failures)
    _scan_hooks(root, failures)

    if failures:
        raise AssertionError("\n".join(failures))
    print("smoke-path-resolution: ok")
