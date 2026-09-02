# Testing Stateful Ingestion Against Replay, Partial Failure, Container Loss, and Outage

A stateful ingestion service is easy to test on the happy path:

**input → success → row exists.**

That says little about what happens when execution becomes ambiguous.

For Operational Waste Recovery, the narrower reliability question is:

> Can the ingestion path preserve its state invariants when the same input is replayed, a batch fails during validation, the service container is destroyed, or the service disappears and returns?

The active path is intentionally small:

`JSONL → bounded adapter → validation → atomic/idempotent SQLite upsert → analysis/reporting → CLI + read-only HTTP API`

The runtime proof builds the repository's actual Docker image and gives SQLite its own Docker volume. The same state is then exercised through packaged CLI commands and the running HTTP service.

## The invariants

### 1. Replay must not create another fact

The three-event fixture is ingested once, then ingested again with the same event IDs.

Required result:

`3 interactions → replay → 3 interactions`

A retry is therefore tested as a state transition, not merely as another successful HTTP/CLI call.

### 2. Invalid batches must fail atomically

The hostile fixture contains:

- a valid first record;
- a syntactically valid second record with inconsistent token totals.

The important question is whether the first record leaks into persistence before the second one fails.

Required result:

`command != 0` **and** `interaction count remains unchanged`

That distinction matters in any ingest system where validation can fail after part of an input has already been parsed.

### 3. Application lifetime must not equal state lifetime

After successful ingestion, the running service container is destroyed.

A fresh container is started against the same SQLite volume.

Required result:

`recreated service → ready → accepted interactions still present`

This checks persistence across container identity rather than merely restarting a process in place.

### 4. Recovery must include an observed failure

The harness stops the service and first requires the client to observe it as unavailable.

Only then is the service restarted.

Required result:

`observed outage → restart → readiness → prior state intact`

This prevents a recovery test from passing without proving that an outage actually occurred.

## Other boundaries exercised

The same harness also checks:

- authenticated readiness on clean state;
- HTTP 401 when protected state is queried without the bearer token;
- report generation against the persisted database;
- 30 authenticated status requests with error rate plus p50/p95/max timings.

The harness prints one JSON receipt and exits non-zero if any required check fails.

Run it with:

```bash
python scripts/runtime_proof.py
```

Implementation: [`scripts/runtime_proof.py`](../scripts/runtime_proof.py)

Proof contract: [`RUNTIME_RELIABILITY_PROOF.md`](../RUNTIME_RELIABILITY_PROOF.md)

CI wiring: [`.github/workflows/runtime-proof.yml`](../.github/workflows/runtime-proof.yml)

Architecture: [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)

Release claim boundary: [`RELEASE_CHECKLIST.md`](../RELEASE_CHECKLIST.md)

## What this demonstrates — and what it does not

The release gates record these bounded runtime behaviors as verified in GitHub-hosted CI.

That is the claim.

It is **not** evidence of production scale, real customer traffic, multi-tenant isolation, long-duration availability, organization-scale latency, customer ROI, or adoption.

The useful pattern is broader than this repository:

**Stateful reliability tests should attack transitions and invariants, not merely assert that endpoints return 200.**

Replay, partial failure, runtime replacement, and outage/recovery are small tests, but they expose classes of failure that a happy-path integration test cannot.
