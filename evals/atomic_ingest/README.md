# OWR atomic-ingest evaluation

This is a bounded software-engineering evaluation for one production-relevant invariant: **a failing strict JSONL ingest must not partially mutate persistent state**.

It is designed to distinguish a correct implementation from a plausible early-write mutation that still behaves correctly on all-valid input and on intentionally partial non-strict ingestion.

## Run

From the repository root:

```bash
PYTHONPATH=src python evals/atomic_ingest/grader.py --self-check
```

Grade another implementation with the same public function contract:

```bash
PYTHONPATH=src python evals/atomic_ingest/grader.py --candidate path/to/candidate.py
```

Exit code `0` means all required cases passed. The grader also prints a machine-readable JSON report.

## Cases

| Case | Required behavior |
| --- | --- |
| `all_valid_strict` | two valid records persist in strict mode |
| `mixed_non_strict` | valid records persist, invalid record is rejected, existing row can be updated |
| `mixed_strict_atomic` | `ValueError` is raised and persistent state remains exactly equal to the pre-call snapshot |

The strict case is deliberately stateful. It seeds `eval-existing`, then feeds a batch containing:

1. a valid new record,
2. a syntactically valid but domain-invalid record,
3. a valid record with the same `event_id` as the seeded row but changed content.

A correct strict implementation leaves only the original seeded row. The included `mutants/early_insert.py` instead writes each valid record immediately; it should pass the first two cases and fail only `mixed_strict_atomic`.

## Evidence contract

A successful `--self-check` supports this bounded claim:

> The evaluation detects a specific transactional/state-transition failure while not rejecting equivalent happy-path or non-strict behavior.

It does **not** establish real-world model performance, customer value, production scale, or independent human ownership. Those require separate receipts.
