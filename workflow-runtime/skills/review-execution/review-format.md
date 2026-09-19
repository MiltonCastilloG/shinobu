# Review format

**JSON only** — output reviews have exactly two top-level keys: `approved` and `content`.

Review writes **no file**. This shape is what the review return `summary` conveys, so the caller can act on it.

## Top-level fields

| Field | Required | Description |
|-------|----------|-------------|
| `approved` | Yes | `true` if the implementation passes review; `false` if blocking issues remain |
| `content` | Yes | Pass summary (`approved: true`) or actionable issue list (`approved: false`) |

**Output reviews have no other top-level keys.** Do not add `meta`, `title`, or routing hints.

## Optional review input (guidance)

Review guidance files use review JSON plus one extra input-only key. See [review-guidance-format.md](review-guidance-format.md).

| Field | Required | Description |
|-------|----------|-------------|
| `approved` | Yes | Usually `false`; explains that previous review should not be treated as approved |
| `content` | Yes | Why the previous review should be rerun |
| `important-considerations` | Yes | Scope or correctness notes to keep in mind while reviewing |

`important-considerations` is input-only. Output must still have only `approved` and `content`.

## `approved`

- `true` — requirements met, verify passed, no blocking convention violations. `[scope]` notes allowed.
- `false` — one or more **blocking** issues (`[req-`, `[verify]`, `[convention]`). `[scope]` alone does not require `false`.

## `content`

Use a JSON string (use `\n` for newlines). Write in plain language with consistent prefixes so issues are easy to scan and act on.

### When `approved: true`

Brief pass summary (2–5 lines). Mention requirements coverage, verify results, and scope.

```json
{
  "approved": true,
  "content": "All spec requirements met (hero-headline, hero-subcopy, hero-cta, hero-tokens).\nVerify: npm run lint and npm test -- Hero passed.\nNo files changed outside spec scope.\n"
}
```

### When `approved: false`

List **blocking issues** only. Each bullet should be actionable — reference IDs, paths, and failures.

| Prefix | Use for |
|--------|---------|
| `[req-<id>]` | Spec requirement not met |
| `[scope]` | Change outside spec `scope.out` — **non-blocking**; name it in the summary as deferred work |
| `[verify]` | Lint, test, build, or other check failure |
| `[convention]` | CONTRIBUTING rule violation (tokens, i18n, deps) |

```json
{
  "approved": false,
  "content": "[req-hero-cta] Hero component has no CTA button — only headline and subcopy rendered.\n[verify] npm run lint failed: src/components/Hero/Hero.tsx — unused import 'Link'.\n[scope] src/components/Footer/Footer.tsx modified — outside spec scope.out.\n"
}
```

## Writing good `content`

**Do:**

- Reference spec requirement IDs when applicable
- Name exact file paths for code and scope issues
- Paste or summarize verify command failures with enough context to reproduce
- Keep bullets specific and testable

**Don't:**

- Suggest fixes — only report what failed review
- Include non-blocking nits unless strict review was requested
- Add keys beyond `approved` and `content`

## Ambiguity → stop

You cannot reach a human. Return the question in `open_questions` and stop — no verdict — when:

- Spec or story is missing and partial review is insufficient
- A requirement is subjective and pass/fail is unclear
- Verify commands cannot run (missing deps, wrong branch base)
- Git history makes change discovery unreliable

Your caller puts the question to the user and re-spawns you with the answer.
