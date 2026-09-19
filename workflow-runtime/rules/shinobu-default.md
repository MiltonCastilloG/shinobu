# Shinobu invocation (opt-in)

Do **not** route messages to Shinobu by default. Respond as the normal Agent unless the user explicitly invokes her.

## Invoke Shinobu when

User addresses Shinobu by name at the start of the message, e.g. `shinobu fetch`, `Shinobu, continue`, `shinobu what's next`.

When matched, invoke a **fresh** Task (`subagent_type: shinobu`) — never `resume`. Pass the user's latest message as the prompt (strip an optional `shinobu` prefix).

**Task selector — the one thing you may add.** If this chat has identified which project and task it concerns (the user named it now or earlier in this chat), prepend a single line `Task: <project>/<slug>` before the user's message. That selector is the *only* context you may forward. If no task has been identified in this chat, forward the message alone — Shinobu will ask which project/task before doing pipeline work; she does not auto-select `active_task`.

Return the subagent's response as your primary reply.

## Stay on Shinobu

After the first invocation, keep invoking a fresh Task on every Shinobu-directed message until the user says they want to stop (e.g. `stop shinobu`, `talk to me directly`, `exit shinobu`).

## Stop and ask

Sheep cannot reach the user; you and Shinobu can. When a sheep return (or Shinobu's relay of one) carries `open_questions`, put each question to the user with `AskQuestion` — offer the entry's `options` when present — then continue: re-spawn the same sheep with the answers (ad-hoc), or pass the answers back to Shinobu so she re-spawns (pipeline). For `spec`, keep the pause path in the prompt so the sheep resumes. Never answer for the user.

## Otherwise

Handle the message yourself. Do not run multi-step pipeline orchestration inline.

- **Full pipeline:** suggest invoking Shinobu (`shinobu start …`, `shinobu continue`).
- **Ad-hoc work:** Task-spawn the sheep directly (see below), or attach the skill when you want the work in your own context.

## Ad-hoc: invoke a sheep directly

Ad-hoc needs no task, worktree, or `status.json` — only instructions. Task-spawn one sheep, relay its return JSON in chat, and stop. Never run `bootstrap-context.py`, never call `sheep-status`, never write pipeline state.

Pack the prompt with the user's instructions plus:

- **Document sheep** (`sheep-gherkin`, `sheep-spec`) — an output path. Use the user's path when they name one, otherwise a sensible file under `docs/adhoc/`. For `sheep-gherkin`, also pack the spec path. For `sheep-spec`, also pack a pause path (e.g. under `docs/adhoc/`) so the sheep can stop mid-run without losing exploration.
- **Archive sheep** (`sheep-archive`) — always `<prefix>/docs/archive/<slug>/`. Pass `prefix` (workspace or nested-project root) and `slug`; never `docs/adhoc/`. Also pass status/artifact paths or a `source_document`, and an errors path when one exists.
- **Operational sheep** (`sheep-review`) — the working directory. If unclear, ask the user with `AskQuestion`; do not guess.
- **Git sheep** (`sheep-sync`, `sheep-integrate`) — get an explicit yes naming the side effect before spawning.

**When a sheep returns `open_questions`:** it has stopped, not failed. Put each question to the user with `AskQuestion` (offer the entry's `options` when present), then re-spawn the **same** sheep with the answers. For `spec`, include the pause path so it resumes instead of re-exploring. Never answer for the user.

**Shinobu-only sheep:** `sheep-start`, `sheep-close`, and `sheep-status` own the worktree registry and per-task status. Never spawn them from the parent agent.
