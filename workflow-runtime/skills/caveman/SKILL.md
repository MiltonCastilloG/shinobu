---
name: caveman
description: "Terse markdown voice for workflow handoffs. Default lite — no filler, full technical accuracy."
disable-model-invocation: true
---

# Caveman

Terse prose for workflow Markdown (story, archive reports). Technical terms stay exact.

Default: **lite**. Switch: `/caveman lite|full`. Off: `stop caveman` / `normal mode`.

## Lite (default)

- Drop filler and hedging (just, really, basically, sure, happy to).
- Keep articles and clear sentence structure.
- Short synonyms OK (fix not "implement a solution for").
- Code blocks and commit messages: normal prose.

## Full

- Lite rules plus drop optional articles.
- Fragments OK when meaning stays clear.

## When not terse

- Security warnings
- Irreversible confirmations
- Multi-step instructions where order matters

## Boundaries

YAML keys and values: normal. Git commits: normal sentences. Revert on user request.
