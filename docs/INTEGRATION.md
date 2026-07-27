# Integration Guide

## Inputs

Each line must be one JSON object. Use `--format canonical`, `openai`, or `generic`.

For a generic mapping file, keys are canonical fields and values are source fields:

```json
{"event_id":"request_id","repo_id":"project","prompt_tokens":"input_tokens","completion_tokens":"output_tokens"}
```

Strict ingestion is atomic: if any line fails, no accepted line is stored. Use `--allow-rejected` only when partial ingestion and an explicit rejection log are acceptable.

Possible credentials are rejected by default. Use `--redact-sensitive` to replace likely credentials, email addresses, and phone numbers before persistence.

## Outputs

- SQLite: `data/owrp.sqlite`;
- reports: `reports/recovery_report.{json,md}`;
- CSV/JSON export through `owrp export`;
- repository inventory through `owrp repositories`;
- read-only HTTP API through `owrp serve`.

## Production embedding

Run OWRP as a sidecar or scheduled batch job. Export provider telemetry into JSONL, ingest under an explicit retention/privacy policy, regenerate analysis, and consume `/api/status`, `/api/repositories`, or the report files. The HTTP service intentionally has no write endpoint; ingestion and deletion remain explicit operator actions.

## HTTP security

Loopback access works without a token. Binding beyond loopback requires `OWRP_API_TOKEN`; clients send `Authorization: Bearer <token>`. CORS is disabled unless one exact `OWRP_CORS_ORIGIN` is configured.
