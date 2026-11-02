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
- **Test support** — fixtures, helpers, hooks, and test config used only by tests. Runner config is shared, not test support.
- **Implementation** — everything the product runs that is not test-side, generated, or shared. Product code that tests merely import or call is implementation.
- **Generated** — files produced by a build or tool.
- **Shared** — package manifests, lockfiles, build and runner config, and anything else both the tests and the product configure.

## Write domain

| File class | This skill |
|------------|------------|
| Feature files | comments only (see below) |
| Step definitions | owns |
| Test support | owns |
| Implementation | never touches |
| Generated | unowned, left alone |
| Shared | unowned, left alone |

Step definitions and test support are this skill's main material. Implementation never changes here: it was settled by the implementation-focused refactor that ran before, and the test side is its oracle — changing both in one pass lets a behavior change pass unnoticed. Generated files are rewritten by the tool that produced them, and shared files configure what runs for both sides, so a change to either is not a refactor.

**Feature files: comments only.** A feature file's Gherkin is the scenarios themselves. No refactor rewrites it, and later verification finds each scenario by its `Scenario:` line. Within a feature file this skill may edit comments only. Never edit the `Feature:` line, `Rule:`, `Background:`, `Scenario:`, `Scenario Outline:`, `Examples:`, any step line (`Given`, `When`, `Then`, `And`, `But`, `*`), data tables, doc strings, or tags, and never reorder scenarios.

**Assertions are fixed.** Never remove, weaken, or skip an assertion, a step, or a test. Every step definition must still do and assert exactly what it did; restructure how, never what.

Edit only test-side files in the diff, plus new files you create for code you extract from them. A file in the diff that does not fit a class, or fits a class this skill does not own: do not edit it; record it and move on (see Report).

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

Run the full-suite command once, before making any edit. It must pass: exit status 0, with no failed, errored, undefined, or pending tests or scenarios. Do not retry. A failure — flaky, pre-existing, or otherwise — is a question, not a pass: return it with the output excerpt and stop without editing anything.

### Step 2: Read the diff

Read the changed and untracked files and classify each against the classes above. Before the first edit, record the current content of every file you will change or delete, and the path of every file you will create (in memory or a scratch copy), so you can restore the tree exactly. Files outside the write domain: leave them untouched and note each one with its file class — `unclassified` when it fits none — for the report.

### Step 3: Simplify the test side

Within step definitions and test support: remove duplication, improve abstractions, reduce indirection — whatever makes the tests clearer, under the assertion rule above. Within feature files: comments only. Do not add functionality or touch any file outside the test side.

### Step 4: Run once, after

Run the full-suite command exactly once. Pass means the same as in Step 1.

- Passes → done.
- Does not pass → restore the tree to what you recorded in Step 2: rewrite each changed file to its recorded content, recreate each file you deleted, and delete each file you created. Never use `git checkout`, `git stash`, or `git reset` — other uncommitted work sits in the same tree. Then return the question with the output excerpt, naming what you changed.

### Step 5: Report

- Files changed
- The full-suite command, with its pass/fail result before and after
- Files left alone, each with its file class

## Safety rules

- Write only step definitions, test support, and comments in feature files
- Never edit any non-comment line of a feature file
- Never remove, weaken, or skip an assertion, step, or test
- Never edit implementation
- Never edit generated or shared files
- Never edit a file outside the diff, except new files you create for extracted code
- Never touch a file you cannot classify
- Never stage, commit, stash, reset, or check out
- When in doubt, return the question and stop — do not guess
