---
name: red-refactor
description: "Given the uncommitted diff left by an implementation-focused refactor, simplify the test side without changing scenario meaning."
---

# Red Refactor

Given the uncommitted diff left by an implementation-focused refactor, simplify the **test side** that diff touches — remove duplication, improve abstractions — **without changing scenario meaning**. This is the second half of a two-part refactor pair: it runs after the implementation-focused refactor and reads the diff that refactor leaves. Write the test side only. Never change implementation.

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
| Feature files | owns, restricted (see below) |
| Step definitions | owns |
| Test support | owns |
| Implementation | never touches |
| Generated | unowned, left alone |
| Shared | unowned, left alone |

Step definitions and test support are this skill's main material. Implementation never changes here — the implementation-focused refactor already settled it, and touching it here would let this skill mask a regression that refactor exists to catch. Generated and shared files are left alone: a generated file may be overwritten by whatever produced it, and a shared file is read by both the test side and the implementation, so editing it here risks moving behavior on a side this skill never runs against.

**Feature files are restricted.** A scenario's meaning lives in its `Scenario:`, `Given`, `When`, `Then`, `And`, and `But` lines, and no refactor may rewrite them — that text has to stay byte-for-byte so later verification can still find the scenario by its `Scenario:` line. Within a feature file this skill may edit only the `Feature:` line, `Background:` blocks, comments, and tags. Never reorder scenarios or renumber/rename a scenario's own lines.

A file in the diff that does not fit a class, or fits a class this skill does not own: do not edit it; record it and move on (see Report).

## Procedure

```
Task Progress:
- [ ] Run the full-suite command once, before any edit
- [ ] Read the diff and classify every file it touches
- [ ] Simplify the test side only, scenario text untouched
- [ ] Run the full-suite command once, after editing
- [ ] Report, or restore and report a question
```

### Step 1: Confirm the starting point

Run the full-suite command once, before making any edit. It must pass. If it does not, return the question with the output excerpt and stop — do not edit anything.

### Step 2: Read the diff

Read the changed and untracked files and classify each against the classes above. For every file you are about to touch, record its current content first (in memory or a scratch copy), so you can restore it exactly if the suite fails later. Files outside the write domain: leave them untouched and note each one with its file class for the report.

### Step 3: Simplify the test side

Within step definitions and test support: remove duplication, improve abstractions, reduce indirection — whatever makes the tests clearer without changing what any scenario means. Within feature files: edit only the `Feature:` line, `Background:` blocks, comments, and tags, per the restriction above. Do not touch a `Scenario:`, `Given`, `When`, `Then`, `And`, or `But` line anywhere in the file, including scenarios outside the diff. Do not add functionality or touch any file outside the test side.

### Step 4: Run once, after

Run the full-suite command exactly once.

- Still passes → done.
- Does not pass → restore every file you changed to the content you recorded in Step 2. Never use `git checkout`, `git stash`, or `git reset` to do this — other uncommitted work may be sitting in the same tree. Then return the question with the output excerpt, naming what you changed.

### Step 5: Report

- Files changed
- The full-suite command, with its pass/fail result before and after
- Files left alone, each with its file class

## Safety rules

- Write only feature files (restricted), step definitions, and test support
- Never edit implementation
- Never edit generated or shared files
- Never touch a `Scenario:`, `Given`, `When`, `Then`, `And`, or `But` line of any scenario
- Never touch a file you cannot classify
- Never stage, commit, stash, reset, or check out
- When in doubt, return the question and stop — do not guess
