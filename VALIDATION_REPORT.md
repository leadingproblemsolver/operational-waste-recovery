# Validation Report

## Release purpose

Dependency-free local-first import, duplicate-work analysis, context-capsule generation, reporting, export, and read-only evidence API.

## Result

- **Automated tests:** 15/15 Pytest tests passed
- **Release validation:** Source compilation, repository validation, two byte-identical wheel builds, offline wheel installation, CLI ingest/status/analyze/query/report/export/repositories workflow, and authenticated read-only API smoke checks passed.
- **Release status:** offline-verified release candidate

## Verified

- canonical, OpenAI-style, and mapped generic JSONL adapters
- strict atomic and idempotent ingestion
- token arithmetic and malformed-input rejection
- default credential-like-content rejection and optional redaction
- repo-scoped lexical duplicate detection
- context-capsule and report generation
- CSV/JSON export and scoped purge
- offline deterministic wheel
- API health, authentication, repository listing, and exact-origin CORS behavior

## Not verified

- Docker/Compose runtime because no container runtime was available
- provider-specific live telemetry exports
- organization-scale data volume and p95/p99 latency
- accuracy of lexical duplicate classification on real corpora
- realized labor savings, ROI, adoption, and cold-operator activation

## Claim boundary

This report establishes deterministic local behavior and the stated release contracts only. It does not establish production scale, adoption, business impact, or independent human ownership. See `AI_HUMAN_PROVENANCE.md`, `PORTFOLIO_EVIDENCE.md`, and `HUMAN_OWNERSHIP_SPRINTS.md`.
