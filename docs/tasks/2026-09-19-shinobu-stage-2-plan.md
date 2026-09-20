# Shinobu Stage 2 — build plan

**Status:** live plan. Owner of this file and of [`tasks.md`](tasks.md) is the architect session; worker sessions flip one row and nothing else.

**Reads:** [`SHINOBU_NEXT_STEPS.md`](../SHINOBU_NEXT_STEPS.md) (the "Settled — do not reopen" table is binding) · [`SHINOBU.md`](../SHINOBU.md) · [`OWNERSHIP.md`](../OWNERSHIP.md) · [`2026-09-19-runtime-extract-and-delivery-options.md`](2026-09-19-runtime-extract-and-delivery-options.md)

**Where we are:** this repository is a history-preserving clone of Nicki at `v0.3.0-nicki-baseline`, `origin` already pointed at `MiltonCastilloG/shinobu`. `python3 test.py` is green on 15 smoke modules. Nothing Shinobu-specific exists yet.

---

## 1. Constraints this plan is built on

Restated so a worker prompt can cite them, not to reopen them.

| | Binding rule |
| - | ------------ |
| Namespace | The repository is the namespace. Agents flat under `workflow-runtime/agents/`, filename == frontmatter `name:`. Skills exactly one level: `workflow-runtime/skills/<name>/SKILL.md`. |
| Generic names stay | `sheep-start`, `sheep-status`, `sheep-close`, `status.json`, `story.md`, `specs/`. No product suffixes. |
| Only the selector moves | `nicki` → `shinobu` for the orchestrator agent, its rule, its routing/bootstrap folder, and product-facing config filenames. |
| No sharing | No shared runtime package, no Nicki↔Shinobu sync, no `--pipeline` flag. |
| Loop | Plain in-repo script, invoked synchronously in the live session. Not a daemon, not a graph framework. The loop marks `- [x]`; green never does. |
| Consent | Exactly two: before the first red, after review. |
| Story artifact | `current-task/scenarios.json`: ordered array of `{ id, title, gherkin, done }`. The loop reads the first `done: false`, flips `done` after green. Replaces the `- [ ]` Markdown checklist (owner's call, S2a). |
| Red | Input is one packed scenario object from `scenarios.json` (id, title, gherkin). Success = fails right. Anything else → `open_questions`, loop holds. |
| Green | Input is the git diff only. Never edits the test or the story. |
| The four new sheep | `sheep-red`, `sheep-green`, `sheep-green-refactor`, `sheep-red-refactor`. |
| Refactors are **serial** | `sheep-green-refactor` (implementation) on the post-loop diff, then `sheep-red-refactor` (tests) on the diff that leaves. Each is an ordinary step with its own `sheep-status`. No fork-and-join anywhere. **Exact file scope stays OPEN until those sheep are built (S3b), not decided here.** |
| Review | Two explicit jobs: full-suite **regression** check, and **scenario compliance** — every `- [x]` in `story.md` actually satisfied. |
| Editing | Edit `workflow-runtime/`, never through `.cursor/` or `.claude/`. After changing the invocation rule, run both installers and commit the regenerated `.mdc`. |

---

## 2. Job graph

```text
S1  identity rename
 │
S2  remove the Nicki tail
 │
S2a scenarios.json — gherkin writes an ordered scenario array
 │
 ├──────────┬──────────┐
S3a red     S3b        S3c review              ← parallel, disjoint write domains
    +green  refactors  hardening
 └──────────┴──────────┘
 │
S4  loop + routing + status + permissions wiring     ← serial, owns every shared file
 │
 ├──────────────┐
S5  smokes      S7 docs                        ← parallel, disjoint write domains
 └──────────────┘
 │
S6  dogfood (human-run checklist)
```

| Group | Jobs | Run |
| ----- | ---- | --- |
| A | S1 | one worker |
| B | S2, then S2a | one worker each, serial |
| C | S3a, S3b, S3c | **three workers in parallel** |
| D | S4 | one worker |
| E | S5, S7 | **two workers in parallel** |
| F | S6 | human, from a checklist I write |

**Why S1 before S2**, although deleting first would shrink S1's grep inventory: the overlap is seven string hits in five files that S2 deletes, and a mechanical rename on a green, unmodified baseline is the cleanest bisect point we will ever get. S1 simply skips those five paths.

**Why S5 is not written alongside S4**, although it could be: its assertions encode S4's exact routing keys and status shape. Writing them against a guess costs more churn than it saves wall-clock.

---

## 3. Write domains

The authority for "can these two run at once". A worker may create/modify/delete only inside its own domain.

| Path | S1 | S2 | S3a | S3b | S3c | S4 | S5 | S7 |
| ---- | -- | -- | --- | --- | --- | -- | -- | -- |
| `workflow-runtime/agents/shinobu.md` | ✎ | ✎ | — | — | — | ✎ | — | — |
| `workflow-runtime/agents/sheep-red.md`, `sheep-green.md` | — | — | **✎** | — | — | — | — | — |
| `workflow-runtime/agents/sheep-green-refactor.md`, `sheep-red-refactor.md` | — | — | — | **✎** | — | — | — | — |
| `workflow-runtime/agents/sheep-subtask.md`, `sheep-execute.md` | — | ✗ | — | — | — | — | — | — |
| other `workflow-runtime/agents/sheep-*.md` | ✎ | — | — | — | — | — | — | — |
| `workflow-runtime/skills/red-implementation/**`, `green-implementation/**` | — | — | **✎** | — | — | — | — | — |
| `workflow-runtime/skills/green-refactor/**`, `red-refactor/**` | — | — | — | **✎** | — | — | — | — |
| `workflow-runtime/skills/review-execution/**`, `agents/sheep-review.md` | ✎ | **✎** | — | — | **✎** | — | — | — |
| `workflow-runtime/skills/subtask-maker/**`, `execute-plan/**`, `validation/**` | — | ✗ | — | — | — | — | — | — |
| `workflow-runtime/skills/shinobu/routing.json` | ✎ | ✎ | — | — | — | ✎ | — | — |
| `workflow-runtime/skills/shinobu/scripts/**` | ✎ | — | — | — | — | ✎ | — | — |
| other `workflow-runtime/skills/**` | ✎ | ✎ | — | — | — | — | — | — |
| `.cursor/hooks/agent-permissions.json`, `.cursor/permissions.json` | ✎ | ✎ | — | — | — | ✎ | — | — |
| `workflow-runtime/rules/shinobu-default.md` (+ regenerated `.mdc`, `CLAUDE.md`) | ✎ | ✎ | — | — | — | ✎ | — | — |
| `install*.py`, `.gitignore`, root config files | ✎ | — | — | — | — | — | — | — |
| `tests/smoke/**`, `test.py` | ✎ | ✎ | — | — | — | — | ✎ | — |
| `README.md`, `docs/**` (except `tasks.md`) | ✎ (README only) | ✎ (README pipeline line only) | — | — | — | — | — | ✎ |
| `docs/tasks/tasks.md` | row flip only | row flip only | row flip only | row flip only | row flip only | row flip only | row flip only | row flip only |

✎ = may edit · ✗ = deletes · — = must not touch.

**S2a is serial and has no column.** It touches `skills/scenario-maker/**`, `agents/sheep-scenarios.md`, the `scenarios` entry in `routing.json`, the story path in `shinobu.md`, `task-archive/**`, the current-task-update docs, `start-task` / `close-*` SKILL prose, fixtures, the smokes that name `story.md`, and README's two story lines. It runs alone between S2 and Group C, so nothing it touches is contested.

**S2 and S3c share `review-execution/` and `sheep-review.md`, and that is safe** because they are sequential, not parallel: S2 finishes before Group C starts. S2 removes the dead subtask/execute references (they are part of the tail it exists to remove); S3c then adds the regression and scenario-compliance duties. Leaving dangling references for a job two steps away would be worse than sharing a file across two serial jobs.

**Group C disjointness proof.** S3a's domain is four paths: `agents/sheep-red.md`, `agents/sheep-green.md`, `skills/red-implementation/`, `skills/green-implementation/`. S3b's is four: `agents/sheep-green-refactor.md`, `agents/sheep-red-refactor.md`, `skills/green-refactor/`, `skills/red-refactor/`. S3c's is two: `agents/sheep-review.md`, `skills/review-execution/`. Pairwise intersection is empty. Every file more than one of them would otherwise want — `routing.json`, `shinobu.md`, `agent-permissions.json`, `permissions.json`, the smokes — is deferred to S4, which is serial. S3a and S3b create files only; S3c is the only one of the three that modifies an existing file, and no other job in the group reads it.

**Group E disjointness proof.** S5's domain is `tests/smoke/**` + `test.py`. S7's is `README.md` + `docs/**` minus `tasks.md`. Disjoint, and no smoke module reads `README.md` or `docs/` (`path_resolution.py` scans `workflow-runtime/` markdown, `routing.json`, `.cursor/permissions.json`, `.cursor/hooks.json` — nothing under `docs/`).

---

## 4. Jobs

### S1 — Identity rename

One mechanical PR. `git grep -n -i nicki` is the inventory; every hit is classified as **rename** (product identity), **leave — history** (`docs/archive/**`, `docs/tasks/**`, `.cursor/hooks/state/sessions.json`), **leave — S7** (the doc set), or **leave — S2 deletes it**.

Renames: `agents/nicki.md` → `shinobu.md`, `rules/nicki-default.md` → `shinobu-default.md`, `skills/nicki/` → `skills/shinobu/`, `nicki-workspace.example.yaml` → `shinobu-workspace.example.yaml` (self key `nicki:` → `shinobu:`), `nicki.code-workspace` → `shinobu.code-workspace`, `nicki_version.yaml` → `shinobu_version.yaml`, `.cursor/rules/nicki-default.mdc` → `shinobu-default.mdc` (regenerated, committed), plus both bootstrap fixtures' registry filenames.

Machine-read strings that must flip in the same commit: `routing.json` `harness_failure.scripts[*].route`, `routing_write.py`'s hardcoded `"nicki"/routing.json`, `bootstrap_utils.py`'s `NICKI_WORKSPACE_ROOT` and its `nicki-workspace.example.yaml` workspace-root marker, `create-worktree.py`'s marker tuple / `load_registry` / `--project` self-project id, `.cursor/permissions.json` allowlist prefix, `.cursor/hooks/agent-permissions.json` key, `.gitignore` registry filename, `install_common.py` `INVOCATION_RULE` + substitution table, `install.py` `REGISTRY_PATH`/`CURSOR_RULE`/`REGISTRY_STUB`, and the eleven smoke modules that name any of the above.

**One non-mechanical addition, deliberately in scope:** `create-worktree.py:load_registry()` silently falls back to the `.example.yaml` when the live registry is absent. After S1 the human's live `nicki-workspace.yaml` no longer matches the new name, so that fallback would quietly hand the pipeline a registry full of `your-org` placeholder remotes. Add a stderr warning on the fallback branch. Three lines; it converts the one silent failure S1 creates into a loud one.

**Done when:** `python3 test.py` green (`path_resolution` and `rule_drift` are the net) · fresh clone into a scratch dir + `python3 install.py` succeeds and both host dirs resolve · `git worktree add` from the clone yields working `.cursor/agents` and `.cursor/skills` · `git grep -i nicki` returns hits **only** in `docs/archive/**`, `docs/*.md`, `docs/tasks/**`, `.cursor/hooks/state/sessions.json`, and the five files S2 deletes · `shinobu` is the invocation word in the generated `CLAUDE.md` and `.cursor/rules/shinobu-default.mdc`, both regenerated by running the installer, the `.mdc` committed, the old one `git rm`'d.

**Ends with a manual step for the human** — the live registry is gitignored, so no worker may touch it: `mv nicki-workspace.yaml shinobu-workspace.yaml`, then edit the self-project key `nicki:` → `shinobu:`. Recorded in `tasks.md` as well as in the S1 prompt.

**Model:** Opus 5. It is wide but mechanical, and a green test suite covers most of it — yet it is the foundation every later job inherits, and it carries four traps a fast pass will miss: the `bootstrap_utils` marker filename, the installers-then-commit ordering that `rule_drift` enforces, the `.gitignore` flip that un-ignores the human's live file, and the fixture registry names.

### S2 — Remove the Nicki tail

Delete `sheep-subtask.md`, `sheep-execute.md`, `skills/subtask-maker/`, `skills/execute-plan/`, `skills/validation/` (already retired per `OWNERSHIP.md`). Remove the `subtasks`, `execute`, and `fix` steps from `routing.json` and leave `scenarios → review` so the graph terminates — **not** `red`, which does not exist yet. Strip `current-task/subtasks/` scaffolding from `create-worktree.py`, subtask/execute language from `shinobu.md` and the current-task-update docs, and the matching keys from `agent-permissions.json`.

Expect to rewrite, not merely edit: `routing_next_step.py`, `routing_write.py` (its `artifact_key` set assertion names `subtasks`), `jump_mode.py`, `readiness_mapping.py`, `status_vocabulary.py`.

**Done when:** `python3 test.py` green · routing resolves start → … → done with no dangling step · `git grep -n "subtask\|execute-plan\|sheep-execute"` returns nothing outside `docs/archive/**` and `docs/tasks/**`.

**Model:** Opus 5 — the routing/smoke rewrite is judgement, not substitution.

### S2a — `scenarios.json`, and one name at every level

Two changes in one job, because they touch the same files and the second is what makes the first coherent:

**1. Format.** `sheep-gherkin` stops writing a Markdown checklist and writes a JSON scenario array:

```json
{
  "meta": { "schema": "scenarios.v1" },
  "feature": { "title": "…", "as_a": "…", "i_want": "…", "so_that": "…" },
  "scenarios": [
    { "id": "hero-headline", "title": "Headline is visible above the fold",
      "gherkin": "Scenario: Headline is visible above the fold\n  Given …\n  When …\n  Then …",
      "done": false }
  ]
}
```

Array order is dependency order. `id` is stable kebab-case, unique, never reused, never changed once `done: true`. `gherkin` is one string — the full `Scenario:` block — so red can drop it into a feature file unchanged. Every rule in today's `story-format.md` survives the format change: split on two sentences / goal-shaped / more than four `Then`s, order after splitting, no product questions, amend appends and never rewrites a done entry.

**2. Name.** The artifact is a list of scenarios; Gherkin is the syntax it holds. So one word at every level, owner's call:

| Level | Was | Becomes |
| ----- | --- | ------- |
| routing step | `gherkin` | `scenarios` |
| sheep | `sheep-gherkin` | `sheep-scenarios` |
| skill | `story-maker/` (`story-format.md`) | `scenario-maker/` (`scenario-format.md`) |
| file | `current-task/story.md` | `current-task/scenarios.json` |
| status key | `artifacts.story` | `artifacts.scenarios` |

Why now, and why its own job: S3a's red packs one object from this file and S4's loop reads and flips it. Settling the schema *and* the names in real files before building two consumers beats defining them twice in prompts. Serial, alone, before Group C.

**Files:** the skill folder (`git mv`), the sheep file (`git mv` + frontmatter `name:`), `routing.json` (`spec.default_next_step`, the step key, its `sheep` and `artifact_key`, its prompt), `shinobu.md`, `rules/shinobu-default.md` (+ regenerated `.mdc` and `CLAUDE.md`), `.cursor/hooks/agent-permissions.json` key, `task-archive/**`, `current-task-update/*.md`, `start-task` / `close-*` / `spec-maker` SKILL prose, the bootstrap fixture `status.json`, every smoke naming `gherkin` / `story`, README.

**Done when:** `python3 test.py` green · `git grep -nE "story\.md|story-maker|sheep-gherkin|artifacts\.story"` and a routing-step grep for `"gherkin"` return nothing outside `docs/archive/**`, `docs/tasks/**`, and the banner-ed baseline docs · agent files ↔ permission keys a bijection · routing chain is `start → spec → scenarios → review → …` · the example in `scenario-format.md` parses as JSON · every carried-over rule is findable by name · `task-archive` names `scenarios.json`.

**Model:** Opus 5 — the rename is mechanical; keeping the split / order / amend rules exactly as strong through the rewrite is judgement.

### S3a — `sheep-red` + `sheep-green`

Two agent files and two skills: `skills/red-implementation/SKILL.md`, `skills/green-implementation/SKILL.md`. Red takes one packed scenario (id + body) and the worktree, writes/extends step definitions, runs that scenario's test **once**, returns `task: false`; success is exactly "fails right", everything else is `open_questions`. Green takes the git diff only, makes the smallest change that passes, never touches the test or `story.md`. Both follow the existing sheep return contract in `routing.json`.

**Files:** the four listed above. Nothing else — no routing, no `shinobu.md`, no permissions, no tests.

**Done when:** both agents' filename == frontmatter `name:` · both skills are exactly one level with a `SKILL.md` · every path string in the four files resolves · `python3 test.py` green (nothing wired yet, so this is a regression check) · the return-JSON shape each sheep documents matches `routing.json`'s `sheep_return_contract`.

**Model:** Opus 5.

### S3b — `sheep-green-refactor` + `sheep-red-refactor`

Two agent files and two skills: `skills/green-refactor/`, `skills/red-refactor/`.

`sheep-green-refactor` runs **first**, on the post-loop diff, and revises implementation only. `sheep-red-refactor` runs **second**, on the diff that green-refactor leaves, and revises tests only without changing scenario meaning. Serial, each an ordinary step with its own `sheep-status` after it. Each SKILL.md must say plainly that it runs after/before the other and what it reads.

**This job settles the one genuinely open product question.** Each SKILL.md states its own write domain explicitly and names what it does when the diff touches a file it does not own (leave it, and say so in `summary`). Serial execution removes the *concurrency* hazard but not the need for domains — red-refactor must not quietly undo green-refactor's work, and neither owns step definitions, fixtures/helpers, generated files, or shared utilities until this job says who does. The worker returns the proposed boundary to me; I put it to the human before S4 wires the pair.

**Files:** the four listed above. Same exclusions as S3a.

**Done when:** as S3a, plus: the two SKILL.md write domains are stated, are disjoint by construction, and together cover every path class named above — with "unowned, left alone" an allowed answer · each names its position in the order and its input diff.

**Model:** Opus 5.

### S3c — Review hardening

`sheep-review` and `skills/review-execution/` gain two explicit duties, and the prompt says they are duties, not suggestions:

1. **Regressions** — run the whole suite, not only this task's scenarios, and report anything that broke. This is the step that catches a refactor which quietly changed behaviour.
2. **Scenario compliance** — every `- [x]` line in `story.md` is actually satisfied by the implementation. A checked box that the loop flipped is a claim, not evidence.

Keep everything review already does. Review still writes nothing but its return, and still routes its verdict through `summary`.

Also drop `review-execution/review-guidance-format.md`'s hardcoded `current-task/review-inputs/rN-review.json` default. Its writer was the retired `validation/` skill (deleted in S2); nothing produces it, routing packs no path for it, and `status-format.md` forbids a pointer to it. Found by the S2 worker, correctly left for this job.

**Files:** `workflow-runtime/agents/sheep-review.md`, `workflow-runtime/skills/review-execution/**`. Nothing else.

**Done when:** both duties are stated in the skill and reflected in the agent's disk-inputs and return shape · `python3 test.py` green · the return shape still matches what `update-status.py` expects from a review step (`summary.next_step` override still works).

**Model:** Sonnet 5 — the shape is fixed and the change is additive and well specified.

### S4 — Loop, routing, status, permissions

Serial, and the only job that touches shared files.

- `shinobu.md`: the loop as a plain in-repo script invoked synchronously — pick the first `- [ ]` in `story.md`, pack it into red, run green on the diff, mark `- [x]`, repeat. Exit when none remain. Two consents, no clock, no polling between red and green.
- `routing.json`: `start → spec → scenarios → red → green → …` with loop-back while the story has `- [ ]`, then `green-refactor → red-refactor → review → git tail`. Four ordinary steps; no fork-and-join, no aggregate status write.
- `.cursor/hooks/agent-permissions.json`: the four new agent keys. `.cursor/permissions.json`: any new allowlist prefix the loop script needs.
- Red returning `open_questions` holds the loop and holds `next_step`.
- The human gate after gherkin: Shinobu renders `scenarios.json`'s scenarios in chat (id, title, gherkin) for approval. The human never reads the JSON raw.

**Done when:** `python3 test.py` green · routing graph terminates at `done` · a hand-run of the loop script against a fixture `story.md` with two unchecked scenarios flips exactly one box per successful green and stops when the file is clear · `green-refactor` precedes `red-refactor` in routing and each has its own status step · every new path string resolves.

**Model:** Opus 5.

### S5 — Shinobu smokes

New modules registered in `test.py`: loop cursor behaviour while scenarios remain and on exit, red-failure `open_questions` hold, refactor step order (`green-refactor` → `red-refactor`, each followed by status), and the routing assertions S2 deferred. Prefer reading `scenarios.json` directly over asserting on prose.

**Done when:** `python3 test.py` green with the new modules listed · each new module fails when its behaviour is reverted (prove it once, by hand).

**Model:** Sonnet 5 — the contract is fixed by S4; this is careful test-writing against a known shape.

### S7 — Docs

`README.md` pipeline section and layout tree, `docs/NICKI.md` → the Shinobu runtime semantics doc, `docs/WORKFLOW-DIAGRAMS.md`, and an `OWNERSHIP.md` pass that flips the fork-action column to what actually shipped. `docs/archive/**` stays untouched — it is history.

S1 leaves these files alone on purpose, so between S1 and S7 they describe an inherited baseline that is no longer live. S1 adds a one-line banner to `NICKI.md` and `WORKFLOW-DIAGRAMS.md` saying so, so the staleness is never silent.

**Done when:** `git grep -i nicki` outside `docs/archive/**` and `docs/tasks/**` returns nothing · the pipeline drawn in the docs matches `routing.json` step for step.

**Model:** Sonnet 5.

### S6 — Dogfood

Human-gated. Run Shinobu on a managed clone that already has a test runner — `projects/tetris-clone-frp` is the candidate; `projects/castlemill-landing` and `projects/project-jung` are the fallbacks. I write the checklist after S5; the human runs it. This is the only end-to-end proof that exists: CI is a structural gate, never a behavioural one.

---

## 5. Working pattern

- One worker session per job. Every prompt carries: scope, explicit non-scope, the file list it may touch, done-when, and `python3 test.py`.
- I own `tasks.md`. A worker flips its own row at the end and edits nothing else in that file. Two workers never hold it at once — in Group C and Group E, the rows are distinct lines and the workers are told to `git pull --rebase` before the flip.
- After each job I audit before the next starts: read the diff, run `test.py`, and where the job touches install or layout, a fresh clone + `python3 install.py` + a real `git worktree add`. Findings are ranked and labelled "worker missed it" or "my prompt was wrong".
- **A fresh-clone check needs a commit first.** `git clone` takes `HEAD`, so cloning a tree with uncommitted work validates the *pre-job* state and proves nothing. S1's prompt asked for both and contradicted itself. From S2 on, worker prompts say: make a local commit (never push), then clone and verify.
- **`install.py` writes a registry stub when none exists.** Any prompt that tells a worker to run it must say so, or the worker silently manufactures a one-project `shinobu-workspace.yaml` that shadows the human's live registry.
- Machine-read strings (executed commands, smoke asserts, allowlist prefixes, routing routes) flip in the same commit as the change they depend on. Prose may lag by a job, but only where a banner says it is lagging.
- Smallest reversible slice. If a job drags, cut scope and record the cut in `tasks.md` rather than letting it sprawl.

---

## 6. Decisions I made that a human can cheaply reverse

| Decision | Default taken | Reverse cost |
| -------- | ------------- | ------------ |
| Skill folder names behind the four sheep | `red-implementation`, `green-implementation`, `red-refactor`, `green-refactor` — owner's call. Red *adds code* (step definitions plus a failing test); a name with "test" in it reads as if the skill runs tests, so both loop skills say `implementation` and the colour carries the meaning. | S3 only; rename a folder |
| `shinobu_version.yaml` starts at | `0.1.0` — new product, its own numbering, rather than inheriting Nicki's `0.3.0` | one line |
| S2 points `scenarios` at `review` | keeps the graph terminating between S2 and S4 instead of naming a step that does not exist | one line in S4 |
| S1 leaves the doc set to S7, with a banner | avoids rewriting docs twice, and the banner keeps the staleness visible | — |
| `create-worktree.py` fallback warning | in S1's scope although it is not a rename | three lines |
| Review hardening is its own job (S3c), in Group C | its files are disjoint from S3a and S3b, and it does not depend on S4's routing — so it costs no serial time | fold into S4 |

## 7. Genuinely open

| Question | When it must be answered |
| -------- | ------------------------ |
| Refactor write domains — implementation-owned vs test-owned paths, including step definitions, fixtures/helpers, generated files, shared utilities. Serial execution removed the concurrency hazard, not the need for the boundary | S3b proposes; human decides at the S3b audit, before S4 wires the pair. Settled nowhere before then, by design. |
| Which managed project S6 dogfoods on | Before S6. Needs a project that already has a runner. |

---

## 8. Changed after the first draft

Recorded so a worker who read an earlier copy is not misled.

| Was | Now | Why |
| --- | --- | --- |
| `sheep-test-refactor`, `sheep-implementation-refactor` | `sheep-green-refactor` (implementation), `sheep-red-refactor` (tests) | Owner's call. Shorter, and the red/green vocabulary is already the pipeline's. |
| Refactor pair runs **in parallel** with disjoint write domains; routing needs fork-and-join; one aggregate status write | **Serial**: green-refactor, then red-refactor. Two ordinary steps, each with its own `sheep-status`. No fork-and-join. | Owner's call: concurrent mutation of implementation and tests lets one refactor mask the other's regression. Sequencing tests last means they are tidied against implementation that has already settled. |
| Review described only as "authoritative final verification" | Review has two named duties: full-suite regression check, and scenario compliance against every `- [x]` | Owner's call. With refactors now running after the loop, review is the only thing standing between a silent behaviour change and the git tail. |

`SHINOBU.md`, `SHINOBU_NEXT_STEPS.md` (including the settled table), and `OWNERSHIP.md` were updated to match. S1's scope and prompt are unaffected by all three changes.
