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
| Review material | Yes* | Diff + optional story/spec from prompt / disk |

\*When the worktree is missing, or the diff alone is unclear with no planning files, return the question in `open_questions` and stop.

## Procedure

1. Resolve worktree scope. Read under scope + CONTRIBUTING. **Write nothing.** Never edit app code, specs, stories, or `status.json`.
2. Load prompt / `current-task/` context when present.
3. Inspect `git diff` vs main (or working tree).
4. Check requirements / verify commands / CONTRIBUTING when material exists.
5. Decide pass vs changes-needed vs re-review. Put blocking findings in `summary` (and `open_questions` when blocked). The caller (Shinobu) relays the verdict and gets user approval before routing — review routes nothing itself.

## Safety

- Never edit application code or planning files.
- Never force-push, reset hard, or delete worktrees without approval.
- When in doubt, return the question in `open_questions` and stop. You judge the work; you do not judge what the work should have been.
