---
name: green-refactor
description: "Given the uncommitted diff left by implementing and testing a change, simplify the implementation without changing behavior."
---

# Green Refactor

Given the uncommitted diff left by implementing and testing a change, simplify the **implementation** that diff touches — remove duplication, improve abstractions — **without changing behavior**. This is the first half of a two-part refactor pair: a test-focused refactor runs after this one, on the diff this leaves. Write implementation only. Never change the test side.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Worktree path | Yes | Absolute or repo-relative. All work stays inside it |
| Full-suite run command | Yes | Already resolved, runs the whole test suite, not one scenario. Never discover, guess, or build it |

The material is **the diff**: `git diff HEAD` plus the untracked files listed by `git status --porcelain` (read them). Plain `git diff` misses new files.

When the run command is missing, return the question and stop without editing.

## File classes

- **Feature files** — Gherkin `.feature` files.
- **Step definitions** — code bound to Gherkin steps.
- **Test support** — fixtures, helpers, hooks, and test config used only by tests.
- **Implementation** — everything the product runs.
- **Generated** and **shared** files (used by both tests and implementation) — see Write domain below.

## Write domain

| File class | This skill |
|------------|------------|
| Feature files | never touches |
| Step definitions | never touches |
| Test support | never touches |
| Implementation | owns |
| Generated | unowned, left alone |
| Shared | unowned, left alone |

Implementation is the only class this skill may edit. Feature files, step definitions, and test support belong to the test-focused refactor; touching them here would let this skill mask a regression the other refactor exists to catch. Generated and shared files are left alone: a generated file may be overwritten by whatever produced it, and a shared file is read by both the test side and the implementation, so editing it here risks moving behavior on a side this skill never runs against.

A file in the diff that does not fit a class, or fits a class this skill does not own: do not edit it; record it and move on (see Report).

## Procedure

```
Task Progress:
- [ ] Run the full-suite command once, before any edit
- [ ] Read the diff and classify every file it touches
- [ ] Simplify implementation files only
- [ ] Run the full-suite command once, after editing
- [ ] Report, or restore and report a question
```

### Step 1: Confirm the starting point

Run the full-suite command once, before making any edit. It must pass. If it does not, return the question with the output excerpt and stop — do not edit anything.

### Step 2: Read the diff

Read the changed and untracked files and classify each against the classes above. For every implementation file you are about to touch, record its current content first (in memory or a scratch copy), so you can restore it exactly if the suite fails later. Files outside the write domain: leave them untouched and note each one with its file class for the report.

### Step 3: Simplify implementation

Within implementation files only: remove duplication, improve abstractions, reduce indirection — whatever makes the code clearer without changing what it does. Do not add functionality, generalize beyond what the diff already does, or touch any file outside implementation.

### Step 4: Run once, after

Run the full-suite command exactly once.

- Still passes → done.
- Does not pass → restore every file you changed to the content you recorded in Step 2. Never use `git checkout`, `git stash`, or `git reset` to do this — other uncommitted work may be sitting in the same tree. Then return the question with the output excerpt, naming what you changed.

### Step 5: Report

- Files changed
- The full-suite command, with its pass/fail result before and after
- Files left alone, each with its file class

## Safety rules

- Write only implementation files
- Never edit feature files, step definitions, or test support
- Never edit generated or shared files
- Never touch a file you cannot classify
- Never stage, commit, stash, reset, or check out
- When in doubt, return the question and stop — do not guess
