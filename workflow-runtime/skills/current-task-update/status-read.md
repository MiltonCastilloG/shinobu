# Status input (read-only)

Per-task `current-task/status.json`. Writer schema: [status-format.md](status-format.md).

**Shinobu bootstrap:** `bootstrap-context.py` stdout supplies `current_step`, `next_step`, `sheep` — do not re-read status during bootstrap.

## Fields Shinobu uses

| Section | Fields |
|---------|--------|
| `task` | `slug`, `title`, `original`, `current_step`, `next_step` |
| `scope` | `worktree_path` |
| `artifacts` | Document paths: story, spec, archive |
| `open_questions` | Blockers |

## Minimal shape

```json
{
  "task": {
    "slug": "hero-section",
    "original": "hero-section",
    "current_step": "gherkin",
    "next_step": "review"
  },
  "scope": {
    "worktree_path": "worktrees/castlemill-landing-hero-section"
  },
  "artifacts": {
    "story": "current-task/story.md",
    "spec": "current-task/specs/hero-section.json"
  },
  "open_questions": []
}
```
