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
- **Generated** and **shared** files (used by both tests and implementation) are unowned. Leave them alone.

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

Confirm the worktree exists and the project has a Gherkin runner. Confirm the run command targets one scenario, not a suite. No runner, or a command that is not scoped to one scenario: return the question and stop. Do not install a runner or edit its config.

### Step 2: Write the scenario

Write the `gherkin` string into the feature file **unchanged**: no parsing, translating, rewording, or reformatting. The `Scenario:` line equals the scenario's `title`.

- File exists: append the block. Never rewrite or reorder existing scenarios.
- File does not exist: create it with a `Feature:` line, then the block.

### Step 3: Write step definitions

Find the project's existing step-definition layout (directory, naming, binding style) and extend it. Reuse steps that already match. Add only the missing ones. No clear layout: return the question and stop.

Make missing implementation fail **at `Then`, not at import**. Reach the behavior without importing code that does not exist yet:

- **Lazy import** — import the module inside the step body, so a missing module surfaces where the step runs. Only valid if the step's failure then lands on an assertion at `Then`; an import error is a wrong failure.
- **Public surface** — drive and observe the behavior through what the product exposes (HTTP request, DOM query, CLI output, file written), so the assertion fails on a missing result instead of a missing symbol.

`Given` and `When` steps must be able to complete against the current code. The `Then` step holds the assertion. If the runner makes this impossible, return the question. Never stub, mock out, or pre-create implementation to dodge the failure.

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
