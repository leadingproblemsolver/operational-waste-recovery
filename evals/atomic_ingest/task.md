# Atomic ingest evaluation

You are given an implementation of `ingest_jsonl()` with the same public contract as `src/owrp/pipeline/ingest.py`.

Your task is to make the implementation satisfy the behavioral contract below without special-casing fixture names, event IDs, or file contents.

## Contract

1. **Strict mode is atomic.** If any non-empty JSONL record is rejected, the invocation raises `ValueError` and causes **zero persistent mutations** from that invocation.
2. Atomicity includes existing rows. A valid record later in a failing strict batch must not update a row that existed before the invocation.
3. **Non-strict mode is intentionally partial.** Valid records persist, invalid records are reported/rejected, and processing continues.
4. An all-valid strict batch persists all valid records.
5. Existing canonical validation, privacy handling, size limits, adapter dispatch, and `event_id` upsert semantics must remain intact.

## Interface

The grader loads a candidate Python file and calls:

```python
ingest_jsonl(path, store, fmt="canonical", mapping=None, strict=True, redact_sensitive=False, reject_secrets=True)
```

Do not change that signature.

## Success condition

The candidate must pass all grader cases:

- `all_valid_strict`
- `mixed_non_strict`
- `mixed_strict_atomic`

The final case seeds an existing row before ingestion, then presents a strict batch containing a valid new event, an invalid event, and a valid update to the pre-existing event. After the expected failure, persistent state must be exactly the seeded state.
