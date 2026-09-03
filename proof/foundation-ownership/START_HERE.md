# START HERE

Do not read the reference implementation before attempting the candidate.

Open only:

1. `evals/atomic_ingest/task.md`
2. `proof/foundation-ownership/candidate.py`

Before changing code, write down:

- the first persistent mutation in the current path;
- the point at which strict failure becomes known;
- one sentence explaining why those two points are ordered incorrectly.

Then make the smallest patch that preserves non-strict partial ingestion.
