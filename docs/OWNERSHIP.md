# Ownership map — Nicki baseline and Shinobu fork

Live Stage 1 inventory. Destination behavior: [`SHINOBU.md`](SHINOBU.md). Sequence: [`SHINOBU_NEXT_STEPS.md`](SHINOBU_NEXT_STEPS.md).

## Locked architecture

1. Finish Stage 1 in this Nicki repository.
2. Extract the canonical host-neutral runtime to `workflow-runtime/`.
3. Tag the fork point.
4. Clone the repository, with history, into a sibling Shinobu repository and replace its remote.
5. Develop and release Nicki and Shinobu independently.

The products do not coexist in one runtime. There is no shared runtime package and no ongoing Nicki-to-Shinobu merge process.

## Legend

| Owner | Meaning |
| ----- | ------- |
| **Nicki** | Remains only in the Nicki repository after the fork. |
| **fork baseline** | Copied with Git history into Shinobu, then independently maintained. This does not mean a live shared file. |
| **Shinobu** | Added or changed only after the fork. |
| **host adapter** | Cursor- or Claude-specific generated surface around `workflow-runtime/`. |
| **workspace layout** | Generic task/worktree shape copied at the fork. Each repository owns its own instance. |

## Naming rule

Repository identity is the namespace. Do not add product suffixes merely to avoid Nicki/Shinobu collisions.

- Agent files stay flat under `workflow-runtime/agents/`.
- Agent filename and frontmatter `name:` match.
- Keep ordinary sheep names: `sheep-start`, `sheep-status`, `sheep-close`, `sheep-subtask`, `sheep-execute`.
- Shinobu inherits those names in its own repository.
- Orchestrator selector is the product name: `nicki` in Nicki, changed to `shinobu` in the fork.
- Skills stay one level below `workflow-runtime/skills/` because Claude only discovers `<skills>/<name>/SKILL.md`.
- Scripts may remain under their owning skill; no filename prefix is needed.
- Current-task artifacts remain generic (`status.json`, `story.md`, `specs/`, `subtasks/`) because the repositories and worktrees are separate.

## Target runtime layout

**Live** as of task **20b** (Track 1 — committed Cursor symlinks; Cursor symlink spike **20a** PASS).

```text
workflow-runtime/
├── agents/                 # flat agent files
├── skills/                 # flat discoverable skill folders
└── rules/                  # canonical invocation rules

.cursor/
├── agents -> ../workflow-runtime/agents
├── skills -> ../workflow-runtime/skills
├── rules/                  # generated Cursor adapter
├── hooks/
└── permissions.json

.claude/
├── agents -> ../workflow-runtime/agents
└── skills -> ../workflow-runtime/skills

CLAUDE.md                    # generated Claude adapter
```

Supporting markdown does not belong under `agents/`; Cursor can discover nested markdown as agents.

## Agents

| Today | Owner | Stage 1 / fork action | Why |
| ----- | ----- | --------------------- | --- |
| `.cursor/agents/nicki.md` (`nicki`) | Nicki, then Shinobu modification | Move flat to `workflow-runtime/agents/nicki.md`; fork changes filename/name/content to `shinobu` | Product selector and orchestrator. |
| `sheep-start` | fork baseline | Move flat; keep name in both repositories | Lifecycle is copied, not generalized. |
| `sheep-status` | fork baseline | Move flat; keep name in both repositories | Each repository writes its own `status.json`. |
| `sheep-close` | fork baseline | Move flat; keep name in both repositories | Each repository owns teardown and registry mutation. |
| `sheep-spec` | fork baseline | Move flat; keep name | Both products start from the same spec behavior at the fork point. |
| `sheep-gherkin` | fork baseline | Move flat; keep name | Stage 1 makes spec → Gherkin checklist; both inherit it. |
| `sheep-review` | fork baseline | Move flat; keep name | Both inherit review behavior, then may diverge. |
| `sheep-sync` | fork baseline | Move flat; keep name | Git tail copied into each repository. |
| `sheep-archive` | fork baseline | Move flat; keep name | Archive behavior copied into each repository. |
| `sheep-integrate` | fork baseline | Move flat; keep name | Git tail copied into each repository. |
| `sheep-fallback` | fork baseline | Move flat; keep name | Harness error handling copied into each repository. |
| `sheep-subtask` | Nicki | Move flat; keep name | Nicki tail; remove from Shinobu when its TDD pipeline replaces it. |
| `sheep-execute` | Nicki | Move flat; keep name | Nicki tail; remove from Shinobu when red/green replaces it. |
| `sheep-red` | Shinobu | Add after fork | One scenario; success means fails right. |
| `sheep-green` | Shinobu | Add after fork | Minimal change to pass; does not edit test/story. |
| `sheep-green-refactor` | Shinobu | Add after fork | Implementation-only refactor; runs first. |
| `sheep-red-refactor` | Shinobu | Add after fork | Tests-only refactor; runs second, after green-refactor. |

Agent permissions use the same flat agent names. No Nicki/Shinobu suffix keys are needed because each repository has its own `.cursor/hooks/agent-permissions.json`.

## Skills

| Today | Owner | Stage 1 / fork action | Why |
| ----- | ----- | --------------------- | --- |
| `start-task/` | fork baseline | Keep generic, move under `workflow-runtime/skills/` | Each repository has one start lifecycle. |
| `current-task-update/` | fork baseline | Keep generic, move | Each repository has one status writer and routing. |
| `close-task/` | fork baseline | Keep generic, move | Each repository has one close lifecycle. |
| `close-scope/` | fork baseline | Keep generic, move | Registry/worktree teardown copied at fork. |
| `spec-maker/` | fork baseline | Keep generic, move | Common baseline behavior. |
| `story-maker/` | fork baseline | Keep generic, move | Stage 1 Gherkin transform inherited by Shinobu. |
| `review-execution/` | fork baseline | Keep generic, move | Independent copies after fork. |
| `sync-task/` | fork baseline | Keep generic, move | Git operation copied at fork. |
| `integrate-task/` | fork baseline | Keep generic, move | Git operation copied at fork. |
| `task-archive/` | fork baseline | Keep generic, move | Archive behavior copied at fork. |
| `conflict-resolution/` | fork baseline | Keep generic, move | Git safety copied at fork. |
| `errors-recording/` | fork baseline | Keep generic, move | Harness failure recording copied at fork. |
| `pause-context/` | fork baseline | Keep generic, move | Stop-and-ask support copied at fork. |
| `hook-contract/` | fork baseline | Keep generic, move | Registry/status resolution copied at fork. |
| `caveman/`, `brainstorm/` | fork baseline | Keep generic, move | General utilities copied at fork. |
| `subtask-maker/` | Nicki | Keep generic, move; remove from Shinobu if unused | Nicki tail. |
| `execute-plan/` | Nicki | Keep generic, move; remove from Shinobu if unused | Nicki tail. |
| `validation/` | Nicki | Retired; remove rather than copy when cleanup permits | Not a Shinobu dependency. |
| red/green/refactor skills | Shinobu | Add after fork as top-level skill folders | Claude cannot discover category-nested skills. |

Files that look reusable are copied baseline code, not a third shared package. Extract a shared package only if measured maintenance pain later justifies versioning and compatibility work.

## Scripts and hardcoded paths

| Today | Owner | Stage 1 / fork action | Why |
| ----- | ----- | --------------------- | --- |
| `start-task/scripts/create-worktree.py` | fork baseline | Keep basename/path under the skill | No cross-product filename collision after fork. |
| `register-global-status.py` / `.sh` | fork baseline | Keep basename/path | Each repository writes its own registry. |
| `start-worktrees.sh` | Nicki | Retired path; remove if unused, otherwise copy as-is | Do not rename solely for namespacing. |
| `current-task-update/scripts/update-status.py` | fork baseline | Keep basename/path | Each repository writes generic `status.json`. |
| `current-task-update/scripts/routing_write.py` | fork baseline | Remove hardcoded `skills/nicki/routing.json` during neutral extraction | Product-branded routing is the main hidden fork coupling. |
| `close-scope/scripts/unregister-global-status.sh` | fork baseline | Keep basename/path | Repository-local registry. |
| `close-scope/scripts/teardown-worktree.sh` | fork baseline | Keep basename/path | Repository-local worktrees. |
| `skills/nicki/scripts/bootstrap-context.py` | Nicki, then Shinobu modification | Move with runtime; fork removes Nicki identity | Reads routing, registry, and status. |
| `skills/nicki/scripts/bootstrap_utils.py` | Nicki, then Shinobu modification | Move with runtime; fork replaces `NICKI_WORKSPACE_ROOT` and Nicki routing | Product-specific bootstrap implementation. |
| `skills/nicki/scripts/validate-harness-stdout.py` | fork baseline | Move with harness; fork points at Shinobu routing | Contract checker. |
| `errors-recording/scripts/append-error.py` | fork baseline | Keep generic | Each repository owns its errors artifact. |
| `scripts/generate-code-workspace.sh` | Nicki, then Shinobu modification | Copy at fork; rename generated workspace in Shinobu | Product-facing IDE workspace. |

Neutral extraction may keep `.cursor/skills/...` command paths temporarily through symlink compatibility, but canonical docs and new code should point at `workflow-runtime/`.

## Artifacts and workspace layout

| Name | Owner | Action | Why |
| ---- | ----- | ------ | --- |
| `current-task/status.json` | workspace layout | Keep generic | One product per repository/worktree. |
| `current-task/story.md` | workspace layout | Keep generic | No cross-product collision. |
| `current-task/specs/` | workspace layout | Keep generic | No cross-product collision. |
| `current-task/subtasks/` | Nicki | Keep in Nicki; Shinobu may remove after fork | Nicki tail only. |
| `current-task/specs/errors.json` | fork baseline | Keep generic | Harness-local error record. |
| `global-status.json` | workspace layout | Keep generic | Each repository has its own registry. |
| `worktrees/<project>-<slug>/` | workspace layout | Keep | Each product evaluates in its own workspace clone. |
| `nicki-workspace.yaml` | Nicki | Fork renames product-facing registry/config if Shinobu retains it | Product-facing filename, not collision avoidance. |
| `nicki.code-workspace` | Nicki | Fork changes to Shinobu equivalent | Product-facing IDE filename. |
| `nicki_version.yaml` | Nicki | Fork changes to Shinobu equivalent | Independent versions after fork. |
| `docs/archive/<slug>/` | fork baseline | Keep generic | Each repository owns its archive. |

The old prefixed artifact proposal (`nicki-status.json`, `shinobu-status.json`, and similar) is cancelled. It solved a same-worktree collision that no longer exists.

## Routing and bootstrap

| Item | Owner | Action |
| ---- | ----- | ------ |
| Nicki routing | Nicki | Stage 1 becomes `start → spec → gherkin → subtasks → execute → …`. |
| Bootstrap/read path | fork baseline | Neutral extraction removes `.cursor` as canonical source; fork changes product selector/routing only. |
| Status writer | fork baseline | Keep `status.json`; route from the repository-local routing file. |
| Shinobu routing | Shinobu | After fork: `start → spec → gherkin → red/green loop → green-refactor → red-refactor → review → git tail`. |
| Lifecycle implementation | fork baseline | Copied with history, then independently maintained; never parameterized across repositories. |

## Rules, hooks, permissions, installers

| Today | Owner | Stage 1 / fork action |
| ----- | ----- | --------------------- |
| `.cursor/rules/nicki-default.mdc` | Nicki | Move canonical rule to `workflow-runtime/rules/`; Cursor adapter generated. Fork rewrites selector to Shinobu. |
| `CLAUDE.md` | host adapter | Generate from the repository’s canonical rule. |
| `.cursor/hooks.json` | host adapter | Stay Cursor-specific. |
| `.cursor/hooks/enforce-agent-tools.sh` | host adapter | Stay Cursor-specific; each repository has its own agent keys. |
| `.cursor/hooks/agent-permissions.json` | host adapter | Stay Cursor-specific; keep generic sheep names. |
| `.cursor/permissions.json` | host adapter | Stay Cursor-specific; update allowed paths after neutral extraction. |
| `install.py` | fork baseline | Installs both Cursor and Claude host adapters from `workflow-runtime/`; fork changes product-facing messages/config. |

## Smoke and harness

All live `tests/smoke/` modules remain Nicki tests during Stage 1. Neutral extraction updates paths without changing behavior. They are copied into Shinobu at the fork, then its suite is changed to assert Shinobu routing and loop behavior.

Stage 1 must cover:

- `start → spec → gherkin → subtasks`;
- generic agent names (`sheep-start`, `sheep-status`, `sheep-close`);
- generic artifacts (`status.json`, `story.md`, `specs/`, `subtasks/`);
- the live `sheep-gherkin` routing/file/frontmatter name;
- hardcoded `.cursor/skills/...` compatibility during neutral extraction;
- `routing_write.py` and bootstrap routing ownership;
- recursive agent test globs only if the runtime ever introduces agent subfolders (current decision: flat).

## Stage 1: change and leave

Change:

- Nicki behavior to spec-first + Gherkin transform.
- Move canonical runtime from `.cursor/` to `workflow-runtime/`.
- Make `.cursor/` and `.claude/` host adapters.
- Remove hardcoded canonical dependence on `.cursor/` and hidden Nicki routing where the fork would inherit it.
- Add smoke CI after the Stage 1 behavior changes.

Leave:

- flat agent names;
- generic lifecycle agent, skill, and script names;
- generic current-task artifact names;
- generic worktree and archive layouts;
- one complete Nicki product per repository.

## Fork into Shinobu

1. Tag the approved Nicki baseline after Stage 1, smoke CI, and neutral extraction.
2. Clone that repository into a sibling `shinobu/` folder, preserving all Git history.
3. Create the Shinobu remote and replace `origin`.
4. Change product selector, orchestrator, routing, installer text, workspace/config/version filenames, and documentation.
5. Remove Nicki-only subtask/execute tail where Shinobu no longer uses it.
6. Add `sheep-red`, `sheep-green`, `sheep-green-refactor`, and `sheep-red-refactor` sheep/skills. The two refactors run serially: green-refactor, then red-refactor.
7. Keep shared-at-fork code independent; cherry-pick only deliberate critical fixes.

## Deferred

- Evaluation repository or harness design.
- Shared runtime package/repository.
- Ongoing cross-repository synchronization.
- Independent packaging beyond each repository’s current installers.

## Open

None for repository/runtime ownership. Evaluation design is intentionally deferred.
