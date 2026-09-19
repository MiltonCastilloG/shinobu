# Approach B — neutral-dir extract checklist

**Task:** [`tasks.md`](tasks.md) **#20**

**Design (B):** [Approach B — neutral-dir host runtime](2026-07-15-host-runtime-single-source-design.md)

**Approach A (shipped):** [`archive/host-runtime-symlink/report.md`](../archive/host-runtime-symlink/report.md) · [A design](../archive/host-runtime-symlink/2026-07-15-host-runtime-single-source-design.md)

**Fresh-install context:** [Fresh install design](../archive/fresh-install/2026-07-02-fresh-install-design.md) — historical `#20` text calls the target `nicki-workflow/`; this live checklist supersedes it with `workflow-runtime/`.

**Prerequisite:** Approach A shipped — `.cursor/` canonical, `RUNTIME_ROOT = .cursor`, Claude symlinks via the installer. See [`tasks-done.md`](../tasks-done.md).

**Goal:** One **host-neutral** committed canonical dir for agents/skills/rules; host dirs (`.cursor/`, `.claude/`) become adapters via symlinks + generated rule files. Land this once before the history-preserving Shinobu repository fork.

Reference A→B delta from the [B design](2026-07-15-host-runtime-single-source-design.md) (A detail in the archive link above):

1. Move `.cursor/agents`, `.cursor/skills`, `.cursor/rules` into a neutral dir.
2. Flip `RUNTIME_ROOT` to that dir.
3. Add `.cursor/` (and keep `.claude/`) symlinking via the same `link_dir` helper.
4. Rewrite or compat-hardcoded `.cursor/skills/...` path prose.

---

## Canonical directory

**Decision: `workflow-runtime/`.**

| Option | Pros | Cons |
|--------|------|------|
| **`workflow-runtime/`** (chosen) | Visible, host-neutral, and valid unchanged in both repositories after the fork | Longer paths; one more top-level dir |
| `nicki-workflow/` | Clearly branded in Nicki | Must be renamed in the Shinobu fork; no longer neutral for the baseline |
| `.agents/` | Short; matches some ecosystem examples | Hidden; easy to confuse with host tooling; weaker "Nicki owns this" signal; not the name used in `#20` prose |

**Decision checklist**

- [x] Confirm `workflow-runtime/` in the design and ownership map
- [ ] Layout target: `workflow-runtime/agents/`, `workflow-runtime/skills/`, `workflow-runtime/rules/` (rules stay canonical; hosts get generated adapters)
- [ ] Keep agent files flat and retain generic sheep names
- [ ] Keep discoverable skills one level deep: `workflow-runtime/skills/<name>/SKILL.md`
- [ ] Decide whether hooks / `permissions.json` stay under `.cursor/` only (host-specific) or also move — **recommend leave hooks + permissions under `.cursor/`** unless Claude needs them later (out of scope for B core)

## Move agents, skills, rules from `.cursor/` into neutral dir

- [ ] `git mv` `.cursor/agents` → `workflow-runtime/agents`
- [ ] `git mv` `.cursor/skills` → `workflow-runtime/skills`
- [ ] `git mv` `.cursor/rules` → `workflow-runtime/rules` (at least `nicki-default.mdc`)
- [ ] Leave host-only Cursor files in place if not moved: `permissions.json`, `hooks.json`, `hooks/` (unless a later task relocates them)
- [ ] Verify no stray copies of agents/skills remain as real directories under `.cursor/` after move

## Flip `RUNTIME_ROOT` in the Claude install path

- [ ] Set `RUNTIME_ROOT` from `.cursor` → `workflow-runtime`
- [ ] Confirm `link_dir(RUNTIME_ROOT/agents → .claude/agents)` and skills still relative and self-repairing
- [ ] Confirm `generate_claude_md()` reads `workflow-runtime/rules/nicki-default.mdc`
- [ ] Re-run manual Claude install proof (idempotent + self-repair)

## Cursor installer: `install-cursor.py` or `install.py` `link_cursor_runtime`

Per fresh-install "Future hook (#20)" and single-source B delta:

- [ ] Prefer extending `install.py` with `link_cursor_runtime()` **or** add `install-cursor.py` that reuses the same `link_dir` helper — one shared implementation, no duplicate link logic
- [ ] Symlink: `workflow-runtime/agents` → `.cursor/agents`
- [ ] Symlink: `workflow-runtime/skills` → `.cursor/skills`
- [ ] Rule file: **generate** `.cursor/rules/nicki-default.mdc` from canonical rule (or keep a thin Cursor-only adapter) — **do not symlink the `.mdc` if that breaks Cursor's "no follow references" constraint**; generate-inline stays the safe pattern
- [ ] Fresh clone path: `python3 install.py` must create Cursor links so Cursor works without a manual second script (README must match)
- [ ] Claude path: covered by `python3 install.py` (both hosts)

## Gitignore / git tracking strategy

- [ ] **Canonical `workflow-runtime/`** — tracked in git (source of truth)
- [ ] **`.claude/`** — remain gitignored (generated symlinks + install artifact)
- [ ] **`CLAUDE.md`** — remain gitignored (generated adapter)
- [ ] **`.cursor/agents` and `.cursor/skills` after B** — become symlinks:
  - Option A (cleaner): stop tracking real trees; document that `install.py` creates links; optionally gitignore link targets if git cannot store them portably
  - Option B (compat): commit relative symlinks in git if the team accepts symlink-in-repo semantics for Linux/macOS
- [ ] Document Windows: symlink may fail → copy fallback (same as Approach A); re-run required after edits in that mode
- [ ] Ensure `git status` after install is clean for ignored generated hosts; no accidental commit of `.claude/` copies

## Hardcoded `.cursor/skills/...` paths — rewrite or compatibility

Paths appear widely (agents, skills, hooks, permissions, routing, smokes, archives).

**Recommended strategy (pick one explicitly):**

1. **Compatibility first (lower churn):** After Cursor links exist, leave prose as `.cursor/skills/...` — resolvable because `.cursor/skills` → `workflow-runtime/skills`. Fastest B land.
2. **Rewrite later (clarity):** Second pass to `workflow-runtime/skills/...` (or a single helper constant) once A/B install is stable.

Checklist:

- [ ] Inventory grep: `nicki.md`, sheep agents, skills (`start-task`, `nicki/routing.yaml`, smoke scripts), hooks, `permissions.json`, tests
- [ ] Either verify every command still resolves via `.cursor/` symlinks **or** batch-rewrite to neutral paths
- [ ] Update `permissions.json` allowlist strings to match the chosen path style
- [ ] Update hook script paths if they invoke skills by string path
- [ ] Re-run gate/bootstrap smokes after path decision

## Host adapters: `CLAUDE.md` + `nicki-default.mdc`

- [ ] Keep **generate, don't symlink** for host rule/invocation files
- [ ] Canonical rule lives under `workflow-runtime/rules/nicki-default.mdc`
- [ ] `install.py` → generates root `CLAUDE.md`
- [ ] Cursor install → generates/refreshes `.cursor/rules/nicki-default.mdc` (or leaves a Cursor-specific wrapper that embeds the same opt-in Nicki text)
- [ ] Document: edit the canonical rule; re-run host install(s) when the invocation rule changes (agent/skill edits still need **no** reinstall if symlinks)

## Docs updates

- [ ] `README.md` — canonical dir is `workflow-runtime/`; edit there; host dirs are adapters; atomic-save warning applies to **both** `.cursor/` and `.claude/` symlink trees
- [ ] `docs/future-tasks/PLAN.md` — replace "workflow lives in `.cursor/`" / `package/.cursor/` language with neutral runtime + install-into-host
- [ ] Fresh-install design / archive notes — optional batch rename of the old Claude-only installer naming (claude-adapter suggestion) when touching bootstrap docs

## Manual verification checklist (Cursor + Claude after extract)

- [ ] Clean clone → `python3 install.py` → `.cursor/agents` and `.cursor/skills` are symlinks into `workflow-runtime/`
- [ ] `python3 install.py` → `.claude/agents` and `.claude/skills` are symlinks into `workflow-runtime/` (via `RUNTIME_ROOT`)
- [ ] Edit a skill under `workflow-runtime/skills/…`; change visible in Cursor path **and** Claude path without reinstall
- [ ] Re-run both installers → idempotent; no error
- [ ] Break a host link (replace with a regular directory) → re-run installer → link repaired
- [ ] `bootstrap-context.py` invoked with documented paths still works
- [ ] Cursor: `nicki start …` / `nicki continue` opt-in still works
- [ ] Claude: same after `CLAUDE.md` present
- [ ] Atomic-save warning: editing through the host symlink path must not replace the symlink (document; spot-check editor behavior)

## Handoff to the Shinobu fork

- [ ] Complete Stage 1, smoke CI, and this runtime extract before forking
- [ ] Tag the approved Nicki baseline
- [ ] Clone with full Git history into a sibling `shinobu/` directory
- [ ] Create a new Shinobu remote and replace `origin`
- [ ] Verify the fork starts from the tagged commit
- [ ] Rewrite product-facing selector, routing/bootstrap identity, installer text, workspace/config/version filenames, and docs
- [ ] Keep generic sheep, skill, script, and artifact names
- [ ] Do not add a shared runtime dependency or automatic cross-repository merge process

## Migration risks

| Risk | Mitigation |
|------|------------|
| **Atomic saves break symlinks** | Document "edit canonical `workflow-runtime/`, never host symlink path"; installers self-repair |
| **Windows symlink privilege / failure** | Keep copy fallback + warning that re-runs are required after edits |
| **Worktrees inheriting `.cursor/`** | Worktrees created from a branch that already has Cursor links (or real trees) inherit them; after B, ensure default branch has correct layout / install step before new worktrees |
| **Git and symlinks** | Decide track-vs-gitignore before merge; avoid half-tracked copy leftovers |
| **Path prose drift** | Grep gate + permissions + smoke in the same PR as the move |
| **Hooks stay Cursor-only** | Do not assume Claude gets hook parity in B (explicitly out of scope) |
| **Large simultaneous churn** | B is mostly move + flip `RUNTIME_ROOT` + Cursor linker |

## Out of scope for Approach B

- Cursor hooks parity in Claude
- `nicki doctor` / version pin (`#28` in fresh-install out-of-scope list)
- Managed-project runtime install (`nicki runtime install <project>`) unless required to unblock the Nicki-repo extract
- Host registry / plugin abstraction
- Shared runtime-link package extraction beyond what's needed to share `link_dir` between installers
- Full PLAN.md multi-project CLI (workspace init, clone, etc.)
- Shinobu product implementation beyond producing a clean tagged fork baseline
- Evaluation harness/repository
- Shared runtime package or cross-repository synchronization
