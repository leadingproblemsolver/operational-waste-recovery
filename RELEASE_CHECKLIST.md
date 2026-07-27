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
- [ ] Docker/Compose runtime because no container runtime was available.
- [ ] provider-specific live telemetry exports.
- [ ] organization-scale data volume and p95/p99 latency.
- [ ] accuracy of lexical duplicate classification on real corpora.
- [ ] realized labor savings, ROI, adoption, and cold-operator activation.

Unchecked items require a real browser, deployment environment, external integration, or human/user evidence. They are not implied by the checked offline release gates.
