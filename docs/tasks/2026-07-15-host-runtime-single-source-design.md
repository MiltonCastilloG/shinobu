# Approach B — host-neutral workflow runtime

**Status:** open — [`tasks.md`](tasks.md) **#20**  
**Checklist:** [`host-runtime-backlog-and-approach-b.md`](host-runtime-backlog-and-approach-b.md)  
**Prerequisite (Approach A, shipped):** [`archive/host-runtime-symlink/report.md`](../archive/host-runtime-symlink/report.md) · design [`archive/host-runtime-symlink/2026-07-15-host-runtime-single-source-design.md`](../archive/host-runtime-symlink/2026-07-15-host-runtime-single-source-design.md)

---

## Problem (after A)

Approach A made `.cursor/` the committed canonical runtime and symlinked Claude into it. That removed Claude staleness, but Cursor still owns the canonical tree. The workflow runtime should live in a **host-neutral** directory so both Cursor and Claude are adapters, not landlords.

This extraction happens after Nicki Stage 1 and before the history-preserving Shinobu repository fork. It is implemented once, then inherited by both independent products.

---

## Decision: Approach B

| Topic | Decision |
|-------|----------|
| Canonical source | `workflow-runtime/agents/`, `skills/`, `rules/` (committed) |
| Cursor | Symlink `.cursor/agents` and `.cursor/skills` → neutral dir; generate `.cursor/rules/nicki-default.mdc` (do not symlink `.mdc` if Cursor cannot follow refs) |
| Claude | Keep `link_dir` + `generate_claude_md()`; flip `RUNTIME_ROOT` to `workflow-runtime` |
| Hooks / permissions | Stay under `.cursor/` (host-specific) unless a later task moves them |
| Agents | Flat files; ordinary names such as `sheep-start` |
| Skills | One-level `<skill>/SKILL.md`; Claude does not discover category-nested skill folders |
| Path prose | Prefer compatibility via `.cursor/` symlinks first; new canonical references use `workflow-runtime/...` |
| Fork boundary | Tag Nicki after B; clone with history into a sibling Shinobu repo; no shared runtime dependency afterward |

### A→B delta (from Approach A design)

1. Move `.cursor/agents`, `.cursor/skills`, `.cursor/rules` into `workflow-runtime/`.
2. Flip `RUNTIME_ROOT` from `.cursor` to `workflow-runtime`.
3. Add Cursor install (`install.py` or `install-cursor.py`) using the same `link_dir` helper Approach A already shipped.
4. Rewrite or keep `.cursor/skills/...` path prose via compatibility symlinks.

Reuse from A (already on disk): `RUNTIME_ROOT`, `link_dir`, isolated `generate_claude_md()`. Full A decisions and install semantics: see the archived design above.

---

## Out of scope for B

- Cursor hooks parity in Claude
- `nicki doctor` / version pin
- Managed-project `nicki runtime install` (unless required to unblock extract)
- Host registry / plugin abstraction
- Full PLAN.md multi-project CLI
- Shinobu product changes
- Evaluation harness/repository
- Shared runtime package or cross-repository synchronization

---

## Success criteria

1. Clean clone → `python3 install.py` → `.cursor/agents` and `.cursor/skills` are symlinks into `workflow-runtime/`.
2. `python3 install.py` → `.claude/` links into `workflow-runtime/` via `RUNTIME_ROOT`.
3. Edit under `workflow-runtime/skills/…` visible to both hosts without reinstall.
4. Both installers idempotent and self-repairing.
5. Bootstrap / Nicki opt-in still work on Cursor and Claude.
6. Agent definitions remain flat; skill definitions remain one level deep.
7. The resulting commit can be tagged and cloned as the exact Shinobu fork baseline.
