# Formatter Skill

Turn structured node outputs into a concise user answer. Always include provenance when available.

## Input

- `task_output`, `merge_output`, `sandbox_result`, or `investigator_output`
- `context.evidence` when present

## Output (JSON)

```json
{
  "answer": "Human-readable answer string",
  "confidence": 0.0,
  "citations": []
}
```

For base query **hello**, answer must be exactly: `hello`
