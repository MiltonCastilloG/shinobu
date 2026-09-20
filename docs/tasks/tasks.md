# Shinobu — tasks

Actionable backlog. Completed work: [`tasks-done.md`](tasks-done.md).

This repository is a history-preserving fork of Nicki at `v0.3.0-nicki-baseline`. Stage 2 builds the TDD pipeline: [`SHINOBU.md`](../SHINOBU.md) · sequence: [`SHINOBU_NEXT_STEPS.md`](../SHINOBU_NEXT_STEPS.md) · job graph, write domains, and per-job done-when: [`2026-09-19-shinobu-stage-2-plan.md`](2026-09-19-shinobu-stage-2-plan.md).

## Three goals (always)

Every change must respect **all three**. They are standing requirements, not pick-one options.

| Goal | Always means |
|------|----------------|
| **Correct functioning** | Pipeline runs end-to-end; worktrees, paths, handoffs work |
| **Harness and guardrails** | Read/write scripts + smoke tests stay in place; scripts enforce position; chat consent before first red and after review |
| **Trimming** | Prompt and docs stay lean; cut duplication when safe |

**When goals conflict**, higher tier wins: (1) Correct functioning → (2) Harness and guardrails → (3) Trimming.

Example: never trim `shinobu.md` consent rules that scripts do not enforce.

---

## Stage 2 — build Shinobu

One worker session per job. The architect session owns this file; a worker flips **only its own row** at the end. Full scope, non-scope, file lists, and done-when live in the [plan note](2026-09-19-shinobu-stage-2-plan.md).

| # | Job | Depends on | Runs with | Status |
|---|-----|-----------|-----------|--------|
| **S1** | Identity rename — `nicki` → `shinobu` for the orchestrator, rule, routing/bootstrap folder, config/workspace/version filenames, installers, permissions keys, smokes, README | — | alone | done |
| **S2** | Remove the Nicki tail — `sheep-subtask`, `sheep-execute`, `subtask-maker`, `execute-plan`, `validation`; routing steps `subtasks`/`execute`/`fix`; `current-task/subtasks/`; the smokes that assert them | S1 | alone | done |
| **S2a** | `scenarios.json` — the gherkin sheep writes an ordered scenario array `{ id, title, gherkin, done }` instead of a Markdown checklist, so the loop reads and flips without parsing prose; and one name at every level: step `scenarios`, `sheep-scenarios`, `scenario-maker`, `artifacts.scenarios` | S2 | alone | **next** |
| **S3a** | `sheep-red` + `sheep-green` and their skills (`red-implementation`, `green-implementation`) | S2a | **∥ S3b, S3c** | todo |
| **S3b** | `sheep-green-refactor` + `sheep-red-refactor` and their skills. Serial at runtime — green-refactor on the post-loop diff, then red-refactor on what it leaves. **Settles the open refactor-scope question** — each SKILL.md states its own write domain | S2a | **∥ S3a, S3c** | todo |
| **S3c** | Review hardening — `sheep-review` + `review-execution` gain two named duties: full-suite **regression** check, and **scenario compliance** against every `- [x]` in `story.md` | S2a | **∥ S3a, S3b** | todo |
| **S4** | Loop + routing + status — `shinobu.md` orchestration, loop-back while `story.md` has `- [ ]`, then `green-refactor` → `red-refactor` → `review` as four ordinary steps, the four new permission keys | S3a, S3b, S3c | alone | todo |
| **S5** | Shinobu smokes — loop cursor while `scenarios.json` has `done: false`, loop exit, red-failure `open_questions` hold, refactor step order | S4 | **∥ S7** | todo |
| **S7** | Docs — README pipeline + layout, `NICKI.md` → Shinobu semantics, `WORKFLOW-DIAGRAMS.md`, `OWNERSHIP.md` fork-action column | S4 | **∥ S5** | todo |
| **S6** | Dogfood on a managed clone that already has a runner. **Human-gated** — architect writes the checklist, human runs it | S5 | — | todo |

### Manual step after S1 — **done**

The live registry was renamed to `shinobu-workspace.yaml` with self key `shinobu:`, by hand, because it is gitignored. `projects/`, `worktrees/`, and `global-status.json` were never touched.

That closes the one hazard S1 created: `install.py:write_registry()` writes a one-project stub whenever the registry is absent, and a stub would have silenced the new fallback warning *and* shadowed the live registry with `copy: []`, so new worktrees would silently stop receiving `.env` and `node_modules`. With the real file in place, `write_registry()` skips. The stub behaviour is correct for a genuinely fresh clone and is left alone.

### Known lag between S1 and S7

S1 deliberately leaves `docs/NICKI.md`, `docs/WORKFLOW-DIAGRAMS.md`, `docs/PLAN.md`, and `docs/OWNERSHIP.md` alone, and adds a banner to the first two saying they describe the inherited baseline. S7 rewrites them once the pipeline is real.

**Dead paths: fixed.** The S1 audit found `docs/NICKI.md` and `docs/WORKFLOW-DIAGRAMS.md` pointing at `workflow-runtime/skills/nicki/…`, `agents/nicki.md`, and `rules/nicki-default.md` — paths that no longer exist. The banner covers stale *behaviour*, not dead *file paths*, and `path_resolution` does not scan `docs/`. Path strings were corrected in place; prose still says Nicki, which is what the banner is for. S7 still owns the rewrite.

**`docs/PLAN.md` got the same banner.** Its paths were *not* corrected: the whole document describes a `nicki` CLI, `NickiWorkspace`, and `bin/nicki` that were never built, so a filename sweep would half-rename a document whose subject is Nicki itself. It is rewritten if and when the PLAN CLI is picked up.

**README link exception, deliberate.** S1 could not keep README links to `docs/NICKI.md`: the done-when grep is file-scoped and README is not on its allowlist, so a link whose *filename* contains the product name fails the check. README now points at `SHINOBU.md` for layout and rationale, which is the better target anyway. Kept.

---

## Later / deferred

Nothing below blocks Stage 2. **22–25 are mutually independent — any or all can run in parallel, before or after Stage 2.**

| # | Item | Notes |
|---|------|-------|
| **22** | PR-gated integrate | **Deferred at the fork, deliberately.** `sync` opens/updates the PR; `integrate` waits on checks, then merges (keep the local merge; do not switch to `gh pr merge`). Degrade to today's local merge when there is no remote or no `gh`. Conflicts stay local and human-approved; consent model unchanged. Adopt if a red merge ever actually happens. Design: §Layer D of [the design note](2026-09-19-runtime-extract-and-delivery-options.md). |
| **23** | Runtime install into managed projects | `install.py --project projects/<name>` links/copies `workflow-runtime/` into that project's host dirs. Fixes observed staleness: `projects/tetris-clone-frp/.cursor/` has `skills/` and no `agents/`; the other two clones have no `.cursor/`. Likely to bite during **S6** — revisit then. |
| **24** | Release artifact on tag | CI on `v*` builds a runtime tarball with **materialized** (copied, Windows-safe) host adapters, attached to a GitHub Release. Gives `shinobu_version.yaml` meaning. Rejected alternative: committing generated adapters back to `main`. |
| **25** | Real-git worktree exercise in CI | `git init` fixture → start → status → close. Git is present in Actions, no remote needed. Largest unclaimed automation win. |
| **17** | AWS deployment exploration | How TBD. Candidate: [Bedrock AgentCore MCP](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/mcp-getting-started.html). Document options; no playbook yet. |
| | PLAN CLI + multi-project dogfood | [`PLAN.md`](../PLAN.md) — schema, `workspace init` / clone / install / doctor |
| | Caller-owned output shape | [`caller-owned-output-shape.md`](caller-owned-output-shape.md) — revisit once the Stage 2 sheep exist; archive-only bugs if they bite |
| | Stage 3 — black sheep | Audit which sheep are ad-hoc-only, then `black-sheep-testing-scaffold` (runner + step-definition layout). [`SHINOBU_NEXT_STEPS.md`](../SHINOBU_NEXT_STEPS.md) |
| | Quoting polish | Optional only — [`story-format.md`](../../workflow-runtime/skills/scenario-maker/story-format.md). Not a rewrite. |

**Not doing:** shared runtime package, submodule, or subtree · any Nicki↔Shinobu sync or cherry-pick automation · product-suffixed sheep or artifact names · a `--pipeline` flag · Claude hook parity or a generated Claude permissions adapter · branch protection on `main` · `doctor` / version pin · evaluation harness or repository.

---

## References

| Doc | Role |
|-----|------|
| [`2026-09-19-shinobu-stage-2-plan.md`](2026-09-19-shinobu-stage-2-plan.md) | Stage 2 job graph, write domains, done-when, open questions |
| [`SHINOBU.md`](../SHINOBU.md) | Destination behaviour — sheep, loop, gates |
| [`SHINOBU_NEXT_STEPS.md`](../SHINOBU_NEXT_STEPS.md) | Stages, sequencing, and the settled table |
| [`OWNERSHIP.md`](../OWNERSHIP.md) | Per-file owner and fork action |
| [`2026-09-19-runtime-extract-and-delivery-options.md`](2026-09-19-runtime-extract-and-delivery-options.md) | Extract, distribution, validation, and git-tail options |
| [`tasks-done.md`](tasks-done.md) | Shipped tasks and archives |
| [`flexibility.md`](flexibility.md) | Flexibility model (shipped) |
| [`NICKI.md`](../NICKI.md) | Inherited baseline semantics — rewritten by S7 |
| [`WORKFLOW-DIAGRAMS.md`](../WORKFLOW-DIAGRAMS.md) | Inherited baseline diagrams — rewritten by S7 |
