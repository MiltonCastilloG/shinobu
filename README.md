# Shinobu

**Shinobu is a good dog.**

Workflow for Cursor and Claude Code. Shinobu orchestrates the current-task pipeline (start → close) in project-local worktrees with YAML/Markdown handoffs on disk.

---

## What you get

| Component | Location | Role |
| --------- | -------- | ---- |
| Orchestrator | `workflow-runtime/agents/shinobu.md` + `workflow-runtime/skills/shinobu/routing.json` | Read-only conductor; routes from disk; sends sheep via Task in isolated context |
| Sheep | `workflow-runtime/agents/sheep-*.md` | Workflow binding — load disk inputs, invoke skills (Shinobu on the pipeline; direct spawn for ad-hoc) |
| Skills | `workflow-runtime/skills/<name>/` | Pure functionality — how to perform one job; artifact schemas |
| Skill index | `workflow-runtime/skills/README.md` | Skills vs agents rules and exceptions |

Ad-hoc work outside the pipeline: Task-spawn the sheep directly with instructions and an output path (default `docs/adhoc/`), or attach the skill (e.g. `spec-maker`, `story-maker`, `conflict-resolution`) to do the work inline. No task, worktree, or status write is involved. `sheep-start`, `sheep-close`, and `sheep-status` stay Shinobu-only.

### Three layers

```text
Shinobu (workflow-runtime/agents/shinobu.md + routing.json)
  └─ sends sheep (child loads workflow-runtime/agents/sheep-*.md)
       └─ loads current-task/* from disk
       └─ follows skill (workflow-runtime/skills/<name>/SKILL.md)
       └─ returns compact YAML → Shinobu → sheep-status
```

Leaf skills are **portable** — no `status.json`, no pipeline step names, no “spawn X next”. Sheep own auto-load paths and Shinobu handoff expectations.

### Harness scripts (read / write)

Orchestration edges are invoke-and-exit Python — not a per-step schema validator:

| Type | Script | Role |
| ---- | ------ | ---- |
| Read | `workflow-runtime/skills/shinobu/scripts/bootstrap-context.py` | Position, next step, intended sheep |
| Write | `workflow-runtime/skills/current-task-update/scripts/update-status.py` | Sole writer for `current-task/status.json` |

Missing required write fields → `written: false` + `errors[]` (retry JSON); not a harness crash. Spawn gate retired: [`docs/archive/retire-check-gate/report.md`](docs/archive/retire-check-gate/report.md).

---

## Quick start

### 1. Clone and install

```bash
git clone <repo-url> shinobu
cd shinobu
python3 install.py
```

This writes a minimal `shinobu-workspace.yaml` (shinobu-only registry), ensures `worktrees/` exists, verifies committed `.cursor/agents` and `.cursor/skills` symlinks into `workflow-runtime/`, and installs the Claude Code adapter (`.claude/` links + `CLAUDE.md`). Open the repo in Cursor or Claude Code. Claude Code does not replicate Cursor hooks; pipeline work uses the installed agents and skills only. For multi-project workspaces, managed clones live under `projects/<name>/` (see [`docs/PLAN.md`](docs/PLAN.md)). How to edit the runtime: [Editing the runtime](#editing-the-runtime).

### 2. Open the repo

Open the cloned repository folder in Cursor or Claude Code.

### 3. Run with Shinobu

Address Shinobu by name:

```text
shinobu start my-task
shinobu continue
```

The parent agent Task-spawns the `shinobu` subagent (see `.cursor/rules/shinobu-default.mdc`, generated from `workflow-runtime/rules/shinobu-default.md`). Shinobu asks before sync and sends sheep (`sheep-start`, `sheep-spec`, `sheep-gherkin`, `sheep-review`, …); the consent before the first red arrives with the loop. After every sheep except start and close, Shinobu sends `sheep-status` to update `current-task/status.json`.

Git steps (`sync`, `integrate`) need explicit confirmation. Archive and close need separate confirms. Close asks to confirm worktree delete only.

---

## Editing the runtime

One real copy; both hosts read it through shortcuts.

```text
workflow-runtime/agents/   ← edit here
workflow-runtime/skills/   ← edit here
workflow-runtime/rules/    ← edit here

.cursor/agents, .cursor/skills   → symlinks (committed)
.claude/agents, .claude/skills   → symlinks (install.py)
```

Agent and skill edits are visible to Cursor and Claude the moment you save. No reinstall.

**One special case — the invocation rule.** Cursor and Claude need it as two
different files, so they are generated, not linked:

```text
workflow-runtime/rules/shinobu-default.md
  → python3 install.py   writes .cursor/rules/shinobu-default.mdc (committed)
                         and CLAUDE.md (gitignored)
```

After editing the rule, run `python3 install.py` and commit the refreshed `.mdc`.
If you forget, `python3 test.py` fails on `rule_drift`.

**Never edit through `.cursor/` or `.claude/`.** Some editors save by
write-temp-then-rename, which turns a symlink into a real folder. If a link
breaks, re-run `python3 install.py`; it self-repairs. CI runs the installer
and the smokes on every push.

---

## Pipeline

```
start → spec → gherkin → review → acceptance → sync → archive → sync → integrate → close
```

Post-review routing comes from the review sheep's return `summary`, not from a file on disk:

| Verdict | Next |
| ------- | ---- |
| changes required | Shinobu relays the verdict; with approval, jumps to `gherkin` to append a scenario (or to `spec` when the spec is wrong) |
| ready | Shinobu `acceptance` checkpoint — sync blocked until user accepts |
| blocked | Shinobu asks user |

Shinobu-only step: `acceptance`.

`sheep-start` / `sheep-close` own `global-status.json`; `sheep-status` owns per-task `status.json`.

| Step | Sheep | Loads (typical) | Primary output |
| ---- | ----- | --------------- | -------------- |
| Setup | `sheep-start` | — (creates worktree + registry) | worktree + `global-status.json` entry |
| Spec | `sheep-spec` | status, free text / `task.original` | `current-task/specs/<slug>.json` |
| Gherkin | `sheep-gherkin` | spec path | `current-task/story.md` (Gherkin checklist) |
| Review | `sheep-review` | worktree diff + available current-task files | no file — verdict in the return `summary` |
| Sync / archive / integrate | `sheep-sync`, `sheep-archive`, `sheep-integrate` | status, worktree | git side effects; `docs/archive/<slug>/` from archive only |
| Close | `sheep-close` | status | worktree deleted; unregister `global-status.json` |

---

## State on disk

```text
global-status.json                         # workspace root; sheep-start / sheep-close only
  tasks[<id>].status_path → current-task/status.json

worktrees/<path>/current-task/
  status.json                              # sheep-status only
  story.md
  specs/<slug>.json
```

Operational steps write no handoff files. Position plus these document artifacts is the whole record.

Writer schemas: `workflow-runtime/skills/current-task-update/status-format.md`, `global-status-format.md`. Shinobu and readers use slim `status-read.md` / `global-status-read.md`.

---

## Layout

```text
shinobu/
├── README.md
├── install.py / install_common.py
├── workflow-runtime/          # canonical host-neutral runtime
│   ├── agents/                # shinobu + sheep (flat)
│   ├── skills/                # pure functionality + README.md
│   └── rules/                 # shinobu-default.md (no host frontmatter)
├── docs/
│   ├── SHINOBU.md
│   ├── WORKFLOW-DIAGRAMS.md
│   ├── PLAN.md
│   ├── OWNERSHIP.md
│   ├── tasks/                 # backlog + designs
│   └── archive/<slug>/        # history; inherited baseline docs rewritten in S7
├── .cursor/                   # Cursor host adapter
│   ├── agents -> ../workflow-runtime/agents
│   ├── skills -> ../workflow-runtime/skills
│   ├── rules/                 # committed shinobu-default.mdc (from canonical rule)
│   ├── hooks/
│   └── permissions.json
└── .claude/                   # Claude host adapter (generated, gitignored)
    ├── agents -> ../workflow-runtime/agents
    └── skills -> ../workflow-runtime/skills
```

Design rationale: [`docs/SHINOBU.md`](docs/SHINOBU.md). Diagrams: [`docs/WORKFLOW-DIAGRAMS.md`](docs/WORKFLOW-DIAGRAMS.md). Multi-project workspace: [`docs/PLAN.md`](docs/PLAN.md). Backlog: [`docs/tasks/tasks.md`](docs/tasks/tasks.md). Ownership / fork map: [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md).
