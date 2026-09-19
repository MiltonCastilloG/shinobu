#!/usr/bin/env python3
"""Create one Shinobu task worktree from workspace root.

Workflow (happy path):
  1. Validate workspace root cwd
  2. Load shinobu-workspace.yaml (or .example.yaml)
  3. git pull on base branch in project git root
  4. git worktree add at worktrees/<project>-<slug>
  5. Copy registry-declared locals (skip missing with notice)
  6. Run post_create hooks in new worktree
  7. Scaffold current-task/ with initial status.json
  8. Register in global-status.json (unless --skip-register)
  9. Emit JSON handoff on stdout

On recoverable failure, partial worktrees are preserved. See WORKFLOW.md
for manual recovery steps.

Usage:
  create-worktree.py --project shinobu --slug my-task --type chore [--original "..."]
  create-worktree.py --project tetris-clone-frp --slug hero-section --type feature
  create-worktree.py --dry-run ...   # validate only, no git/copy/register
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTER_SCRIPT = SCRIPT_DIR / "register-global-status.py"
REGEN_SCRIPT = "scripts/generate-code-workspace.sh"
WORKFLOW_DOC = SCRIPT_DIR / "WORKFLOW.md"

TYPE_PREFIX = {
    "feature": "feature",
    "fix": "fix",
    "chore": "chore",
    "docs": "docs",
    "refactor": "refactor",
    "test": "test",
    "perf": "perf",
}

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class WorktreeError(Exception):
    """Recoverable worktree creation failure."""


@dataclass
class ProjectConfig:
    project_id: str
    path: Path
    git_root: Path
    copy: list[str] = field(default_factory=list)
    post_create: list[str] = field(default_factory=list)
    default_branch: str = "main"
    remote: str = "origin"


@dataclass
class Handoff:
    status: str
    project: str
    slug: str
    branch: str
    worktree_path: str
    status_path: str
    task_id: str | None = None
    registry_key: str | None = None
    git_root: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "status": self.status,
            "project": self.project,
            "slug": self.slug,
            "branch": self.branch,
            "worktree_path": self.worktree_path,
            "status_path": self.status_path,
            "git_root": self.git_root,
        }
        if self.task_id is not None:
            out["task_id"] = self.task_id
        if self.registry_key is not None:
            out["registry_key"] = self.registry_key
        if self.warnings:
            out["warnings"] = self.warnings
        if self.errors:
            out["errors"] = self.errors
        if self.dry_run:
            out["dry_run"] = True
        return out


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except ImportError:
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Minimal YAML subset for shinobu-workspace registry (stdlib fallback)."""
    root: dict[str, Any] = {"projects": {}}
    projects: dict[str, Any] = root["projects"]
    current_project: str | None = None
    current_list: str | None = None
    list_items: list[str] = []

    def flush_list() -> None:
        nonlocal list_items, current_list, current_project
        if current_project and current_list and list_items:
            proj = projects.setdefault(current_project, {})
            proj[current_list] = list_items[:]
        list_items = []

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("projects:"):
            continue
        m_proj = re.match(r"^  ([a-z0-9-]+):\s*$", line)
        if m_proj:
            flush_list()
            current_project = m_proj.group(1)
            projects[current_project] = {}
            current_list = None
            continue
        m_path = re.match(r"^    path:\s*(.+)\s*$", line)
        if m_path and current_project:
            projects[current_project]["path"] = m_path.group(1).strip()
            continue
        m_list = re.match(r"^    (copy|post_create):\s*$", line)
        if m_list and current_project:
            flush_list()
            current_list = m_list.group(1)
            list_items = []
            continue
        m_item = re.match(r"^      - (.+)\s*$", line)
        if m_item and current_project and current_list:
            list_items.append(m_item.group(1).strip())
            continue
        m_cmd = re.match(r"^    post_create:\s*$", line)
        if m_cmd:
            flush_list()
            current_list = "post_create"
            list_items = []
    flush_list()
    return root


def find_workspace_root() -> Path:
    cwd = Path.cwd().resolve()
    markers = (
        cwd / "shinobu-workspace.yaml",
        cwd / "shinobu-workspace.example.yaml",
        cwd / "workflow-runtime",
        cwd / ".cursor" / "skills" / "start-task",
    )
    if not any(p.exists() for p in markers):
        raise WorktreeError(
            "Must run from Shinobu workspace root (shinobu-workspace.yaml, "
            "workflow-runtime/, or .cursor/skills/start-task/ required)."
        )
    return cwd


def load_registry(workspace: Path) -> dict[str, Any]:
    live = workspace / "shinobu-workspace.yaml"
    if live.exists():
        return _load_yaml(live)
    example = workspace / "shinobu-workspace.example.yaml"
    if example.exists():
        print(
            "warning: shinobu-workspace.yaml not found; falling back to "
            "shinobu-workspace.example.yaml (placeholder remotes)",
            file=sys.stderr,
        )
        return _load_yaml(example)
    raise WorktreeError("No shinobu-workspace.yaml or shinobu-workspace.example.yaml found.")


def detect_default_branch(git_root: Path) -> str | None:
    """Detect the project's default branch from git when registry may be wrong."""
    if not git_root.is_dir():
        return None
    sym = git_output(git_root, "symbolic-ref", "refs/remotes/origin/HEAD", check=False)
    if sym:
        return sym.rsplit("/", 1)[-1]
    for candidate in ("main", "master"):
        if ref_exists(git_root, f"refs/heads/{candidate}") or ref_exists(
            git_root, f"refs/remotes/origin/{candidate}"
        ):
            return candidate
    return None


def resolve_project(workspace: Path, registry: dict[str, Any], project_id: str) -> ProjectConfig:
    projects = registry.get("projects") or {}
    if project_id not in projects:
        raise WorktreeError(f"Unknown project '{project_id}' in workspace registry.")
    raw = projects[project_id] or {}
    rel = raw.get("path", ".")
    project_path = (workspace / rel).resolve()
    git = raw.get("git") or {}
    registry_branch = git.get("default_branch", "main")
    default_branch_name = registry_branch
    detected = detect_default_branch(project_path)
    if detected:
        registry_ref_ok = ref_exists(
            project_path, f"refs/heads/{registry_branch}"
        ) or ref_exists(project_path, f"refs/remotes/origin/{registry_branch}")
        if not registry_ref_ok or registry_branch != detected:
            default_branch_name = detected
    return ProjectConfig(
        project_id=project_id,
        path=project_path,
        git_root=project_path,
        copy=list(raw.get("copy") or []),
        post_create=list(raw.get("post_create") or []),
        default_branch=default_branch_name,
        remote=git.get("remote", "origin"),
    )


def worktree_dir_name(project_id: str, slug: str) -> str:
    return f"{project_id}-{slug}"


def worktree_rel_path(project_id: str, slug: str) -> str:
    return f"worktrees/{worktree_dir_name(project_id, slug)}"


def default_branch(task_type: str, slug: str, override: str | None) -> str:
    if override:
        return override
    prefix = TYPE_PREFIX.get(task_type)
    if not prefix:
        raise WorktreeError(f"Unknown task type '{task_type}'.")
    return f"{prefix}/{slug}"


def run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=check,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise WorktreeError(
            f"git {' '.join(args)} failed in {cwd}: {detail}\n"
            f"See {WORKFLOW_DOC.name} for manual recovery."
        ) from exc


def git_output(cwd: Path, *args: str, check: bool = True) -> str:
    result = run_git(cwd, *args, check=check)
    return (result.stdout or "").strip()


def ref_exists(cwd: Path, ref: str) -> bool:
    return run_git(cwd, "show-ref", "--verify", "--quiet", ref, check=False).returncode == 0


def pull_main(cfg: ProjectConfig, dry_run: bool) -> list[str]:
    warnings: list[str] = []
    if dry_run:
        return warnings
    if git_output(cfg.git_root, "status", "--porcelain"):
        warnings.append(
            f"Uncommitted changes in {cfg.git_root}; continuing pull anyway."
        )
    run_git(cfg.git_root, "checkout", cfg.default_branch)
    pull = run_git(
        cfg.git_root,
        "pull",
        cfg.remote,
        cfg.default_branch,
        check=False,
    )
    if pull.returncode != 0:
        raise WorktreeError(
            f"git pull failed in {cfg.git_root}: {pull.stderr.strip() or pull.stdout.strip()}\n"
            f"See {WORKFLOW_DOC.name} for manual recovery."
        )
    return warnings


def assert_worktree_available(
    workspace: Path, cfg: ProjectConfig, wt_rel: str, branch: str, dry_run: bool = False
) -> None:
    wt_abs = workspace / wt_rel
    if wt_abs.exists():
        raise WorktreeError(
            f"Worktree path already exists: {wt_rel}. Not overwriting.\n"
            f"See {WORKFLOW_DOC.name} for manual recovery."
        )
    if dry_run:
        return
    if ref_exists(cfg.git_root, f"refs/heads/{branch}"):
        porcelain = git_output(cfg.git_root, "worktree", "list", "--porcelain")
        needle = f"branch refs/heads/{branch}"
        if needle in porcelain:
            raise WorktreeError(
                f"Branch {branch} is already checked out in another worktree.\n"
                f"See {WORKFLOW_DOC.name} for manual recovery."
            )


def add_worktree(
    workspace: Path, cfg: ProjectConfig, wt_rel: str, branch: str, dry_run: bool
) -> None:
    if dry_run:
        return
    wt_abs = workspace / wt_rel
    wt_abs.parent.mkdir(parents=True, exist_ok=True)
    # Worktree path relative to git root
    wt_from_git = os.path.relpath(wt_abs, cfg.git_root)
    branch_exists = ref_exists(cfg.git_root, f"refs/heads/{branch}")
    if branch_exists:
        run_git(cfg.git_root, "worktree", "add", wt_from_git, branch)
    else:
        run_git(
            cfg.git_root,
            "worktree",
            "add",
            wt_from_git,
            "-b",
            branch,
            cfg.default_branch,
        )


def _expand_copy_patterns(source_root: Path, patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        if "*" in pattern or "?" in pattern:
            parent = source_root
            glob_pat = pattern
            if "/" in pattern:
                parent = source_root / Path(pattern).parent
                glob_pat = Path(pattern).name
            if parent.exists():
                for match in parent.glob(glob_pat):
                    if match.is_file() or match.is_dir():
                        rp = match.resolve()
                        if rp not in seen:
                            seen.add(rp)
                            found.append(match)
        else:
            candidate = source_root / pattern
            if candidate.exists() and candidate.resolve() not in seen:
                seen.add(candidate.resolve())
                found.append(candidate)
    return found


def copy_locals(
    source_root: Path, dest_root: Path, patterns: list[str], dry_run: bool
) -> list[str]:
    notices: list[str] = []
    copied_any = False
    for pattern in patterns:
        matches = _expand_copy_patterns(source_root, [pattern])
        if not matches:
            notices.append(f"skip copy: missing source {pattern} (from {source_root})")
            continue
        for src in matches:
            rel = src.relative_to(source_root)
            dest = dest_root / rel
            if dry_run:
                notices.append(f"would copy: {src} -> {dest}")
                copied_any = True
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest, symlinks=True)
            else:
                shutil.copy2(src, dest)
            notices.append(f"copied: {rel}")
            copied_any = True
    if not copied_any and patterns:
        notices.append("no copy sources matched; continuing setup")
    return notices


def run_post_create(dest_root: Path, commands: list[str], dry_run: bool) -> None:
    for cmd in commands:
        if dry_run:
            continue
        result = subprocess.run(
            cmd,
            cwd=dest_root,
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise WorktreeError(
                f"post_create failed ({cmd!r}): "
                f"{result.stderr.strip() or result.stdout.strip()}\n"
                f"Worktree at {dest_root} was created; complete remaining steps manually.\n"
                f"See {WORKFLOW_DOC.name} for manual recovery."
            )


def scaffold_current_task(
    workspace: Path,
    wt_rel: str,
    project_id: str,
    slug: str,
    task_type: str,
    original: str,
    dry_run: bool,
) -> str:
    status_rel = f"{wt_rel}/current-task/status.json"
    if dry_run:
        return status_rel
    wt_root = workspace / wt_rel
    ct = wt_root / "current-task"
    for sub in ("specs",):
        (ct / sub).mkdir(parents=True, exist_ok=True)
    status = {
        "meta": {"schema": "task-status.v2"},
        "task": {
            "slug": slug,
            "project": project_id,
            "original": original or slug,
            "type": task_type,
            "current_step": "start",
            "next_step": "spec",
        },
        "scope": {"worktree_path": wt_rel},
        "artifacts": {},
        "open_questions": [],
    }
    (ct / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return status_rel


def register_task(
    workspace: Path,
    project_id: str,
    slug: str,
    wt_rel: str,
    task_id: str | None,
    dry_run: bool,
) -> tuple[str, str]:
    if dry_run:
        return ("dry-run-id", f"{project_id}:dry-run-id")
    cmd = [
        sys.executable,
        str(REGISTER_SCRIPT),
        str(workspace),
        project_id,
        slug,
        wt_rel,
    ]
    if task_id:
        cmd.append(task_id)
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise WorktreeError(
            f"global-status registration failed: "
            f"{result.stderr.strip() or result.stdout.strip()}\n"
            f"Worktree at {wt_rel} exists; register manually.\n"
            f"See {WORKFLOW_DOC.name} for manual recovery."
        )
    # Parse last JSON line from register script
    for line in reversed((result.stdout or "").splitlines()):
        line = line.strip()
        if line.startswith("{"):
            data = json.loads(line)
            return str(data.get("task_id", "")), str(data.get("registry_key", ""))
    # Fallback parse human line
    for line in (result.stdout or "").splitlines():
        if line.startswith("registered:"):
            parts = line.split()
            if len(parts) >= 3:
                key = parts[2]
                tid = key.split(":", 1)[-1]
                return tid, key
    raise WorktreeError("register-global-status.py succeeded but produced no task id.")


def regenerate_code_workspace(workspace: Path, dry_run: bool) -> str | None:
    if dry_run:
        return None
    script = workspace / REGEN_SCRIPT
    if not script.is_file():
        return f"workspace regeneration skipped: missing {REGEN_SCRIPT}"
    result = subprocess.run(
        ["bash", str(script)],
        cwd=workspace,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return f"workspace regeneration failed: {detail}"
    return None


def create_worktree(
    *,
    project_id: str,
    slug: str,
    task_type: str,
    branch_override: str | None,
    original: str,
    dry_run: bool,
    skip_register: bool,
    skip_pull: bool,
) -> Handoff:
    if not KEBAB_RE.match(slug):
        raise WorktreeError(f"Slug must be kebab-case: {slug!r}")

    workspace = find_workspace_root()
    registry = load_registry(workspace)
    cfg = resolve_project(workspace, registry, project_id)
    if not dry_run and not cfg.git_root.is_dir():
        raise WorktreeError(
            f"Project git root missing: {cfg.git_root}. Clone or fix registry path."
        )

    branch = default_branch(task_type, slug, branch_override)
    wt_rel = worktree_rel_path(project_id, slug)
    status_rel = f"{wt_rel}/current-task/status.json"
    handoff = Handoff(
        status="pending",
        project=project_id,
        slug=slug,
        branch=branch,
        worktree_path=wt_rel,
        status_path=status_rel,
        git_root=str(cfg.git_root),
        dry_run=dry_run,
    )

    assert_worktree_available(workspace, cfg, wt_rel, branch, dry_run)

    if not skip_pull:
        handoff.warnings.extend(pull_main(cfg, dry_run))

    add_worktree(workspace, cfg, wt_rel, branch, dry_run)

    copy_source = workspace if project_id == "shinobu" else cfg.path
    copy_notices = copy_locals(copy_source, workspace / wt_rel, cfg.copy, dry_run)
    handoff.warnings.extend(copy_notices)

    run_post_create(workspace / wt_rel, cfg.post_create, dry_run)

    scaffold_current_task(
        workspace, wt_rel, project_id, slug, task_type, original, dry_run
    )

    if not skip_register:
        tid, rkey = register_task(
            workspace, project_id, slug, wt_rel, None, dry_run
        )
        handoff.task_id = tid
        handoff.registry_key = rkey
        # Patch status.json with task id
        if not dry_run:
            status_file = workspace / status_rel
            data = json.loads(status_file.read_text(encoding="utf-8"))
            data["task"]["id"] = tid
            status_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    warn = regenerate_code_workspace(workspace, dry_run)
    if warn:
        handoff.warnings.append(warn)

    handoff.status = "dry_run" if dry_run else "complete"
    return handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Create one Shinobu task worktree.")
    parser.add_argument("--project", required=True, help="Registry project id (e.g. shinobu)")
    parser.add_argument("--slug", required=True, help="Kebab-case task slug")
    parser.add_argument(
        "--type",
        required=True,
        choices=sorted(TYPE_PREFIX),
        help="Task type for default branch prefix",
    )
    parser.add_argument("--branch", help="Override branch name")
    parser.add_argument("--original", default="", help="Original task description text")
    parser.add_argument("--dry-run", action="store_true", help="Validate without creating")
    parser.add_argument("--skip-register", action="store_true")
    parser.add_argument("--skip-pull", action="store_true")
    args = parser.parse_args()

    try:
        handoff = create_worktree(
            project_id=args.project,
            slug=args.slug,
            task_type=args.type,
            branch_override=args.branch,
            original=args.original,
            dry_run=args.dry_run,
            skip_register=args.skip_register,
            skip_pull=args.skip_pull,
        )
        print(json.dumps(handoff.to_dict(), indent=2))
        return 0
    except WorktreeError as exc:
        branch = args.branch
        if not branch:
            prefix = TYPE_PREFIX.get(args.type)
            branch = f"{prefix}/{args.slug}" if prefix else ""
        wt_rel = worktree_rel_path(args.project, args.slug)
        err = {
            "status": "error",
            "project": args.project,
            "slug": args.slug,
            "branch": branch,
            "worktree_path": wt_rel,
            "status_path": f"{wt_rel}/current-task/status.json",
            "errors": [str(exc)],
            "message": str(exc),
            "workflow_doc": str(WORKFLOW_DOC),
        }
        print(json.dumps(err, indent=2), file=sys.stderr)
        print(f"\nManual recovery: see {WORKFLOW_DOC}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
