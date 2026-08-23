# Human Ownership Gate 01 — OWR Execution Path + Atomic Failure

**Purpose:** create evidence of independent technical ownership without pretending AI-assisted repository work is unaided authorship.

**Timebox:** 45 minutes total. Do this without generated notes or an AI answer open beside you.

## Part A — execution-path defense (10 minutes)

Without opening `docs/ARCHITECTURE.md`, explain aloud or in your own written notes:

1. how one external JSONL record becomes a canonical `Interaction`;
2. where secret rejection/redaction occurs;
3. what makes strict ingestion atomic;
4. what makes replay/idempotency possible;
5. where duplicate analysis reads state from;
6. why duplicate analysis is repo-scoped;
7. how a context capsule is derived;
8. how the result reaches CLI/report/API consumers.

Then open the code and mark each claim as `CORRECT`, `PARTIAL`, or `WRONG`. Preserve the corrections; do not erase them.

## Part B — predict the failure before execution (10 minutes)

Read only the public contract in `evals/atomic_ingest/README.md`.

Before running anything, record your prediction for both implementations:

| Candidate | all_valid_strict | mixed_non_strict | mixed_strict_atomic | Why? |
| --- | --- | --- | --- | --- |
| reference |  |  |  |  |
| `mutants/early_insert.py` |  |  |  |  |

Your explanation must state the persistent-state invariant, not merely "the test should fail."

## Part C — execute and diagnose (10 minutes)

Run:

```bash
PYTHONPATH=src python evals/atomic_ingest/grader.py --self-check
```

Capture:

- command;
- exit code;
- machine-readable result;
- whether your prediction matched;
- the precise state-transition bug in the mutant.

If your prediction was wrong, preserve the wrong prediction and explain what code behavior corrected your model.

## Part D — reconstruction test (15 minutes)

Create a temporary file **outside the repository's committed paths** and implement the smallest strict-ingest algorithm you believe satisfies the public contract. You may inspect type signatures and fixtures, but do not copy the existing `ingest_jsonl` implementation.

Grade it with:

```bash
PYTHONPATH=src python evals/atomic_ingest/grader.py --candidate /path/to/your_candidate.py
```

You pass only if all three grader cases pass.

Do **not** commit the candidate merely to manufacture activity. The receipt is the grader output plus your prediction/diagnosis.

## Acceptance gate

PASS requires all of the following:

- execution-path explanation corrected against real code;
- explicit atomicity invariant stated correctly;
- pre-run prediction preserved;
- self-check run captured;
- independent candidate passes all three grader cases;
- you can explain why early writes are safe in non-strict mode but violate strict-mode atomicity.

## Receipt schema

Save a local note or screen recording with:

```yaml
ownership_gate_01:
  attempted_at: <timestamp>
  execution_path_self_score:
    correct: <n>
    partial: <n>
    wrong: <n>
  prediction_before_run: <preserved text/table>
  self_check_exit_code: <int>
  self_check_result: <json or file path>
  candidate_grader_exit_code: <int>
  candidate_grader_result: <json or file path>
  diagnosis: <your own words>
  correction_to_my_mental_model: <your own words>
  pass: true|false
```

## Claim boundary

Completing this gate does not prove general software-engineering mastery. It is a bounded receipt that you can reconstruct one OWR execution invariant, predict a failure, diagnose it, and implement a conforming behavior under an existing grader.
