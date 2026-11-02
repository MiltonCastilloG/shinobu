# Orchestrator handoff — Shinobu Stage 2

**For:** whoever picks up the architect/orchestrator role next. You plan, write worker prompts, audit results, and keep `tasks.md` current. You do not implement — see the role brief below, which is unchanged from the original.

**As of:** 2026-11-02, commit `702de4f`, tree clean, `python3 test.py` green on 15 smoke modules.

---

## Read first, in this order

1. This file.
2. [`docs/tasks/2026-09-19-shinobu-stage-2-plan.md`](2026-09-19-shinobu-stage-2-plan.md) — the live job graph, write-domain table, per-job scope and done-when. Its "Where we are" line at the top is kept current; trust it over this handoff if they ever disagree.
3. [`docs/tasks/tasks.md`](tasks.md) — the row table. Status column is ground truth for what's done vs next.
4. [`docs/tasks/tasks-done.md`](tasks-done.md) — Stage 2 section at the top records what each landed job actually did and what its audit found. Read S1/S2/S2a's entries before touching anything near them.
5. [`docs/SHINOBU.md`](../SHINOBU.md) and [`docs/SHINOBU_NEXT_STEPS.md`](../SHINOBU_NEXT_STEPS.md) — destination behaviour and the "Settled — do not reopen" table. Both are kept current through S2a (scenario naming, serial refactors, review's two duties are already reflected).
6. [`docs/OWNERSHIP.md`](../OWNERSHIP.md) — per-file fork ownership. Still describes the pre-Stage-2 target layout in places; S7 corrects it.

Do **not** re-read `docs/NICKI.md`, `docs/WORKFLOW-DIAGRAMS.md`, or `docs/PLAN.md` for current behaviour — they carry a banner marking them stale baseline, rewritten by S7.

---

## Role brief (unchanged)

You are the architect/orchestrator. You do NOT implement. You plan, write prompts for worker sessions, audit their results, and keep `docs/tasks/tasks.md` current.

**Hard constraints, settled, do not relitigate** (full detail in `SHINOBU_NEXT_STEPS.md`'s table):
- Repository is the namespace. Agents flat under `workflow-runtime/agents/`, filename == frontmatter `name:`. Skills exactly one level.
- Generic names stay generic: `sheep-start`, `sheep-status`, `sheep-close`, `status.json`.
- Only the product selector/orchestrator changed (`nicki` → `shinobu`, done in S1).
- No shared runtime package, no Nicki↔Shinobu sync, no product-suffixed names, no `--pipeline` flag.
- Loop is a plain in-repo script invoked synchronously in the live session — not a daemon, not a graph framework.
- Two consents only: before first red, after review.
- Red input = one packed scenario object from `scenarios.json`; success = fails right.
- Green input = git diff only; never edits the test or `scenarios.json`.
- **Refactors are serial**, not parallel: `sheep-green-refactor` (implementation) on the post-loop diff, then `sheep-red-refactor` (tests) on what it leaves. Each is an ordinary step with its own `sheep-status`. (Changed from the original "parallel with disjoint domains" plan — see `tasks.md`'s Group C row and `2026-09-19-shinobu-stage-2-plan.md` §8 for why.)
- **Review has two named duties**: full-suite regression check, and scenario compliance — every `done: true` entry in `scenarios.json` actually satisfied. S3c is building this now.
- Edit `workflow-runtime/`, never through `.cursor/` or `.claude/`. After changing the invocation rule, run `python3 install.py` (single installer now — `install-claude.py` was deleted in a pre-S1 commit) and commit the regenerated `.mdc`.

**Working pattern:**
- One worker session per job. Every prompt: scope, explicit non-scope, exact file list, done-when, "run `python3 test.py`", a model recommendation.
- You own `tasks.md`. Workers flip only their own row, at the very end, after `git pull --rebase` if another job landed concurrently.
- **Audit before the next job starts — always, not optionally.** Read the diff yourself, re-run `test.py`, and for anything touching install/layout: fresh clone in a scratch dir + `python3 install.py` + a real `git worktree add`. Do not take a worker's self-report at face value — verify independently, the way every prior audit in this session did. This has caught real things every single time so far (see "What auditing has actually caught" below).
- Rank findings; say whether it was "worker missed it" or "my prompt was wrong." Both happen often — own the second one in the record, don't just note the first.
- Machine-read strings (routing, smoke asserts, permission keys, allowlist prefixes) must flip in the same commit as the behavior they depend on. A worker who defers this is wrong even if tests still pass by accident.
- Smallest reversible slice. If a job drags, cut scope and record the cut in `tasks.md`.
- **Fresh-clone checks need a commit first.** `git clone` takes `HEAD`; cloning a tree with uncommitted work validates the *pre-job* state and proves nothing. Every worker prompt from S2 onward says: commit locally (never push), then clone and verify. Keep doing this.
- `python3 install.py` writes a one-project `shinobu-workspace.yaml` stub whenever that file is absent. The human's real registry exists, is gitignored, and must never be shadowed by that stub. Any prompt that has a worker run `install.py` must warn about this; if a worker's fresh-clone check is in a true scratch dir (no real registry present), the stub there is fine and expected — it's only a problem inside *this* checkout.

---

## Current state of the job graph

```
S1  identity rename                              done  (72748ce)
S2  remove the Nicki tail                        done  (5478d3a)
S2a scenarios.json + one name at every level      done  (5bbf848, + follow-up 0eab38d)
 │
 ├─────────────┬─────────────┐
S3a red+green  S3b refactors S3c review          ← NEXT. Three workers, parallel.
 └─────────────┴─────────────┘
 │
S4  loop + routing + status + permissions         serial, depends on all of S3
 │
 ├──────────────┐
S5  smokes      S7 docs                          parallel, depends on S4
 └──────────────┘
 │
S6  dogfood                                       human-gated, depends on S5
```

**Routing today:** `start → spec → scenarios → review → acceptance → sync → archive → sync → integrate → close → done`. The `scenarios → review` edge is a deliberate placeholder (S2's doing) — S4 repoints it through `red`/`green`'s loop-back. Don't be alarmed that it currently skips straight from writing scenarios to review; nothing is broken, that's the state between S2 and S4 by design.

**Immediately next: write the prompts for S3a, S3b, S3c and run them in parallel.** Their write domains are proven disjoint in the plan's §3 table. None of the three depend on each other; all three depend only on S2a (done).

### S3a — `sheep-red` + `sheep-green`
New sheep + skills (`red-implementation`, `green-implementation` — named to avoid "test" sounding like it *runs* tests when it actually *writes* them; see plan §6). Red takes one packed scenario object (id, title, gherkin) + worktree, writes/extends step definitions, runs that scenario's test once, returns `task: false`; success is exactly "fails right". Green takes the git diff only, makes the smallest change that passes, never touches the test or `scenarios.json`. No routing, no `shinobu.md`, no permissions wiring — purely new, isolated files.

### S3b — `sheep-green-refactor` + `sheep-red-refactor`
New sheep + skills (`green-refactor`, `red-refactor`). Serial at runtime: green-refactor (implementation) on the post-loop diff first, then red-refactor (tests) on what it leaves. **This job settles the one genuinely open product question**: implementation-owned vs test-owned file paths — step definitions, fixtures/helpers, generated files, shared utilities. Each SKILL.md must state its own write domain explicitly, with "unowned, left alone" as a valid answer. The worker proposes; **you bring the proposed boundary to the human before S4 wires the pair.** Do not let S4 start until that's confirmed.

### S3c — Review hardening
`sheep-review` + `review-execution/` gain two named duties: full-suite regression check (not just this task's scenarios), and scenario compliance (every `done: true` in `scenarios.json` actually satisfied, not just claimed). This is additive to what review already does — don't redesign the rest of it. Also: drop `review-execution/review-guidance-format.md`'s hardcoded `current-task/review-inputs/rN-review.json` default — found during S2's audit, its writer (`validation/`) was deleted, nothing produces that path anymore, and `status-format.md` already forbids pointing at it.

**Why these three can run in parallel:** proven disjoint in the plan — S3a touches 4 files, S3b touches 4 files, S3c touches `sheep-review.md` + `review-execution/`. Zero overlap. Everything any of them might otherwise contest (`routing.json`, `shinobu.md`, `agent-permissions.json`, the smokes) is deliberately deferred to S4, which is serial.

---

## What auditing has actually caught (so you know what to look for)

This isn't hypothetical — every job so far has had something a fresh-eyes check found that the worker's self-report didn't surface, or that the prompt itself got wrong:

- **S1:** a worker reasonably ran both "don't commit" and "fresh clone to verify" in the same prompt — contradictory, since `git clone` takes `HEAD`. Fixed the template for every job after.
- **S1:** `install.py`'s registry-stub-on-absence behavior would have silently shadowed the human's real workspace registry if a worker ran it twice during verification. Added an explicit warning requirement to every subsequent prompt.
- **S2:** the write-domain table had a real gap — `workflow-runtime/rules/shinobu-default.md` wasn't listed as anyone's domain, yet S1 and S2 both needed to touch it. Patched the table, not papered over.
- **S2:** README had leftover `sheep-execute`/`sheep-subtask` references at five places because the prompt said "one line only" — too narrow a non-scope carve-out. That's a prompt-writing mistake, recorded as mine, not the worker's.
- **S2a:** a hardcoded `"gherkin"` step-name literal in `harness_failure.py` wasn't in the prompt's smoke list — caught because the prompt's own done-when check (grep classifying every remaining use of the word) was broad enough to catch what the scope list missed. That's the pattern to keep: make done-when checks structural (grep the whole surface, classify every hit) rather than a checklist of files you already thought of.
- **S2a audit (this session):** a deprecated, unreferenced-except-by-one-link schema file (`current-task-context-format.md`) had an unrelated `task.story` field that *looked* like it was part of the rename surface and wasn't — it had already cost one worker a judgment call. Deleted it outright rather than let it cost the next three workers the same call.

**Takeaway:** assume every worker prompt has at least one gap. The fix is never "trust the self-report harder" — it's independent verification (re-run the suite yourself, re-run the grep yourself, do the fresh clone yourself) plus noticing when the *prompt* was the problem and fixing the template, not just the instance.

---

## Decisions made along the way that are cheap to reverse

| Decision | What | Reverse cost |
|---|---|---|
| Refactor sheep run **serially**, not in parallel | User's call, mid-Stage-2: concurrent implementation+test refactoring let one mask the other's regression | Would require re-adding fork-join to routing/status — S3b/S4 not built yet, so free right now |
| Review has two **named** duties (regression + scenario compliance) | User's call, same conversation turn as above | S3c is building this now; cheap while unbuilt |
| Skill names: `red-implementation`/`green-implementation` not `red-test`/`green-implementation` | User's call — "test" sounds like it runs tests, not writes them | Folder rename only, S3a not built yet |
| Story artifact renamed `scenarios.json`, one name at every level (step/sheep/skill/file/key all say "scenarios") | User's call: Gherkin is the *format*, scenarios is the *content* | Done (S2a); reversing now means re-touching ~20 files |
| `scenarios → review` placeholder edge in routing | Architect's call, to keep the graph terminating between S2 and S4 | One line, in S4 |
| `shinobu_version.yaml` starts at `0.1.0` not inherited `0.3.0` | Architect's call — new product, own numbering | One line |

---

## Genuinely open — needs a human decision, not yours to make

1. **Refactor write domains** (implementation-owned vs test-owned paths, including step definitions/fixtures/generated files/shared utilities). S3b proposes it. **You must put it to the human before S4 wires the pair.** This is the one item explicitly flagged as not-yet-settled in `SHINOBU_NEXT_STEPS.md`'s "Still open" table.
2. **Which managed project S6 dogfoods on.** Needs a project with an existing test runner. `projects/tetris-clone-frp` looked likeliest as of the original plan (it has a partial `.cursor/` already) but confirm it still has a runner before committing to it.

Nothing else is open. If you find yourself about to make a product call that isn't in this list or isn't clearly derivable from the settled table, stop and ask — don't improvise past this list the way the previous session occasionally caught itself doing (e.g. the registry-stub, the `review-inputs` hardcoded path — both were found and *deferred to the right job* rather than silently fixed out of scope).

---

## Practical notes

- **Worker prompts for S1–S2a are saved** at `/tmp/claude-1000/-home-castlemill-repositories-shinobu/*/scratchpad/` from prior sessions but that scratchpad is session-scoped and likely gone by the time you read this — don't rely on finding them. Use them as a *template* for structure (scope / non-scope / exact files / done-when / report-back), not as copy-paste source, since S3a/S3b/S3c are new jobs with no prior prompt to reuse.
- **Model recommendations used so far:** Opus 5 for anything mechanical-but-foundational or involving judgment calls under a weakenable test suite (S1, S2, S2a, and likely S3a/S3b). Sonnet 5 was earmarked for S5/S7 (smoke-writing against an already-fixed contract, and docs) — lighter judgment load once the shape is settled.
- **The live workspace registry** (`shinobu-workspace.yaml`) is gitignored and already correctly renamed by the human — this is done, not outstanding. Don't re-flag it.
- **`projects/`, `worktrees/`, `global-status.json`** are local state the human keeps on purpose. No worker, ever, touches these — this has held for every job so far and must keep holding.

Good luck. The pattern that's worked: write a tight prompt, let the worker run, then verify everything yourself before writing the next prompt. Don't skip the verify step even when the report sounds complete — it hasn't been, yet, every single time.
