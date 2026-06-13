# Architecture

MODE: MANUAL
BRAAT BLOCK: Architecture boundary
MISSION: Document only architecture that exists in this repository.

## Active local architecture

```text
JSONL telemetry
  -> pipeline.ingest
  -> storage.sqlite_store
  -> pipeline.deduplicate
  -> execution_context.capsules
  -> pipeline.reports
  -> retrieval.query
```

## Implemented package boundaries

```text
core
  pure types, hashing, resource accounting, paths, logging

pipeline
  ingest, deduplicate, report, validate

storage
  SQLite schema and store

retrieval
  local query and similar incident retrieval

execution_context
  context capsule generation
```

## Import rule

Allowed direction:

```text
cli -> pipeline / retrieval / execution_context / storage
pipeline -> core / storage
retrieval -> core / storage
execution_context -> core / storage
storage -> core
core -> stdlib only
```

Forbidden:

```text
core importing pipeline
storage importing pipeline
owrp.cli importing owrp.cli
any package importing itself through main aliases
```

## External systems are not active assumptions

GitHub, Slack, PagerDuty, Jira, Neo4j, ClickHouse, OpenAI, and vector databases are integration candidates only. The active proof path is local SQLite + JSONL.
