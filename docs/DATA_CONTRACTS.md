# Data Contracts

MODE: HYBRID
BRAAT BLOCK: Event contracts
MISSION: Make ingestion reproducible and inspectable.

## LLM interaction event

Required:

```json
{
  "event_type": "llm_interaction",
  "interaction_id": "llm-001",
  "timestamp": "2026-06-01T09:00:00Z",
  "prompt": "Investigate Redis timeout",
  "tokens_spent": 12000,
  "cost_usd": 0.06
}
```

Recommended:

```json
{
  "user_id": "eng-a",
  "repo_id": "payments-api",
  "branch": "main",
  "response": "Likely connection pool issue",
  "files_read": ["payments/redis_pool.py"],
  "files_modified": []
}
```

## Incident event

Required:

```json
{
  "event_type": "incident_event",
  "incident_id": "inc-001",
  "timestamp": "2026-06-01T09:00:00Z",
  "service": "payments-api",
  "node_type": "hypothesis",
  "text": "Redis saturation caused timeout"
}
```

Allowed `node_type` values are defined in `configs/incident_ontology.yaml`.
