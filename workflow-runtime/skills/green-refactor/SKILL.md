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
- **Test support** — fixtures, helpers, hooks, and test config used only by tests. Runner config is shared, not test support.
- **Implementation** — everything the product runs that is not test-side, generated, or shared. Product code that tests merely import or call is implementation.
- **Generated** — files produced by a build or tool.
- **Shared** — package manifests, lockfiles, build and runner config, and anything else both the tests and the product configure.

## Write domain

| File class | This skill |
|------------|------------|
| Feature files | never touches |
| Step definitions | never touches |
| Test support | never touches |
| Implementation | owns |
| Generated | unowned, left alone |
| Shared | unused-dependency removal only (see below) |

Implementation is this skill's material. The test side is the oracle for the implementation: changing both in one pass lets a behavior change pass unnoticed, so the test side is left to the test-focused refactor that runs after this one. Generated files are rewritten by the tool that produced them, and shared files configure what runs for both sides, so a change to either is not a refactor — with one exception below.

**Unused dependencies.** In a package manifest, this skill may delete a dependency entry that no file in the worktree imports or references anymore. Edit nothing else in shared files: no version changes, no additions, no scripts or settings. Never run the package manager; leave the lockfile as it is and report it as needing an update.

Edit only implementation files in the diff, the package manifest for unused-dependency removal, and new files you create for code you extract. A file in the diff that does not fit a class, or fits a class this skill does not own: do not edit it; record it and move on (see Report).

## Procedure

```
Task Progress:
- [ ] Run the full-suite command once, before any edit
- [ ] Read the diff and classify every file it touches
- [ ] Simplify implementation files; remove unused dependencies
- [ ] Run the full-suite command once, after editing
- [ ] Report, or restore and report a question
```

### Step 1: Confirm the starting point

Run the full-suite command once, before making any edit. It must pass: exit status 0, with no failed, errored, undefined, or pending tests or scenarios. Do not retry. A failure — flaky, pre-existing, or otherwise — is a question, not a pass: return it with the output excerpt and stop without editing anything.

### Step 2: Read the diff

Read the changed and untracked files and classify each against the classes above. Before the first edit, record the current content of every file you will change or delete, and the path of every file you will create (in memory or a scratch copy), so you can restore the tree exactly. Files outside the write domain: leave them untouched and note each one with its file class — `unclassified` when it fits none — for the report.

### Step 3: Simplify implementation

Within implementation files: remove duplication, improve abstractions, reduce indirection — whatever makes the code clearer without changing what it does. Delete manifest entries for dependencies nothing uses anymore. Do not add functionality, generalize beyond what the diff already does, or touch any other file.

### Step 4: Run once, after

Run the full-suite command exactly once. Pass means the same as in Step 1.

- Passes → done.
- Does not pass → restore the tree to what you recorded in Step 2: rewrite each changed file to its recorded content, recreate each file you deleted, and delete each file you created. Never use `git checkout`, `git stash`, or `git reset` — other uncommitted work sits in the same tree. Then return the question with the output excerpt, naming what you changed.

### Step 5: Report

- Files changed
- Dependencies removed, and that the lockfile needs updating
- The full-suite command, with its pass/fail result before and after
- Files left alone, each with its file class

## Safety rules

- Write only implementation files, plus unused-dependency deletions in a package manifest
- Never edit feature files, step definitions, or test support
- Never edit generated files; in shared files, only delete unused dependency entries from a manifest
- Never run the package manager
- Never edit a file outside the diff, except the manifest for unused dependencies and new files you create for extracted code
- Never touch a file you cannot classify
- Never stage, commit, stash, reset, or check out
- When in doubt, return the question and stop — do not guess
