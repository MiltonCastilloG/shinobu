# Review guidance format

Input for a later review run when prior guidance exists on disk.

Default path: `current-task/review-inputs/rN-review.json`.

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `approved` | Yes | Usually `false` |
| `content` | Yes | Why prior review should not drive fixes |
| `important-considerations` | Yes | Context for next review |
| `review_scope` | No | When `mode` is `partial`, gate requires user confirm |

Output reviews still have only `approved` and `content`.

## Example

```json
{
  "approved": false,
  "content": "Prior review mixed scope notes with blockers. Rerun with spec and story.\n",
  "important-considerations": [
    "Do not block on footer redesign; footer is outside scope.in.",
    "Still report verify and convention failures."
  ]
}
```
