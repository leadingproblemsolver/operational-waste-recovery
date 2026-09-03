# Foundation Ownership Gate — Atomic JSONL Ingest

## Goal
Demonstrate that the operator can reconstruct and repair one production-relevant persistence invariant without relying on a tutorial or special-casing fixtures.

## Public contract
Use the existing evaluation spec:

- `evals/atomic_ingest/task.md`
- grader: `evals/atomic_ingest/grader.py`
- candidate: `proof/foundation-ownership/candidate.py`

The required invariant is:

> In strict mode, if any non-empty JSONL record is rejected, the invocation must leave persistent state exactly as it was before the invocation.

This includes pre-existing rows that a later valid record in the same failing batch would otherwise update.

## 35-minute ownership block

1. **Reconstruct** the execution path from file read → adapt → sanitize → validate → persistence.
2. **Predict** why the candidate violates the strict atomicity invariant.
3. **Patch only the causal surface** in `candidate.py`; preserve non-strict partial-ingest behavior and existing upsert semantics.
4. **Run the machine grader**:

```bash
python evals/atomic_ingest/grader.py --candidate proof/foundation-ownership/candidate.py
```

Required result: `3/3` cases pass.

5. Record the human explanation below after the passing receipt exists.

## Human reconstruction receipt

- **Failure cause:** PENDING
- **Invariant:** strict failure causes zero persistent mutations, including updates to pre-existing rows
- **Why the patch works:** PENDING
- **What non-strict mode still does:** PENDING
- **Remaining limitation:** PENDING
- **Grader result:** PENDING

## Evidence boundary
A passing result proves this bounded atomic-ingest contract against the repository grader. It does not prove production-scale concurrency, crash-atomicity across external systems, or generalized database expertise.
