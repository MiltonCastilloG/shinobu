# Shinobu — next steps

Destination: [`SHINOBU.md`](SHINOBU.md). Shinobu is a **separate repository forked from Nicki**. In that repository, `shinobu …` routes to the Shinobu agent. Nicki does not grow a pipeline switch.

Strategy: **Stage 1 improves Nicki. Task #20 makes the baseline host-neutral. Stage 2 begins by forking the repository, then builds Shinobu. Stage 3 is black sheep.**

---

## Why fork after the baseline

The evaluation needs independent implementations. A history-preserving fork copies the proven baseline once, then lets Nicki and Shinobu change without hidden shared-code effects.

Run Stage 1 and the neutral-runtime extract before the fork so both products inherit the same behavior, host adapters, smokes, and history. After the fork there is no shared runtime package and no automatic cross-repository synchronization.

---

## Settled — do not reopen

| Topic | Decision |
| ----- | -------- |
| Invocation | `nicki …` in the Nicki repo; `shinobu …` in the Shinobu repo. No `--pipeline`. |
| Products | Independent repositories with shared Git history through the fork point. |
| Artifacts | Keep generic `status.json`, `scenarios.json`, `specs/`, and `global-status.json`; repository identity is the namespace. `subtasks/` was removed with the Nicki tail (S2); `story.md` became `scenarios.json` (S2a). |
| Agents | Flat agent folder. Keep generic sheep names in each repository; fork changes only the orchestrator selector from `nicki` to `shinobu`. |
| Runtime | Extract `workflow-runtime/` before the fork. `.cursor/` and `.claude/` are host adapters. |
| Spec | Unchanged. Already accepts free text / `task.original`. |
| Spec first | **Nicki Stage 1**, also what Shinobu's head is. One `scenario-maker`. |
| Scenario naming | One word at every level: step `scenarios`, `sheep-scenarios`, skill `scenario-maker`, file `current-task/scenarios.json`, key `artifacts.scenarios`. Gherkin is the *format* the file holds, not a name for the step or the artifact. |
| Gherkin | Spec → `scenarios.json`: an **ordered array** of scenario objects `{ id, title, gherkin, done }`. No product questions. |
| Split | More than four **`Then`** clauses, or two-sentence / goal-shaped. |
| Consent | Once before first red; once after review. Red / green and the two final refactors run uninterrupted — no clock. |
| Red | Input = **one Gherkin scenario** packed by Shinobu. Success = fails right. Else error / hold. |
| Green | Input = **git diff only**. Does not edit the test or the story. |
| Final refactors | **Serial, in this order:** `sheep-green-refactor` (implementation) on the post-loop diff, then `sheep-red-refactor` (tests) on the diff that leaves. Sequential so neither can mask the other's regression, and tests are tidied last against settled implementation. Each owns a file domain; exact scope is open until build time. |
| Amend | Append as a **new** scenario object with `done: false`. Final refactors or the human catch duplication. |
| Cursor | `scenarios.json`. The **loop** packs the first `done: false` scenario into red; after green succeeds, the **same loop** sets `done: true` programmatically. Not green. Exact flip is for loop-build time. Exit: none left. JSON so the loop script reads and flips without parsing Markdown. |
| Loop implementation | Plain in-repo script, invoked synchronously in the live session — not a background daemon, not a graph framework. |
| Step definitions | Code in the worktree. Red finds them like execute finds source. No extra pointer. |
| Test runner | `black-sheep-testing-scaffold` in Stage 3. Until then, projects that already have a runner. |
| Black sheep membership | Audit output. Not named in advance. |
| Loop | red → green per unchecked scenario, then `sheep-green-refactor` → `sheep-red-refactor`, then review. |
| Review | Final verification, explicitly two jobs: full-suite **regression** check, and **scenario compliance** — every `done: true` scenario in `scenarios.json` actually satisfied. |
| Git tail | Inherited at fork, then independently maintained. |
| Lifecycle sheep | `sheep-start`, `sheep-status`, `sheep-close` are inherited unchanged, then independently maintained. Do not parameterize across repositories. |
| Ownership audit | Stage 1 removes same-repo namespacing work and records the fork boundary. Live map: [`OWNERSHIP.md`](OWNERSHIP.md). |

---

## Stage 1 — Nicki (also Shinobu's head)

Lives on **Nicki**. Shinobu copies this head later. No Shinobu agent yet.

### Spec first

`start → spec → gherkin → subtasks → execute → …`

- Nicki `routing.json`: `start` → `spec` → `gherkin` → `subtasks`. Gherkin prompt: spec path, not chat.
- `create-worktree.py:449` and `update-status.py:272`: opening / fallback `next_step` → `spec`.
- Smoke: `routing_next_step.py`, `status_vocabulary.py`, `harness_failure.py`. `routing_write.py` follows `default_next_step`.

### Gherkin is a transform

- `story-maker` reads spec, orders, splits on four `Then`s, no product `open_questions`.
- No interview language in `nicki.md`. Incomplete spec → `sheep-spec` again.
- Product questions stay on spec (`spec-maker` Step 2 / stop-and-ask). Supersedes #6 describe-asks.

### Names and artifacts

Live map: [`OWNERSHIP.md`](OWNERSHIP.md).

Do not prefix generic names for collision avoidance. Agents stay flat. Keep `sheep-start`, `sheep-status`, `sheep-close`, `sheep-subtask`, `sheep-execute`, `status.json`, `story.md`, `specs/`, `subtasks/`, and `global-status.json`.

Stage 1 still audits hardcoded Nicki paths so the fork boundary is explicit. Product-facing selector, routing, bootstrap environment, workspace/config/version filenames, and installer text change in the Shinobu fork.

### `story-format.md`

Scenario ids, dependency order, **`- [ ]` / `- [x]` per scenario**. Ids and checkboxes help Nicki subtasks follow order; Shinobu uses the same file shape as its loop cursor.

### Docs

Done this pass: `docs/NICKI.md`, `WORKFLOW-DIAGRAMS.md`, `status-read.md` / `status-format.md` (closes #13), task-list Shinobu/flexibility blurbs, `caller-owned-output-shape.md` sheep name. Live pipeline language is `start → spec → gherkin → subtasks → …` / `sheep-gherkin`.

---

## Stage 2 — fork, then Shinobu product

### First: create the repository

1. Tag the approved Nicki baseline after Stage 1, smoke CI, and task #20.
2. Clone it with full Git history into a sibling `shinobu/` folder.
3. Create the Shinobu remote and replace `origin`.
4. Change product-facing selector, orchestrator, routing/bootstrap, installer text, workspace/config/version names, and docs.
5. Keep ordinary sheep, skill, script, and artifact names; the repository is the namespace.

### Then: build Shinobu

- `workflow-runtime/agents/shinobu.md` — own pipeline. Shell: Shinobu bootstrap only. Loop packs the first `done: false` scenario from `scenarios.json` into red; after green succeeds, loop sets `done: true` (programmatic, not a sheep). Then `sheep-green-refactor`, then `sheep-red-refactor`. Two gates. Jump to `scenarios` to append; jump to spec if the spec is wrong.
- Shinobu routing: `start → spec → scenarios → red → …` loop-back while `scenarios.json` has a `done: false` scenario.
- Bootstrap reads only the Shinobu repository's routing and `status.json`.
- Lifecycle remains `sheep-start`, `sheep-status`, `sheep-close`.
- Parent rule: `shinobu …` → fresh `shinobu` Task.

### Loop

- Exit = no unchecked scenarios. Prove in smoke (`next_step_when_scenarios_remain` or equivalent reading the story artifact).
- Red errors: `open_questions` hold.
- No clock. Red and green run until they return.
- **One-shot job:** red and green each run **this scenario’s test once**, then return. `task: false`.
- Four skills + four sheep: `sheep-red`, `sheep-green`, `sheep-green-refactor`, `sheep-red-refactor`. Green does not edit the test or the story. Checklist flips belong to the loop.
- The two refactors are two ordinary sequential steps, each followed by its own `sheep-status`. No fork-and-join in routing, no aggregate status write.
- Review performs authoritative final verification: it runs the **whole** suite looking for regressions the refactors introduced, and checks every `done: true` scenario against the implementation.

Dogfood on a project that already has a runner.

---

## Stage 3 — black sheep

1. **Audit** — which sheep are ad-hoc-only. Then name them `black-sheep-*`.
2. **`black-sheep-testing-scaffold`** — runner + step-definition layout. Optional workspace-config fields when the schema work happens.

---

## Still open

| Question | Notes |
| -------- | ----- |
| Refactor scope | Define implementation-owned vs test-owned paths, including step definitions, fixtures/helpers, generated files, and shared utilities. Still needed although the refactors are now serial — each sheep must know what it may not touch. Do not settle this until the sheep are built. |

Black sheep membership is Stage 3's audit, not an open product question.

---

## Nicki backlog vs this path

Live list: [`tasks.md`](tasks/tasks.md).

### Do before the fork

| Item | Why |
| ---- | --- |
| **#20 host-runtime extract** | Before the repository fork, so the migration happens once. Canonical dir: `workflow-runtime/`. |
| **`shinobu-workspace.yaml` schema** | Later home for runner config (PLAN). |

Done and recorded in [`tasks/tasks-done.md`](tasks/tasks-done.md): Stage 1 behavior + docs, smoke CI, flexibility dogfood, #13. Ownership map: [`OWNERSHIP.md`](OWNERSHIP.md).

### Defer

Caller-owned output *shape* (all sheep). PLAN CLI, multi-project dogfood, AWS, evaluation harness/repository. Quoting polish (optional → `story-format.md`).

### Stop

Gherkin interview. One-repo/two-product runtime. Shared runtime package. Automatic Nicki→Shinobu merges. Rebuilding check-gate. Jump-past-spec as the happy path.

### Sequencing

1. ~~Stage 1 (Nicki behavior + docs) + smoke CI~~ — **done** ([`tasks-done.md`](tasks/tasks-done.md)).
2. #20: extract `workflow-runtime/`.
3. Tag Nicki baseline and create the sibling Shinobu repository with full history.
4. Stage 2: rename product-facing identity, then build the red-green loop + the two serial refactor steps.
5. Stage 3 (black sheep audit, then scaffold).

---

## Carry-overs (reuse, do not rebuild)

The fork carries spec, Gherkin, pause, output/archive paths, modes, stop-and-ask, lifecycle, git tail, fallback, worktree layout, registry, host adapters, and smokes. They become independent copies immediately after the fork.
