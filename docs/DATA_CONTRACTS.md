# Data Contracts

## Canonical JSONL

Each non-empty line is one object:

```json
{
  "event_id": "evt-001",
  "timestamp": "2026-06-12T10:00:00Z",
  "user_id": "eng-1",
  "repo_id": "payments-api",
  "source": "provider-export",
  "model_name": "model-name",
  "prompt": "Debug Redis timeout",
  "response": "Inspect stale pooled connections",
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "total_tokens": 150,
  "cost_usd": 0.0015,
  "classification": "debugging",
  "files_read": ["payments/redis_pool.py"],
  "files_modified": [],
  "metadata": {}
}
```

`total_tokens` must equal prompt plus completion tokens. Timestamps must be ISO-8601. Strict mode is atomic. Input is limited to 50 MB and each line to 2 MB.

## OpenAI-style input

Use `--format openai` for objects with `request`, `response`, and `usage` fields. See `examples/openai_usage.jsonl`.

## Generic input

Use `--format generic --mapping examples/generic-mapping.json`. Mapping keys are canonical fields and values are source-field names.

## Privacy

Possible credentials are rejected by default. `--redact-sensitive` redacts likely secrets, email addresses, and phone numbers before persistence. This is a bounded heuristic, not a substitute for source-system data governance.
