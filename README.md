# Operational Waste Recovery

A local-first tool that imports AI/engineering work telemetry, detects repeated work, produces reusable context capsules, and exports inspectable evidence.

## Immediate user workflow

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
owrp ingest --input data/sample_events.jsonl
owrp status
owrp query "redis timeout"
owrp report
owrp export --format csv --output reports/interactions.csv
```

No API key is required for local CLI use. Data stays in a local SQLite file by default.

## Privacy gate

Ingestion rejects obvious credential-like content by default. Operators can redact likely credentials, email addresses, and phone numbers before storage:

```bash
owrp ingest --input events.jsonl --redact-sensitive
```

`--allow-secrets` is available only for deliberate, controlled local use. It must not be the default in shared or hosted environments.

## Integration surfaces

- canonical JSONL (`--format canonical`);
- OpenAI-style usage JSONL (`--format openai`);
- arbitrary JSONL using a field mapping (`--format generic --mapping mapping.json`);
- JSON and CSV export;
- generated JSON/Markdown recovery reports;
- read-only API: `/health`, `/health/ready`, `/api/status`, `/api/repositories`, `/api/query`, `/api/capsules`.

Local API:

```bash
owrp serve --host 127.0.0.1 --port 8787
```

Non-loopback API:

```bash
export OWRP_API_TOKEN="replace-with-a-long-random-token"
owrp serve --host 0.0.0.0 --port 8787
```

## Retention and deletion

```bash
owrp repositories
owrp purge --repo old-project --yes
owrp purge --before 2026-01-01T00:00:00Z --yes
```

Purge invalidates duplicate/capsule analysis so it must be regenerated.

## Evidence boundary

Duplicate and recovery values are deterministic measurements over imported data. They are not proof of realized labor savings, production ROI, or organization-wide waste.

See [`docs/DATA_CONTRACTS.md`](docs/DATA_CONTRACTS.md), [`docs/INTEGRATION.md`](docs/INTEGRATION.md), [`docs/API.md`](docs/API.md), and [`DEPLOYABILITY_DISTRIBUTION.md`](DEPLOYABILITY_DISTRIBUTION.md).
