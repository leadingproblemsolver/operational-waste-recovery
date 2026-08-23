# Validation Report

## Release purpose

Dependency-free local-first import, duplicate-work analysis, context-capsule generation, reporting, export, and read-only evidence API.

## Result

- **Automated tests:** 15/15 Pytest tests passed in the release validation baseline; the current repository CI also passes on this runtime-proof change.
- **Release validation:** Source compilation, repository validation, two byte-identical wheel builds, offline wheel installation, CLI ingest/status/analyze/query/report/export/repositories workflow, authenticated read-only API smoke checks, isolated Docker runtime proof, and Docker Compose runtime proof passed.
- **Release status:** bounded runtime-verified release candidate.

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
- isolated Docker image build, clean boot, authenticated API boundary, persisted state across container recreation, and outage recovery
- Docker Compose build/start, CLI ingest/analyze/report/export, authenticated API reads, host-visible export, restart, and persisted state after restart

## Runtime receipts — 2026-08-23

### Isolated Docker runtime

GitHub Actions run: https://github.com/leadingproblemsolver/operational-waste-recovery/actions/runs/32651749303

Observed in that bounded CI run:

- clean boot reported zero interactions
- unauthenticated `/api/status` returned 401
- bundled sample ingest produced 3 interactions
- replaying the same sample kept the interaction count at 3
- a strict malformed/domain-invalid batch exited non-zero and left the persisted interaction count at 3
- report generation exited 0
- 30 authenticated status probes completed with 0 errors; p50 0.935 ms, p95 1.03 ms, max 1.767 ms on that runner
- container recreation retained 3 interactions, 1 duplicate pair, and 1 context capsule
- a forced outage was observed and the restarted container recovered the same persisted state

These latency values describe one GitHub-hosted CI run only; they are not production SLOs or organization-scale benchmarks.

### Docker Compose runtime

GitHub Actions run: https://github.com/leadingproblemsolver/operational-waste-recovery/actions/runs/32651749388

The Compose gate passed all of these steps:

1. build and start the Compose service;
2. wait for `/health` liveness;
3. verify the configured bearer-auth boundary;
4. run ingest → status → analyze → report → export inside the container;
5. verify the exported interactions file is visible through the host bind mount;
6. capture API status before restart;
7. restart the Compose service and wait for liveness again;
8. assert the complete status object is unchanged after restart and contains interactions, duplicate pairs, and context capsules;
9. verify authenticated repository and query reads after restart;
10. upload machine-readable runtime receipts and Compose logs.

## Not verified

- provider-specific live telemetry exports
- organization-scale data volume and p95/p99 latency
- accuracy of lexical duplicate classification on real corpora
- realized labor savings, ROI, adoption, and cold-operator activation

## Claim boundary

This report establishes deterministic local behavior, the stated release contracts, and bounded container/Compose runtime behavior in GitHub-hosted CI. It does not establish production scale, provider-specific live telemetry, real-corpus classification accuracy, adoption, business impact, multi-tenant production isolation, or independent human ownership. See `AI_HUMAN_PROVENANCE.md`, `PORTFOLIO_EVIDENCE.md`, and `HUMAN_OWNERSHIP_SPRINTS.md`.
