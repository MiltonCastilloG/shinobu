# Global status input (read-only)

Workspace `global-status.json` — task registry. Writer schema: [global-status-format.md](global-status-format.md).

**Shinobu bootstrap:** `bootstrap-context.py` stdout supplies `active_task` and `status_path` — do not re-read registry fields during bootstrap.

Hooks, start-task, and close-scope still read the registry directly when resolving task ids.
