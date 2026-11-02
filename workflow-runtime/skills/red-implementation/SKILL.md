---
name: red-implementation
description: "Given a Gherkin scenario block, a feature-file path, and a one-scenario run command, write a test that fails right."
---

# Red Implementation

Given one Gherkin scenario, write the test for it and prove it **fails right**: the run reaches the scenario's `Then` and fails on an assertion there. Write the test side only. Never write the behavior under test.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Worktree path | Yes | Absolute or repo-relative. All work stays inside it |
| Scenario | Yes | `id`, `title`, and `gherkin` — the full `Scenario:` block as one string |
| Feature-file path | Yes | Where the scenario goes. The caller owns it — never invent it |
| Run command | Yes | Already resolved, targets exactly this one scenario. Never discover, guess, or build it |

When any input is missing, return the question in `open_questions` and stop.

## File classes

- **Feature files** — Gherkin `.feature` files.
- **Step definitions** — code bound to Gherkin steps.
- **Test support** — fixtures, helpers, hooks, and test config used only by tests.
- **Implementation** — everything the product runs.
- **Generated** files, and **shared** files — package manifests, lockfiles, build and runner config, and anything else both the tests and the product configure — are unowned. Leave them alone. Product code that tests merely import or call is implementation, not shared.

Write only feature files, step definitions, and test support. A file you cannot classify: do not edit it; return the question.

## Procedure

```
Task Progress:
- [ ] Check the run command and the project's Gherkin runner
- [ ] Write the scenario into the feature file, verbatim
- [ ] Write step definitions that fail at Then
- [ ] Run the command once
- [ ] Judge the failure
- [ ] Report
```

### Step 1: Check the setup

Confirm the worktree exists and the project has a Gherkin runner. Confirm, by reading the command, that it targets one scenario and not a suite. Do not execute it, or any other test command, before Step 4. No runner, or a command that is not scoped to one scenario: return the question and stop. Do not install a runner or edit runner config; it is shared.

### Step 2: Write the scenario

Write the `gherkin` string into the feature file **unchanged**: no parsing, translating, rewording, or reformatting. The `Scenario:` line equals the scenario's `title`.

- File exists and already holds a block whose `Scenario:` line equals the title: if that block is identical, leave the file as it is; if it differs, return the question.
- File exists otherwise: append the block. Never rewrite or reorder existing scenarios.
- File does not exist: create it with a `Feature:` line named after the file stem, then the block.

### Step 3: Write step definitions

Find the project's existing step-definition layout (directory, naming, binding style) and extend it. Reuse steps that already match. Add only the missing ones. No clear layout: return the question and stop. Do not change the behavior of an existing step definition; if one must change, return the question.

Make missing implementation fail **at `Then`, not at import**. Reach the behavior without importing code that does not exist yet:

- **Lazy import** — resolve the module inside the step body and turn its absence into an assertion failure at `Then`: for example, catch the import error and fail an assertion naming the missing symbol. An import error that escapes the step is a wrong failure.
- **Public surface** — drive and observe the behavior through what the product exposes (HTTP request, DOM query, CLI output, file written), so the assertion fails on a missing result instead of a missing symbol.

`Given` and `When` steps must be able to complete against the current code. A `When` that invokes behavior which may not exist yet records the outcome (return value, response, output, or raised error) in the scenario context instead of raising, and the `Then` asserts on it. Never move the action into the `Then`. The `Then` step holds the assertion. If the runner makes this impossible, return the question. Never stub, mock out, or pre-create implementation to dodge the failure.

### Step 4: Run once

Run the command exactly once. Do not retry, re-run to confirm, or loosen the test to change the result.

### Step 5: Judge the failure

**Fails right** is exactly this: the run reaches the scenario's `Then` (or an `And`/`But` under `Then`) and fails **on an assertion** there.

Everything else is a question, and you stop:

- an import, compile, syntax, collection, or load-time error;
- an undefined or pending step;
- a failure in a `Given` or `When`;
- the scenario passes on arrival;
- no Gherkin runner configured, or the command does not target this one scenario.

Name which case happened and include the relevant output excerpt. Leave your written files in place for inspection.

### Step 6: Report

- Scenario id
- Files written or extended
- Command run
- The failing-assertion excerpt

## Safety rules

- Write only test-side files named above
- Never edit implementation, generated, or shared files
- Never touch the lines of an existing scenario
- Never stage, commit, stash, reset, or check out
- When in doubt, return the question and stop — do not guess
