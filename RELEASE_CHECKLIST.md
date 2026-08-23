# Release Checklist

## Verified in this release

- [x] canonical, OpenAI-style, and mapped generic JSONL adapters.
- [x] strict atomic and idempotent ingestion.
- [x] token arithmetic and malformed-input rejection.
- [x] default credential-like-content rejection and optional redaction.
- [x] repo-scoped lexical duplicate detection.
- [x] context-capsule and report generation.
- [x] CSV/JSON export and scoped purge.
- [x] offline deterministic wheel.
- [x] API health, authentication, repository listing, and exact-origin CORS behavior.
- [x] bounded Docker runtime: clean boot, auth boundary, idempotent replay, strict-failure atomicity, container recreation persistence, and outage recovery in GitHub Actions.
- [x] Docker Compose runtime: build/start, ingest/analyze/report/export, restart, persisted-state equality, post-restart reads, and uploaded runtime receipts in GitHub Actions.
- [ ] provider-specific live telemetry exports.
- [ ] organization-scale data volume and p95/p99 latency.
- [ ] accuracy of lexical duplicate classification on real corpora.
- [ ] realized labor savings, ROI, adoption, and cold-operator activation.

Checked runtime items establish bounded behavior in GitHub-hosted CI, not production scale or customer impact. The remaining unchecked items require external provider data, materially larger workloads, or real human/customer evidence; they are not implied by the checked release gates.
