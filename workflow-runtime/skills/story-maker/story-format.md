# Story format

**Markdown Gherkin checklist** — story-maker writes this schema. The same file is the story checklist and the loop cursor: one `- [ ]` / `- [x]` per scenario.

The caller packs the output path (usually `current-task/story.md` under the worktree).

Stories define **what** to build as checkable scenarios. They do **not** name implementation steps or file paths.

## File structure

1. `Feature:` title.
2. `As a` / `I want` / `So that` — one set for the feature.
3. Checklist body — **one** `- [ ]` or `- [x]` per scenario, **ordered by dependency** (prerequisites first).
4. Each scenario has a **stable id** and a Gherkin body (`Scenario:` + `Given` / `When` / `Then`).

## Scenario ids

Each scenario has a stable id, like a spec requirement id: lowercase kebab-case, unique in the file. Put it as a Gherkin tag on the checklist line so a caller can pack **id + body** without parsing prose.

Do not reuse an id. Do not change an id after that line is `- [x]`.

## Checklist line rules

| Mark | Meaning |
| ---- | ------- |
| `- [ ]` | Scenario not done |
| `- [x]` | Scenario done — **never rewrite this line** |

The checkbox line is the scenario. Indented `Given` / `When` / `Then` / `And` belong to that scenario until the next `- [` line.

**Do:** one checkable behavior per scenario; dependency order; every scenario testable against finished work.

**Don't:** goal-shaped scenarios ("make the hero better"); more than **four `Then` clauses** in one scenario; skip a spec requirement; invent unstated product specifics.

## Split (before ordering)

Split a scenario into smaller ones when **any** of these hold:

- It cannot be summarized in **two sentences**.
- It reads like a **goal**, not a checkable behavior.
- It has **more than four `Then` clauses**.

Split first, then order the resulting scenarios by dependency.

## Amend

When the file already exists and has any `- [x]` lines: **append** each new scenario as a new `- [ ]`. Do not rewrite, reorder, uncheck, or restyle completed `- [x]` blocks. Unchecked `- [ ]` lines may be replaced only when **no** `- [x]` is in the file (first write / full rewrite).

## Example

```markdown
Feature: Hero section redesign
  As a visitor
  I want a clear headline and CTA
  So that I know how to start

- [ ] @hero-headline
  Scenario: Headline is visible above the fold
    Given the home page is open
    When the hero renders
    Then a prominent headline is visible above the fold

- [ ] @hero-cta
  Scenario: Primary CTA is present
    Given the home page is open
    When the hero renders
    Then a primary CTA button is visible
    And the CTA uses existing button patterns

- [x] @hero-tokens
  Scenario: Hero uses semantic tokens
    Given the hero is on the page
    When styles apply
    Then the hero uses semantic color tokens
    And it does not use raw palette classes
```

The last scenario is done. An amend would add another `- [ ]` **below** it — not edit `@hero-tokens`.
