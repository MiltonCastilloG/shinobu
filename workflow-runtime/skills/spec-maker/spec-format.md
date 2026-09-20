# Spec format

**JSON only** — spec-maker writes this schema.

The caller packs the output path (usually `current-task/specs/<slug>.json` under the worktree).

Specs define **what** to build (requirements, scope, acceptance). They do **not** name implementation steps or file paths.

## Top-level fields

| Field | Required | Description |
|-------|----------|-------------|
| `meta` | Yes | Machine-friendly metadata |
| `title` | Yes | Short task name |
| `type` | Yes | Task type: `feature`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf` |
| `summary` | Yes | One-paragraph description of the goal |
| `requirements` | Yes | Ordered list of what must be delivered |
| `scope` | No | `in` and `out` lists bounding the work |
| `constraints` | No | Rules for downstream work (e.g. `no-commit`, `no-new-deps`) |
| `acceptance` | Yes | Testable criteria for done |
| `assumptions` | No | Defaults applied when the task was silent |
| `open_questions` | No | Unresolved decisions — must be empty before the story is written |

## `meta` block

| Field | Required | Description |
|-------|----------|-------------|
| `worktree` | Yes | Worktree slug (e.g. `hero-section`) |
| `generated_by` | Yes | `spec-maker` for original task specs; `validation` for follow-up specs |
| `task` | Yes | Original task description — Gherkin story or user text |
| `branch` | No | Git branch (e.g. `feature/hero-section`) |
| `context` | No | Optional traceability path when the loading agent sets one |
| `source_review` | No | Review path when generated from validation out-of-scope follow-up |
| `source_validation` | No | Validation path when generated from validation out-of-scope follow-up |
| `source_finding` | No | Original review finding that triggered a follow-up spec |

## Requirement fields

Each item in `requirements`:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Stable label (`hero-cta`, `fix-link-href`) |
| `description` | Yes | Specific, testable requirement — not aspirational |

## JSON example

```json
{
  "meta": {
    "worktree": "hero-section",
    "generated_by": "spec-maker",
    "task": "redesign hero section with headline, subcopy, and CTA",
    "branch": "feature/hero-section"
  },
  "title": "Hero section redesign",
  "type": "feature",
  "summary": "Replace the current home page hero with a new section featuring a prominent headline, supporting subcopy, and a primary call-to-action button.\n",
  "requirements": [
    {
      "id": "hero-headline",
      "description": "Display a prominent headline in the hero area above the fold."
    },
    {
      "id": "hero-subcopy",
      "description": "Display supporting subcopy below the headline."
    },
    {
      "id": "hero-cta",
      "description": "Include a primary CTA button using existing link/button patterns."
    },
    {
      "id": "hero-tokens",
      "description": "Style using semantic Tailwind tokens only — no raw palette classes."
    }
  ],
  "scope": {
    "in": [
      "Home page hero area",
      "New or refactored Hero component"
    ],
    "out": [
      "Header, footer, and other pages",
      "New npm dependencies",
      "i18n changes unless required by the hero copy"
    ]
  },
  "constraints": [
    "no-commit",
    "no-new-deps"
  ],
  "acceptance": [
    "Home page hero shows headline, subcopy, and CTA",
    "Styling uses semantic Tailwind tokens (bg-primary, text-primary, etc.)",
    "npm run lint passes",
    "npm test passes for affected components"
  ],
  "assumptions": [
    "Reuse layout patterns from the existing LandingBanner component",
    "Hero copy is static English for this task"
  ],
  "open_questions": []
}
```

## Writing good specs

**Do:**

- Make every requirement testable and specific
- Bound scope with explicit `in` / `out` lists
- List acceptance criteria the executor can verify
- Record assumptions when the user's task was implicit
- Put unresolved design forks in `open_questions` — do not guess

**Don't:**

- Name file paths or implementation steps
- Use vague verbs without measurable outcomes (`improve`, `modernize`, `clean up`)
- Duplicate implementation detail (commands, step order, create/modify actions)
- Leave silent on constraints — default to `no-commit` and `no-new-deps` unless the task requires otherwise

## Ambiguity → stop

You cannot reach a human. Write no spec file; return the question in `open_questions` and stop when:

- The task has no measurable outcome
- Scope is unclear and cannot be reasonably bounded
- Multiple valid interpretations exist (e.g. which page, which component)
- A design fork affects requirements (CTA destination, copy tone, etc.)

Your caller puts the question to the user and re-spawns you with the answer. Then write with `open_questions: []`.
