---
name: review-execution
description: "Review worktree changes against available current-task files and the git diff; report verdict in summary."
---

# Review Execution

Review implementation in a worktree against the git diff and whatever exists under `current-task/`. Put the verdict in the sheep return `summary` for Shinobu/chat. Do **not** write review JSON, validation JSON, or next-steps handoffs.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Worktree path | Yes | Absolute or repo-relative |
| Spec path | No | When present, check requirements against it |
| Scenario list path | Yes | Format: [scenario-format.md](../scenario-maker/scenario-format.md) |
| `run_all` command | Yes | Packed by the caller, already resolved; runs the whole suite, not only this task's scenarios |

Missing the worktree, `run_all`, or the scenario list path, or a diff that cannot be discovered reliably → return the question in `open_questions` and stop, no verdict.

## Procedure

1. Resolve worktree scope. Read under scope + CONTRIBUTING. **Write nothing.** Never edit app code, specs, or the scenario list. Running `run_all` and verify commands may leave runner caches or reports; that is the only writing allowed.
2. Load prompt / `current-task/` context when present.
3. Inspect the diff against main: `git diff $(git merge-base main HEAD)` for tracked changes, plus `git ls-files --others --exclude-standard` for new files (read them). Plain `git diff` misses new files.
4. Check requirements / verify commands / CONTRIBUTING when material exists.
5. Run the two duties below.
6. Decide pass vs changes-needed vs re-review. Put blocking findings in `summary` (and `open_questions` when blocked). The caller relays the verdict and decides what happens next — review decides nothing itself.

## Duty 1 — Regression check

Run the packed `run_all` command once, against the whole suite. Any failing test is a blocking `[regression]` finding: name the test and include enough of the failure output to reproduce it. Review cannot know whether a failure pre-dates this task — report it as `[regression]` regardless and let the human decide. Missing `run_all` → `open_questions`, no verdict.

## Duty 2 — Scenario compliance

Read the scenario list (format: [scenario-format.md](../scenario-maker/scenario-format.md)); never write it. For every entry with `done: true`, check it is:

- **Present** — its `Scenario:` line (== `title`) appears in a feature file in the worktree, and that scenario's lines match its `gherkin` string line for line, in order, with no lines added between them: compare each line after stripping leading whitespace; the rest must be byte-identical. Read any `Background:` that applies to it; a `Background:` that alters what the scenario checks is blocking. Missing or altered → blocking.
- **Passed** — it ran and passed in the Duty 1 run. Skipped, pending, undefined, or not executed counts as not passed. When the runner output cannot attribute results to individual scenarios, say so in `content`, then confirm that no tag, filter, or runner config excludes this scenario (or its `Feature:` / `Rule:`) and that the run is fully green. Never assume a pass from the `done` flag.
- **Genuinely satisfied** — read the step definitions and the implementation they exercise. A `Then` whose assertion is trivial, skipped, mocked away, or no longer checks what the scenario says is blocking. A `done` flag is a claim, not evidence.

Any entry still `done: false` at review time is blocking. Missing scenario list → `open_questions`, no verdict. Each finding uses prefix `[scenario-<id>]` with the scenario's id.

## Safety

- Never stage, commit, stash, reset, or check out — including to test whether a failure pre-dates this task.
- Never edit application code or planning files.
- Never force-push, reset hard, or delete worktrees without approval.
- When in doubt, return the question in `open_questions` and stop. You judge the work; you do not judge what the work should have been.
