# Shinobu

TDD pipeline. A **different product and repository**, created as a history-preserving fork of Nicki after Nicki Stage 1 and the host-neutral runtime extract. Invoked by name: `shinobu …`.

It inherits Nicki's mechanics at the fork point: one sheep at a time, disk handoffs, caller-owned paths, `sheep-status` after every sheep except `sheep-start` and `sheep-close`, `normal` / `jump`, stop-and-ask. No exceptions: the two final refactor sheep are ordinary sequential steps like every other.

Stages: [`SHINOBU_NEXT_STEPS.md`](SHINOBU_NEXT_STEPS.md).

---

## Fork boundary

Saying **Shinobu** is the selector in the Shinobu repository. There is no `--pipeline` flag and no pipeline field. Nicki and Shinobu do not coexist in one runtime and do not share live files after the fork.

| Shinobu owns after the fork | Inherited baseline (independent copy) |
| --------------------------- | ----------------------------------- |
| `workflow-runtime/agents/shinobu.md` | Leaf sheep: spec, Gherkin, review, sync, archive, integrate, fallback |
| Shinobu routing and bootstrap | Leaf skills: `spec-maker`, `scenario-maker`, review and git skills |
| `sheep-red`, `sheep-green`, `sheep-green-refactor`, `sheep-red-refactor` and their skills | Start/status/close sheep and scripts |
| Shinobu installer text, workspace/config/version names | `status.json`, `scenarios.json`, `specs/`, worktree/archive layout |

Repository identity is the namespace. Agents stay flat and retain ordinary names (`sheep-start`, `sheep-status`, `sheep-close`). Artifacts remain generic (`status.json`, `scenarios.json`, `specs/`). Product prefixes used only to avoid same-repo collisions are cancelled.

A worktree belongs to whichever repository created it.

**Stage 1 happens in Nicki** (spec-first, Gherkin-as-transform). The neutral runtime is extracted next; only then is the repository forked. Shinobu inherits that exact tagged baseline.

---

## Sheep

### New

| Sheep | Input | Output |
| ----- | ----- | ------ |
| `sheep-red` | **One Gherkin scenario** (Shinobu packs it — one object from `scenarios.json`: id, title, gherkin text — the way it packs a spec path). Worktree as scope. | Step definitions + a run. Success: the test **fails right**. Anything else is an **error** (`open_questions`); the loop stops. |
| `sheep-green` | **The git diff only** (uncommitted tree after red). | Smallest change that makes the failing test pass. Does not edit the test. Does not touch the story checklist. |
| `sheep-green-refactor` | **The post-loop git diff.** Runs **first**. | Revises implementation only: simplify, remove duplication, and improve implementation abstractions without changing behavior. Exact implementation-file scope is deliberately open until build time. |
| `sheep-red-refactor` | **The git diff after `sheep-green-refactor`.** Runs **second**. | Revises tests only: simplify, remove duplication, and improve test abstractions without changing scenario meaning. Exact test-file scope is deliberately open until build time. |

Existing step-definition files are just code in the worktree. Red sees them the way execute sees existing source — it does not need a pointer. Shinobu's job is to pack the **next scenario** into red, not to teach red where steps live.

### Modified

| Sheep | Change |
| ----- | ------ |
| `sheep-review` | Final verification, and explicitly two jobs: (1) **regressions** — run the whole suite, not just this task's scenarios, and report anything that broke; (2) **scenario compliance** — every `done: true` scenario in `scenarios.json` is actually satisfied by the implementation. A refactor that quietly changed behaviour is the failure this step exists to catch. |
| `sheep-scenarios` | Reads the **spec**. Writes `current-task/scenarios.json`: an **ordered array of scenarios**, each `{ id, title, gherkin, done: false }`, ordered by dependency. Split before ordering if a scenario cannot be summarized in two sentences, reads like a goal, or has **more than four `Then` clauses**. Amend appends a new object. **No product questions** — incomplete spec → Shinobu sends `sheep-spec` again. |

### Inherited leaf sheep

`sheep-spec`, `sheep-scenarios`, `sheep-review`, `sheep-sync`, `sheep-archive`, `sheep-integrate`, `sheep-fallback`.

`sheep-spec` is unchanged. It already accepts free text / `task.original`.

### Lifecycle inherited at fork

Start, status, and close retain the generic names `sheep-start`, `sheep-status`, and `sheep-close`. They are copied with the repository, then maintained independently. Shinobu rewrites product-facing routing/bootstrap/configuration and has no Nicki runtime dependency.

### Removed at the fork

`sheep-subtask`, `sheep-execute`, `subtask-maker`, `execute-plan`, `validation` — Nicki's tail. Deleted in Stage 2 job S2; `current-task/subtasks/` is no longer scaffolded.

---

## Questions live on spec

`sheep-spec` already stops on vague outcome, unclear scope, competing interpretations, and design forks (`spec-maker` Step 2). `sheep-scenarios` does not ask. The orchestrator does not interview at the scenarios step.

---

## Scenario list (the cursor)

`sheep-scenarios` writes `current-task/scenarios.json`: an ordered array of scenario objects, each with a stable `id`, a `title`, the `scenarios` text, and `done: false`. Array order is dependency order. That file **is** the cursor. No extra field on status.

JSON, not Markdown, because the loop is a script: "first scenario with `done: false`" is a one-line lookup, marking done is a boolean flip rather than a line edit, and red receives one object instead of a parsed Markdown block. The spec is already JSON; the story now matches it. Shinobu renders the scenarios in chat at the human gate, so the human never reads the JSON raw.

- The **loop** (Shinobu, programmatically — not a sheep) picks the first `done: false` scenario and packs that object into red.
- After green returns success, the **same loop** sets that scenario's `done` to `true`. Green never edits the story. Exact flip mechanism is for when the loop is built.
- **Exit:** no `done: false` left → `sheep-green-refactor`, then `sheep-red-refactor`.
- Amend appends a new object with `done: false`. The loop will pick it up; earlier `done: true` entries stay done and are never rewritten.
- **Runs where:** a plain in-repo script invoked synchronously in the live session — not a background daemon, not a graph framework (e.g. LangGraph).

`status.json` still holds `current_step` / `next_step` / artifact pointers / `open_questions`. It does not store which scenario is next — the story file does.

---

## Loop runs uninterrupted

After the yes before the first red, Shinobu runs red → green for every remaining scenario, then `sheep-green-refactor`, then `sheep-red-refactor`, then review, **without asking and without a timer**.

Red and green each do **one write and one run of this scenario**, then return (`task: false`). `open_questions` still stops on a real error (red failed wrong, etc.). The user is not polled between them.

The two refactor sheep run **one after the other**: `sheep-green-refactor` on the post-loop diff, then `sheep-red-refactor` on the diff that leaves. Sequential on purpose — refactoring implementation and tests at the same time lets one mask the other's regression, and the order means tests are tidied last, against implementation that has already settled. Each is an ordinary step with its own `sheep-status` after it. Each still owns a file domain and leaves the other's files alone; exact boundaries remain open until these sheep are built.

---

## Order

`sheep-status` runs after every sheep except `sheep-start` and `sheep-close`, and writes `status.json`. No step is exempt.

1. `sheep-start`
2. `sheep-spec` → `specs/`
3. `sheep-scenarios` → `scenarios.json` scenario list
4. **Human gate** — approve the scenarios
5. **Consent once**, then the loop until the checklist is clear:
   1. `sheep-red` — packed first `done: false` scenario
   2. `sheep-green` — diff
   3. loop sets that scenario `done: true` (programmatic; not a sheep)
6. `sheep-green-refactor` — post-loop diff; implementation domain only
7. `sheep-red-refactor` — the diff after step 6; test domain only
8. `sheep-review` — regressions (full suite) + every `done: true` scenario actually satisfied
9. **Human gate** — user sees the uncommitted changes, then git tail
10. Git tail:
   1. `sheep-sync`
   2. `sheep-archive`
   3. `sheep-sync`
   4. `sheep-integrate`
   5. `sheep-close`

Two consents only: before the first red, after review. Nothing in the loop or the refactor steps asks or commits.

When something is wrong, jump to `scenarios` and **append** a new scenario. If the spec is wrong, jump to spec.

---

## Red is binary

One success: the test **fails right**. Pass on arrival, broken setup, or wrong failure → `open_questions`, loop held. User and Shinobu look at it; red is re-spawned with the same scenario. Errors should be rare.

---

## Black sheep (later)

`black-sheep-*` = ad-hoc only, never a pipeline step. Inverse of the product lifecycle sheep (orchestrator-only). Membership is the black-sheep audit's output, not decided here.

First build after the audit: `black-sheep-testing-scaffold` (Gherkin runner + step-definition layout). Until then, Shinobu only runs where a runner already exists.

---

## What stays the same (reused, not copied)

Spec schema and pause, output/archive paths, modes, git tail, stop-and-ask, fallback, worktree layout, and registry are inherited at the fork point. They are independent copies afterward.
