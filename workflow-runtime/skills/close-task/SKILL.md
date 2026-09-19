---
name: close-task
description: "Unregister global-status, delete worktree. After integrate + Shinobu close confirm."
disable-model-invocation: true
---

# Close Task

[close-scope](../close-scope/SKILL.md) — unregister + delete worktree.

## When

- `integrate-task` done
- status-update recorded integrate
- User confirms worktree delete

## Inputs

| Input | Req |
|-------|-----|
| Worktree path | yes |
| `current-task/status.json` | preferred |

Missing path → return the question in `open_questions` and stop.

## Checklist

```
- [ ] close-scope §1 — paths
- [ ] close-scope §2–3 — unregister + teardown
- [ ] Report
```

Ordering is guaranteed by routing, not by a file check: `next_step` reaches `close`
only through integrate's `default_next_step`, and `update-status.py` refuses to jump
to `close`.

## Safety

- No close without Shinobu confirm.
- No `task: true`.
