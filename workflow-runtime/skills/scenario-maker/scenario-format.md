# Scenario format

**JSON scenario array** — scenario-maker writes this schema. The same file is the scenario list and the loop cursor: one object per scenario, `done: false` / `done: true`.

The caller packs the output path (usually `current-task/scenarios.json` under the worktree).

Scenarios define **what** to build as checkable behaviors, held as Gherkin. They do **not** name implementation steps or file paths.

## File structure

```json
{
  "meta": { "schema": "scenarios.v1" },
  "feature": { "title": "…", "as_a": "…", "i_want": "…", "so_that": "…" },
  "scenarios": [
    { "id": "…", "title": "…", "gherkin": "…", "done": false }
  ]
}
```

1. `meta.schema` — always `"scenarios.v1"`.
2. `feature` — `title`, `as_a`, `i_want`, `so_that` — one set for the feature.
3. `scenarios` — **one** object per scenario, **array order is dependency order** (prerequisites first). No separate ordering field.
4. Each scenario object has a **stable id**, a `title`, a `gherkin` body (`Scenario:` + `Given` / `When` / `Then`), and `done`.

## Scenario ids

Each scenario has a stable `id`, like a spec requirement id: lowercase kebab-case, unique in the file. A caller packs **id + gherkin** without parsing prose.

Do not reuse an id. Do not change an id after that object is `done: true`.

## Scenario object fields

| Field | Meaning |
| ----- | ------- |
| `id` | Stable, lowercase kebab-case, unique in the file |
| `title` | One line, the `Scenario:` name |
| `gherkin` | One string holding the complete `Scenario:` block — `Given` / `When` / `Then` / `And` lines, two-space indented, `\n`-separated. Must be valid Gherkin on its own — red drops it into a feature file unchanged. |
| `done` | `false` when the sheep writes it. Only the loop flips it to `true`. The sheep writes `true` only when preserving an existing `done: true` entry during amend. |

No other fields. Do not add `order`, `depends_on`, `status`, or a per-scenario `spec` pointer.

`done: true` objects are never rewritten, reordered, or removed.

**Do:** one checkable behavior per scenario; dependency order; every scenario testable against finished work.

**Don't:** goal-shaped scenarios ("make the hero better"); more than **four `Then` clauses** in one scenario; skip a spec requirement; invent unstated product specifics.

## Split (before ordering)

Split a scenario into smaller ones when **any** of these hold:

- It cannot be summarized in **two sentences**.
- It reads like a **goal**, not a checkable behavior.
- It has **more than four `Then` clauses**.

Split first, then order the resulting scenarios by dependency.

## Amend

When the file already exists and has any `done: true` object: **append** each new scenario as a new object with `done: false`, at the end of the array. Do not rewrite, reorder, unmark, or restyle a `done: true` object. `done: false` objects may be replaced only when **no** `done: true` object is in the file (first write / full rewrite).

## Example

```json
{
  "meta": { "schema": "scenarios.v1" },
  "feature": {
    "title": "Hero section redesign",
    "as_a": "visitor",
    "i_want": "a clear headline and CTA",
    "so_that": "I know how to start"
  },
  "scenarios": [
    {
      "id": "hero-headline",
      "title": "Headline is visible above the fold",
      "gherkin": "Scenario: Headline is visible above the fold\n  Given the home page is open\n  When the hero renders\n  Then a prominent headline is visible above the fold",
      "done": false
    },
    {
      "id": "hero-cta",
      "title": "Primary CTA is present",
      "gherkin": "Scenario: Primary CTA is present\n  Given the home page is open\n  When the hero renders\n  Then a primary CTA button is visible\n  And the CTA uses existing button patterns",
      "done": false
    },
    {
      "id": "hero-tokens",
      "title": "Hero uses semantic tokens",
      "gherkin": "Scenario: Hero uses semantic tokens\n  Given the hero is on the page\n  When styles apply\n  Then the hero uses semantic color tokens\n  And it does not use raw palette classes",
      "done": true
    }
  ]
}
```

The last scenario is done. An amend would add another object with `done: false` at the **end** of `scenarios` — not edit `hero-tokens`.
