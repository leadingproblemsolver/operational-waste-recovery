# Changelog

## 1.0.0 — 2026-07-27

- Replaced prototype/stale contracts with canonical/OpenAI/generic JSONL ingestion, idempotent SQLite storage, repo-scoped duplicate analysis, context capsules, query, reports, and exports.
- Added privacy rejection/redaction, strict atomic ingestion, stable IDs, bounded input handling, explicit retention/purge, authenticated read-only serving, Docker/Compose/CI, and offline packaging.
- Corrected the bundled synthetic sample so the default run demonstrates at least one repeated-work pair and added a regression test for that user-visible outcome.
