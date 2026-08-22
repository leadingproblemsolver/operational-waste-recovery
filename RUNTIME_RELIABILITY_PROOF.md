# Runtime Reliability Proof

This repository includes an executable Docker reliability harness at `scripts/runtime_proof.py`.

It builds the repository's real Docker image, starts the real HTTP service, and exercises persistent SQLite state through an isolated Docker volume. The workflow uploads the resulting JSON receipt as a GitHub Actions artifact.

## Required checks

1. **Clean boot** — authenticated readiness returns zero interactions on a fresh volume.
2. **Unauthorized boundary** — protected API state returns HTTP 401 without a bearer token.
3. **First ingest** — the bundled three-event sample persists through the packaged CLI.
4. **Duplicate idempotency** — replaying the same event IDs leaves the interaction count unchanged.
5. **Strict failure atomicity** — a batch with a valid first record and domain-invalid second record exits non-zero and adds zero interactions.
6. **Report generation** — the packaged report command succeeds against the live persisted database.
7. **Bounded status probe** — 30 authenticated status requests report actual p50/p95/max latency and error rate.
8. **Container recreation persistence** — destroying and recreating the service container against the same volume retains the accepted interactions.
9. **Outage recovery** — the client observes the stopped service as unavailable, then the restarted service becomes ready with state intact.

## Run

```bash
python scripts/runtime_proof.py
```

The command prints a single JSON receipt and exits non-zero if any required check fails.

## Claim boundary

A passing receipt proves the bounded behavior above for one isolated CI environment and one image ID. It does not establish production scale, real customer traffic, multi-tenant isolation, or long-duration reliability.
