# Scenario format

**`scenarios.json`** — scenario-maker writes this schema. The same file is the scenario list and the loop cursor: one object per scenario, and `done` is the flag the loop reads and flips.

The caller packs the output path (usually `current-task/scenarios.json` under the worktree).

Scenarios define **what** to build as checkable behaviors. They do **not** name implementation steps or file paths. Gherkin is the syntax each scenario's body is written in; it is not the name of the artifact.

## File structure

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

| Field | Required | Notes |
| ----- | -------- | ----- |
| `meta.schema` | Yes | Always `"scenarios.v1"` |
| `feature.title` | Yes | The feature, one line |
| `feature.as_a` / `i_want` / `so_that` | Yes | One set for the feature |
| `scenarios` | Yes | Array, **ordered by dependency** (prerequisites first) |
| `scenarios[].id` | Yes | Stable id — see Scenario ids |
| `scenarios[].title` | Yes | Same text as the `Scenario:` line in `gherkin` |
| `scenarios[].gherkin` | Yes | **One string** holding the full `Scenario:` block (`Scenario:` + `Given` / `When` / `Then` / `And`), lines joined with `\n`, so a caller can drop it into a feature file unchanged |
| `scenarios[].done` | Yes | `false` when written. Only the loop sets `true` — scenario-maker never does |

The file is valid JSON. Write no comments and no trailing commas.

No other fields. Do not add `order`, `depends_on`, `status`, or a per-scenario `spec` pointer.

## Scenario ids

Each scenario has a stable id, like a spec requirement id: lowercase kebab-case, **unique** in the file. A caller packs **id + title + gherkin** by reading one object — no prose parsing.

Do not reuse an id. Do not change an id after that entry is `done: true`.

## Order

The `scenarios` array order is the dependency order. Array position is the only ordering — there is no `order` field. Prerequisites come first, so the loop's "first `done: false`" is always the next buildable scenario.

## Scenario rules

**Do:** one checkable behavior per scenario; dependency order; every scenario testable against finished work; cover every spec requirement.

**Don't:** goal-shaped scenarios ("make the hero better"); more than **four `Then` clauses** in one scenario; skip a spec requirement; invent unstated product specifics.

## Split (before ordering)

Split a scenario into smaller ones when **any** of these hold:

- It cannot be summarized in **two sentences**.
- It reads like a **goal**, not a checkable behavior.
- It has **more than four `Then` clauses**.

Split first, then order the resulting scenarios by dependency.

## No product open_questions

Scenarios are a transform of the spec, not an interview. scenario-maker raises **no product `open_questions`**. A spec too vague to yield testable scenarios is reported as `spec_incomplete` with `gaps`, and nothing is written.

## Amend

When the file already exists and any scenario has `done: true`: **append** each new scenario as a **new object with `done: false`** at the end of `scenarios`. Do not rewrite, reorder, flip back, or restyle any entry with `done: true`. Entries with `done: false` may be replaced only when **no** entry is `done: true` (first write / full rewrite).

An amend never edits the `feature` block or an existing id.

## Example of an amend

Given the example above, a new requirement arrives. The amend appends below `hero-tokens` — it does not edit `hero-tokens`:

```json
{
  "id": "hero-mobile-layout",
  "title": "Hero stacks on narrow screens",
  "gherkin": "Scenario: Hero stacks on narrow screens\n  Given the home page is open on a narrow screen\n  When the hero renders\n  Then the headline appears above the CTA",
  "done": false
}
```
