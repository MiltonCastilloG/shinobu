# create-worktree.py — manual recovery workflow

When `create-worktree.py` fails on a **recoverable** error, the script preserves any
partial worktree and prints a JSON error to stderr. Complete remaining steps manually
in order — do not silently overwrite existing paths or branches.

## Registry default_branch (r2 fix)

Managed projects may use `main` or `master` as their git default. The workspace registry
(`shinobu-workspace.yaml` / `.example.yaml`) must declare the correct `git.default_branch`
per project (e.g. `tetris-clone-frp` → `master`, `castlemill-landing` → `main`).

If the registry value is wrong or the ref does not exist, `create-worktree.py` auto-detects
the default from `origin/HEAD` or local `main`/`master` refs before pull/worktree add.

Git subprocess failures are wrapped as structured JSON on stderr (handoff fields plus
`status: error` and `errors`) — never a raw Python traceback on recoverable failures.

## Recoverable failure modes

| Failure | Partial state | Manual steps |
|---------|---------------|--------------|
| `git pull` failed | None (worktree not added) | Fix network/auth; checkout `main`; `git pull`; re-run script |
| Worktree path exists | Existing directory | Use a different slug or remove worktree with user approval |
| Branch checked out elsewhere | None or partial | Free the branch or pick a new branch name; re-run |
| `post_create` failed | Worktree + copy + scaffold may exist | `cd` worktree; run failed command; fix; register if needed |
| Registration failed | Worktree complete | Run `register-global-status.py` manually (see below) |
| Uncommitted changes on main | Warning only | Commit/stash with user approval, or continue if intentional |

## Happy-path order (for manual completion)

1. **Workspace root** — cwd must be Shinobu workspace root.
2. **Pull** — in project git root (`shinobu` → workspace root; managed → `projects/<project>`),
   using each project's default branch (`main` or `master` per registry):
   ```bash
   git checkout <default_branch> && git pull origin <default_branch>
   ```
3. **Add worktree** — path `worktrees/<project>-<slug>` (single hyphen):
   ```bash
   git worktree add worktrees/<project>-<slug> -b <type>/<slug> <default_branch>
   ```
   For managed projects, run from `projects/<project>` with relative path
   `../../worktrees/<project>-<slug>`.
4. **Copy locals** — from registry `copy` list; skip missing sources with notice.
5. **post_create** — run each command from registry inside the new worktree.
6. **Scaffold** — ensure `current-task/status.json` exists (see `status-format.md`).
7. **Register** — update `global-status.json`:
   ```bash
   python3 workflow-runtime/skills/start-task/scripts/register-global-status.py \
     "<workspace_root>" "<project>" "<slug>" "worktrees/<project>-<slug>"
   ```

## Never do without user approval

- `git worktree remove --force`
- Delete existing worktree directories
- `git branch -D` / force-push
- Overwrite `global-status.json` entries for active tasks

## Structured handoff

On success, `create-worktree.py` prints JSON to stdout:

```json
{
  "status": "complete",
  "project": "shinobu",
  "slug": "my-task",
  "branch": "chore/my-task",
  "worktree_path": "worktrees/shinobu-my-task",
  "status_path": "worktrees/shinobu-my-task/current-task/status.json",
  "task_id": "4",
  "registry_key": "shinobu:4"
}
```

Sheep-start reads this output — no worktree-creation workflow knowledge required on the happy path.
