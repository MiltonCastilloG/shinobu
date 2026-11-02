---
name: green-implementation
description: "Given uncommitted changes that include one failing test, and a run command, make the smallest implementation change that passes."
---

# Green Implementation

Given uncommitted changes that include one failing test, make the **smallest implementation change** that makes it pass. Write implementation only. Never change the test.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Worktree path | Yes | Absolute or repo-relative. All work stays inside it |
| Run command | Yes | Already resolved, targets exactly the failing test. Never discover, guess, or build it |

The material is **the diff**: `git diff HEAD` plus the untracked files listed by `git status --porcelain` (read them). Plain `git diff` misses new files. Read the failing test from the diff; you receive nothing else about it.

When the run command is missing, or the diff holds no failing test to satisfy, return the question and stop.

## File classes

- **Feature files** — Gherkin `.feature` files.
- **Step definitions** — code bound to Gherkin steps.
- **Test support** — fixtures, helpers, hooks, and test config used only by tests.
- **Implementation** — everything the product runs.
- **Generated** and **shared** files (used by both tests and implementation) are unowned. Leave them alone.

A file is implementation when the product runs it and no test-side class describes it. Write only implementation. A file you cannot classify: do not edit it; return the question.

## Procedure

```
Task Progress:
- [ ] Read the diff and understand what the test asserts
- [ ] Find where the behavior belongs
- [ ] Make the smallest implementation change
- [ ] Run the command once
- [ ] Report
```

### Step 1: Read the diff

Read the changed and untracked files. Identify what the test expects and where it currently fails.

### Step 2: Change implementation

Make the smallest change that satisfies what the test asserts. Do not build ahead of the test, generalize beyond it, or tidy surrounding code. Follow the conventions of the code you touch.

Stop and return the question when:

- the test cannot pass without touching the test side;
- the change needs a product decision the test does not settle.

State the reason. Revert nothing you did not write; leave any partial edit out by not making it before you stop.

### Step 3: Run once

Run the command exactly once. Do not run the full suite. If it still fails, do not iterate: return the question with the output excerpt, and say what you changed.

### Step 4: Report

- Files changed
- Command run
- The pass line

## Safety rules

- Write only implementation files
- Never edit feature files, step definitions, test support, generated, or shared files
- Never stage, commit, stash, reset, or check out
- When in doubt, return the question and stop — do not guess
