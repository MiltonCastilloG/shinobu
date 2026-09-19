# Nicki — workflow orchestrator context

> Describes the Nicki baseline this repository inherited at the fork. Shinobu's pipeline replaces it — see [`SHINOBU.md`](SHINOBU.md). Rewritten in Stage 2 job S7.

Nicki is the orchestrator for the CastleMill current-task pipeline. Nicki controls workflow order, not implementation. Nicki runs bootstrap for position, asks yes only before execute and sync, sends the correct sheep, and sends `sheep-status` after every step — except start, whose script already wrote the position, and close, which deletes the task context folder.

Use this document as a rebuild guide: what Nicki is, what it controls, how the pieces fit together, and the key decisions that shaped the design.

---

## What Nicki does

| Nicki does | Nicki does not |
| ---------- | -------------- |
| Run `bootstrap-context.py` (shell allowlist) | Write files or run other shell |
| Send sheep via the Task tool | Search or edit application source |
| Ask for confirmation before **execute** and **sync** | Improvise workflow transitions |
| Pack **output path** (and for gherkin **spec path**; for spec/subtasks **pause path**; for archive **`prefix` + `slug`**) | Spawn nested sheep from workers |
| Send `sheep-status` automatically after each sheep (except start and close) | Skip execute/sync without explicit user confirmation |
| Pack the **spec path** into `sheep-gherkin` (plus story output path) | Re-derive sheep map from prose (scripts + `routing.json` own that) |

Nicki = `workflow-runtime/agents/shinobu.md` subagent (`readonly: false` — Cursor needs write to spawn sheep; shell only for bootstrap). Invoke via Task (`subagent_type: nicki`) or address by name. Custom Cursor mode may wrap Nicki later; not promised today.

### Harness scripts

Authoritative read / write surface (spawn gate retired 2026-08-05 — see [retire-check-gate](archive/retire-check-gate/report.md)):

| Type | Script | Role |
| ---- | ------ | ---- |
| Read | `bootstrap-context.py` | Position (`current_step`, `next_step`), intended sheep on stdout |
| Write | `update-status.py` | `sheep-status` path — Nicki passes `--step`/`--mode`; routing owns `next_step` on normal completion |

Modes: `normal` | `jump` only. Ad-hoc is not a write mode — the parent agent spawns a sheep directly (see [flexibility](tasks/flexibility.md) → [archive report](archive/flexibility/report.md)).

### Bootstrap chain

**Session** cold start (hooks / parent) may surface registry pointers. **Disk** bootstrap is Nicki’s every-response read: resolve worktree → run `bootstrap-context.py` → card and route from stdout only. Consent for execute/sync is chat only. Do not re-read `status.json` for routing while bootstrap succeeds.

Harness crash / bad stdout → `sheep-fallback` (not on `written: false` input errors).

---

## Architecture (three layers)

| Layer | Path | Role |
| ----- | ---- | ---- |
| Nicki | `workflow-runtime/agents/shinobu.md` + `workflow-runtime/skills/shinobu/routing.json` | Pipeline, transitions, status-update summaries, output paths |
| Sheep | `workflow-runtime/agents/sheep-*.md` | Workflow binding — disk inputs, handoffs; loaded in **child** Task context only (Nicki sends) |
| Skill | `workflow-runtime/skills/<name>/` | Pure functionality — procedures and artifact schemas; no pipeline knowledge |

See `workflow-runtime/skills/README.md` for rules and workflow exceptions.

**Frontmatter parsing:** Cursor uses a simplified YAML parser. Use single-line quoted `description: "..."` strings — do not use block scalars (`>-`, `>`, `|`) or the description may truncate to the first line only.

**Sheep** never spawn other sheep. Nicki is the only orchestrator; she sends one sheep at a time via `routing.json` → Task `subagent_type`. Nicki does **not** read sheep agent files — each child writes only at the path Nicki packed, then follows the skill. Nicki relays the sheep return JSON to `sheep-status`.

**State writer** is `sheep-status`: sole writer for per-task `current-task/status.json`. **Registry writer** is `sheep-start` / `sheep-close` only for `global-status.json`. Nicki never writes either directly.

**Ad-hoc work** spawns a sheep directly from the parent agent (or attaches the skill) — no task, no status write. `sheep-start`, `sheep-close`, and `sheep-status` stay Nicki-only. Rule: `workflow-runtime/rules/shinobu-default.md`.

---

## Canonical workflow

Step order and automatic `sheep-status` after each sheep (except start and close) are in the diagram below. Step→sheep mapping lives in `routing.json` + `bootstrap-context.py` — not duplicated here. Explicit chat confirmation is required before **execute** and **sync** only.

```mermaid
flowchart LR
  A[sheep-start] --> C[spec]
  C --> D[sheep-status]
  D --> E[sheep-gherkin]
  E --> F[sheep-status]
  F --> G[sheep-subtask]
  G --> H[sheep-status]
  H --> I[sheep-execute]
  I --> J[sheep-status]
  J --> K[sheep-review]
  K --> L{readiness}
  L -->|fix_required| P[execute fix subtasks]
  P --> I
  L -->|ready_for_acceptance| Acp[acceptance]
  Acp --> Q[sheep-sync]
  L -->|blocked| Ask[ask user]
  Q --> R[sheep-status]
  R --> Arch[sheep-archive]
  Arch --> Q2[sheep-sync]
  Q2 --> R2[sheep-status]
  R2 --> S[sheep-integrate]
  S --> T[sheep-status]
  T --> Y[sheep-close]
```

**Gherkin nuance:** Gherkin is a transform of the spec, not an interview. After spec, Nicki sends `sheep-gherkin` with the spec path and the story output path. Incomplete spec (`summary.spec_incomplete`) → send `sheep-spec` again with the gaps; do not interview at gherkin; do not send `sheep-status` for that incomplete transform. Product questions stay on spec (`spec-maker` Step 2 / stop-and-ask).

**Stop and ask:** When a sheep return carries `open_questions`, Nicki (or the parent agent ad-hoc) puts each question to the user — offering `options` when present — then re-spawns the **same** sheep with the answers. For `spec` / `subtasks`, keep the pause path so the sheep resumes. Non-empty `open_questions` holds `next_step` where it was. Never answer for the user.

---

## Sheep and artifacts

Handoffs live under `worktrees/<project>-<slug>/current-task/` at the **workspace root** (single hyphen between project and slug). Spec is JSON; story and subtasks are Markdown; archive is `report.json` + `report.md`.

| Step | Sheep | Writes code? | Primary output |
| ---- | ----- | ------------ | -------------- |
| Setup | `sheep-start` | No | `worktrees/<project>-<slug>/` via `create-worktree.py` |
| State | `sheep-status` | No (status JSON only) | `current-task/status.json` |
| Spec | `sheep-spec` | No | `current-task/specs/<slug>.json` (+ pause path) |
| Gherkin | `sheep-gherkin` | No | `artifacts.story` → usually `current-task/story.md` (from spec path) |
| Subtasks | `sheep-subtask` | No | `current-task/subtasks/<slug>.md` (+ pause path) |
| Execute | `sheep-execute` | Yes | Code changes + updated subtasks (no execution JSON) |
| Review | `sheep-review` | No | No file — verdict in the return `summary` |
| Sync | `sheep-sync` | Yes (commit + pre-push merge + push feature) | Git side effects only |
| Archive | `sheep-archive` | No | `<prefix>/docs/archive/<slug>/report.json` (+ `report.md`; optional `story.md` / `errors.json`) |
| Integrate | `sheep-integrate` | Yes (merge into target + push target) | Git side effects only |
| Close | `sheep-close` | Delete worktree | unregister + teardown |
| Fallback | `sheep-fallback` | No | Append harness failure to errors file (Nicki-only) |

### Artifact handoff chain

```
spec ──→ gherkin (story) ──→ subtasks ──→ execute (code + checklist) ──→ review (verdict in summary)
sync ──→ archive ──→ sync ──→ integrate ──→ close
```

- **Spec** defines *what* to build — requirements, scope, acceptance. No file paths. Packed from free text / `task.original`.
- **Story** (Gherkin checklist) is a transform of the spec. Nicki packs the spec path; `sheep-gherkin` does not interview.
- **Subtask list** breaks spec into one-sentence build items with checkbox completion state (tests included).
- **Execute-plan** implements unchecked subtasks in order and marks each `- [x]` in place. No `executions/*.json` handoff.
- **Review** inspects the worktree diff plus available `current-task/` files and reports its verdict in the return `summary`. No review file, no readiness file — Nicki turns the verdict into `next_step`.
- **Archive** — always `<prefix>/docs/archive/<slug>/` (`report.json`, `report.md`; `story.md` when present). Committed on feature branch before integrate. `current-task/` is gitignored (worktree-local).
- **Close** — unregister + delete whole worktree after integrate.

---

## State model: JSON status (two layers)

**Workspace registry:** `global-status.json` at workspace root — active tasks, project, worktree path, route to per-task status. **Only sheep-start and sheep-close write this file.**

**Per-task status:** `current-task/status.json` inside the worktree — `task-status.v2`: step pointers (`current_step`, `next_step`), artifact paths, `open_questions`. **Only sheep-status writes this file.**

Nicki and sheep read both; sheep must not edit either. Legacy `current-task/current-task-context.json` is deprecated.

### What it stores

| Section | Purpose |
| ------- | ------- |
| `meta` | Schema identifier only (`task-status.v2`) |
| `task` | Identity + step pointers: `current_step`, `next_step`, optional `side_effects`, short `original` |
| `scope` | `worktree_path` — hard scope boundary |
| `artifacts` | Paths to document files (`story`, `spec`, `subtasks`, `archive`) |
| `open_questions` | Blockers; empty list means Nicki can continue |

### What it deliberately omits

No verbose `history[]`, no `completed_steps`, no `last_completed_step`, no duplicate pointers (`story_artifact`, `artifacts.status`, `scope.worktree`), no ceremony meta (`generated_by`, `updated_by`, `version`). There is **no broad task-level `state` enum** — step pointers, artifact pointers, and `open_questions` are the source of truth. Out-of-band runs are logged in `task.side_effects`, not by moving position.

### Step values

`start`, `spec`, `gherkin`, `subtasks`, `execute`, `review`, `fix`, `acceptance`, `sync`, `archive`, `integrate`, `close`, `done`

Schemas: `workflow-runtime/skills/current-task-update/status-format.md`, `workflow-runtime/skills/current-task-update/global-status-format.md`, `workflow-runtime/skills/hook-contract/SKILL.md`

### Nicki summary → context update

After each sheep except start and close, Nicki sends `sheep-status` with a compact summary plus the `--step` and `--mode` she dispatched (no separate user confirmation needed). On normal completion, routing owns `next_step` — the summary does not need it. After review, Nicki may set summary `next_step` to `acceptance`, `execute`, or `review`.

```yaml
worktree: worktrees/castlemill-landing-hero-section
artifact: current-task/specs/hero-section.json
open_questions: []
summary: Spec captured requirements and acceptance criteria.
```

Nicki passes `--step spec --mode normal` (or `jump` to skip ahead — see [flexibility](tasks/flexibility.md)).

Exceptions: **do not send `sheep-status` after sheep-start** — `create-worktree.py` already wrote the opening position — **or after sheep-close** — close deletes `current-task/`.

---

## Transition discipline

Before each sheep (except `sheep-status`), Nicki shows a compact state card (task / progress / sheep / **Output path** for document steps; **spec path** for gherkin; **pause path** for spec/subtasks; **`prefix` + `slug`** for archive). **Explicit yes is required only for `execute` and `sync`.** Other steps spawn after the card without waiting for approval. Sheep name comes from bootstrap / `routing.json` — there is no spawn-gate script.

`--mode jump` changes how `update-status.py` moves position; `normal` and `jump` are the only modes, and both need a task. Ad-hoc work does not go through Nicki at all — the agent spawns the sheep directly.

---

## Key design decisions

These decisions are load-bearing. Changing them requires updating Nicki, sheep, and docs together.

### 1. Nicki does not write state; harness owns position

Nicki orchestrates but never writes files. She may run only `bootstrap-context.py`. sheep-status writes per-task `status.json` via `update-status.py`; sheep-start / sheep-close own `global-status.json`. This keeps the orchestrator from corrupting workflow state while improvising.

### 2. Sheep are atomic; no nested delegation

Every workflow step agent has `task: false`. Nicki is the only agent that invokes other agents. This keeps scope, permissions, and accountability clear.

### 3. Nicki sends sheep

Nicki sends sheep via Task `subagent_type` only. Parent agent does not run pipeline steps inline and does not send sheep (except ad-hoc, which is outside Nicki).

### 4. Disk handoffs between steps, not chat memory

Each document step produces a compact handoff (JSON or Markdown) at a Nicki-owned path. Downstream agents consume prior artifacts plus `global-status.json` / `status.json` pointers. Disk-first, not chat memory.

### 5. No broad state enum — step pointers + open questions

Instead of a `state: in_progress | blocked | done` field, status uses `current_step`, `next_step`, and `open_questions`. Blockers live in `open_questions`; handoff summaries live in artifact files, not status.

### 6. Worktree path is the hard scope boundary

Task work inside `worktrees/<project>-<slug>/` at the workspace root. Legacy `projects/<project>/worktrees/<slug>/` is deprecated. execute-plan hard boundary. Nicki validates `scope.worktree_path`.

### 7. Git tail: sync → archive → sync → integrate → close

1. **Sync** — local commit, merge base into feature branch, push feature branch (`sync-task`)
2. **Archive** — write `<prefix>/docs/archive/<slug>/` (`sheep-archive` / `task-archive`); no git
3. **Sync** (again) — commit and push archive
4. **Integrate** — merge feature into target branch, push target (`integrate-task`)
5. **Close** — unregister `global-status.json`, delete worktree (`close-task` / `close-scope`)

`current-task/` is gitignored — orchestration stays worktree-local; only archive and product changes reach the target branch.

Chat confirms for consent: **execute**, then **sync** (acceptance). Archive / integrate / close proceed after the card; merge conflicts still need user approval (`open_questions` + re-spawn).

### 8. Shared conflict-resolution protocol

sync-task and integrate-task both reference `workflow-runtime/skills/conflict-resolution/SKILL.md`. Agents summarize conflicts but must ask the user for every resolution. No inferring, no strategy flags unless the user explicitly asks.

### 9. Automatic context update after every step — except start and close

sheep-status runs automatically after each sheep without asking. Two exceptions: sheep-start's script has already written the opening position, and sheep-close removes the worktree — no context write after either.

### 10. Close: teardown

close-task unregisters `global-status.json` and deletes the whole worktree last. Archive runs earlier via `sheep-archive`. Nothing gates close on a file: routing reaches `close` only from integrate, and the status script refuses to jump there.

### 11. Spec/subtask/execute separation

- **Spec-maker** defines requirements — no file paths, no implementation subtasks.
- **Subtask-maker** maps requirements to one-sentence checklist items, including tests and verification.
- **Execute-plan** follows unchecked subtasks in order, marks completed items `- [x]`, and asks on ambiguity. Omits execution JSON.
- **Review-execution** independently inspects the diff plus available current-task files; no execution handoff required.

### 12. Review outcomes; Nicki sets next_step

Review returns a summary; Nicki may set summary `next_step` to `acceptance`, `execute`, or `review`. Default routing after review is `acceptance`. When fixes are needed, Nicki relays suggested lines in chat, waits for approval, then sends `sheep-subtask` to append `## Fix` (preserving `- [x]`). Validation readiness files are retired.

### 13. Acceptance before sync

After review lands on `acceptance`, Nicki asks yes before `sync`. No spawn-gate script.

### 14. open_questions (stop and ask)

Non-empty `open_questions` are relayed in chat and stored in status. Sheep shape them; there is no script spawn veto. Caller re-spawns the same sheep with answers (and pause path for spec/subtasks).

### 15. Caller owns paths (and archive prefix)

Nicki packs output paths. Archive always uses caller `prefix` + `slug` → `<prefix>/docs/archive/<slug>/`. Sheep must not invent paths or invent the archive root.

### 16. Partial review scope

Partial review scope (when supplied via Nicki prompt) is conversation-scoped. Review does not load an execution artifact for scope.

---

## File map for rebuilding

### Orchestrator

| File | Role |
| ---- | ---- |
| `workflow-runtime/agents/shinobu.md` | Nicki subagent definition |
| `workflow-runtime/skills/shinobu/routing.json` | Step → sheep, prompts, harness_failure |
| `workflow-runtime/skills/shinobu/scripts/bootstrap-context.py` | Read harness |
| `docs/NICKI.md` | This context overview |

### State

| File | Role |
| ---- | ---- |
| `workflow-runtime/agents/sheep-status.md` | State writer sheep |
| `workflow-runtime/skills/current-task-update/SKILL.md` | State writer workflow |
| `workflow-runtime/skills/current-task-update/scripts/update-status.py` | Write harness |
| `workflow-runtime/skills/current-task-update/status-format.md` | Per-task status schema |
| `workflow-runtime/skills/current-task-update/global-status-format.md` | Workspace registry schema |

### Sheep (agent + skill + format)

| Step | Sheep | Skill | Format schema |
| ---- | ----- | ----- | ------------- |
| Start | `sheep-start.md` | `start-task/` (`create-worktree.py`) | — |
| Spec | `sheep-spec.md` | `spec-maker/` | `spec-format.md` |
| Gherkin | `sheep-gherkin.md` | `story-maker/` | `story-format.md` |
| Subtasks | `sheep-subtask.md` | `subtask-maker/` | `subtask-format.md` |
| Execute | `sheep-execute.md` | `execute-plan/` | — (no execution JSON) |
| Review | `sheep-review.md` | `review-execution/` | `review-format.md` |
| Sync | `sheep-sync.md` | `sync-task/` | (no handoff file) |
| Archive | `sheep-archive.md` | `task-archive/` | `archive-format.md` (`report.json`) |
| Integrate | `sheep-integrate.md` | `integrate-task/` | (no handoff file) |
| Close | `sheep-close.md` | `close-task/` | — |
| Fallback | `sheep-fallback.md` | `errors-recording/` | errors file |

### Close helpers

| Skill | Role |
| ----- | ---- |
| `task-archive/` | Writes `<prefix>/docs/archive/<slug>/` |
| `close-scope/` | Paths, unregister, worktree delete |

### Shared

| File | Role |
| ---- | ---- |
| `workflow-runtime/skills/conflict-resolution/SKILL.md` | Shared merge conflict protocol for sync and integrate |
| `workflow-runtime/skills/validation/` | **Retired** — historical readiness format only |
| `workflow-runtime/rules/shinobu-default.md` | Opt-in Nicki routing + ad-hoc sheep rules |
| `workflow-runtime/skills/hook-contract/SKILL.md` | Hook / permissions contract |

---

## Tool permissions

Enforced by `.cursor/hooks/enforce-agent-tools.sh` from `.cursor/hooks/agent-permissions.json`. See `workflow-runtime/skills/hook-contract/SKILL.md`.

---

## Quick invocation

```text
nicki hero-section
nicki continue
```

Nicki sends `sheep-start` (no status write — the script already wrote `current_step: start` and `next_step: spec`), then `sheep-spec`, then `sheep-gherkin` with the spec path and story output path, and continues with `sheep-status` after every sheep except start and close. Ad-hoc: spawn one sheep directly with instructions and an output path; do not run the pipeline inline in the parent agent.

---

## Compaction + mode picker

Cursor compacts chats — disk wins via harness: `bootstrap-context.py` stdout, then artifacts as needed. Re-bootstrap on every Nicki activation; re-confirm before execute and sync. Nicki = subagent via Task today; custom mode picker future when Cursor supports repo-defined modes.

---

## Further reading

- Nicki agent definition: [`workflow-runtime/agents/shinobu.md`](../workflow-runtime/agents/shinobu.md)
- Flexibility (shipped + optional quoting polish): [`tasks/flexibility.md`](tasks/flexibility.md) → [`archive/flexibility/report.md`](archive/flexibility/report.md)
- Harness read/write ADR: [`archive/bootstrap-script/2026-07-17-harness-read-write-types-design.md`](archive/bootstrap-script/2026-07-17-harness-read-write-types-design.md)
- Retire check-gate: [`archive/retire-check-gate/report.md`](archive/retire-check-gate/report.md)
- Status schemas: [`workflow-runtime/skills/current-task-update/status-format.md`](../workflow-runtime/skills/current-task-update/status-format.md), [`workflow-runtime/skills/current-task-update/global-status-format.md`](../workflow-runtime/skills/current-task-update/global-status-format.md)
- Archive format: [`workflow-runtime/skills/task-archive/archive-format.md`](../workflow-runtime/skills/task-archive/archive-format.md)
- Backlog: [`tasks/tasks.md`](tasks/tasks.md) · Done: [`tasks/tasks-done.md`](tasks/tasks-done.md) · PLAN: [`PLAN.md`](PLAN.md)
- Shinobu (separate repo forked from Nicki after Stage 1 + #20): [`SHINOBU.md`](SHINOBU.md) · next steps: [`SHINOBU_NEXT_STEPS.md`](SHINOBU_NEXT_STEPS.md)
