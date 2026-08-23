# Real-Corpus Duplicate-Work Evaluation

## Objective

Evaluate the existing OWR lexical duplicate detector against a **frozen human-labeled set of real coding-agent work pairs** without inflating ambiguous or unreviewed pairs into accuracy claims.

This is an evaluation harness, not a synthetic accuracy demonstration. Do not publish precision/recall until the labels come from real sanitized sessions and were frozen before detector changes.

## Input sequence

1. Export real Codex / Claude Code / Cursor (or equivalent) session history.
2. Sanitize secrets and private customer information without rewriting the work sequence.
3. Normalize/ingest into OWR while preserving event IDs and source provenance.
4. Construct candidate work pairs for human review.
5. **Before changing the detector**, freeze `labels.jsonl` in this schema:

```json
{"left_id":"evt-001","right_id":"evt-008","label":"duplicate","rationale":"same auth failure investigation reconstructed"}
{"left_id":"evt-002","right_id":"evt-009","label":"legitimate_revisit","rationale":"same file revisited after a new failing test changed the state"}
{"left_id":"evt-004","right_id":"evt-011","label":"ambiguous","rationale":"overlap exists but causal duplication is not defensible"}
```

Allowed labels:

- `duplicate`: human reviewer judges that the later work materially reconstructed/repeated already-established work.
- `legitimate_revisit`: overlap exists but the revisit is justified by changed state, new evidence, or necessary verification.
- `ambiguous`: evidence is insufficient for a defensible positive/negative judgment. These pairs are excluded from accuracy denominators.

Pair order is canonicalized, so `(A,B)` and `(B,A)` are the same label and duplicate labels are rejected.

## Run

After installing the package in the normal repo environment:

```bash
python scripts/real_corpus_eval.py \
  --root . \
  --labels evals/real_corpus/labels.jsonl \
  --threshold 0.72 \
  --output artifacts/real-corpus-eval.json
```

The command reruns the current detector at the supplied threshold, hashes the exact label file, and reports:

- TP / FP / FN / TN on reviewed non-ambiguous pairs
- precision / recall / F1 when denominators exist
- precision buckets for `>=0.90`, `0.80-0.90`, and detector-threshold-to-`0.80`
- count/list of detector predictions that were not included in the frozen label set
- exact label-file SHA-256

Unreviewed predictions are **not silently counted as false positives**. They remain an explicit review queue.

## Minimum evidence gate

Do not call this "real-corpus accuracy" unless all are true:

- the sessions are real rather than manufactured for the test;
- labels were frozen before detector tuning;
- at least 15 work episodes are represented, with 30 preferred;
- both positive (`duplicate`) and negative (`legitimate_revisit`) judgments exist;
- ambiguous pairs are preserved rather than forced into a binary label;
- every labeled pair can be traced back to source events;
- any post-baseline algorithm change is evaluated separately from the baseline.

For a stronger receipt, split the frozen labels into a development portion and held-out portion before tuning, make at most one principled detector change, and report both before/after metrics on the held-out set.

## Failure taxonomy to capture

At minimum classify each FP/FN into one of:

- `same_words_different_goal`
- `necessary_reverification`
- `state_changed_since_prior_work`
- `same_goal_different_subproblem`
- `lexical_paraphrase_missed`
- `context_reconstruction_without_prompt_overlap`
- `insufficient_source_evidence`
- `other`

Do not change the detector until a failure class is understood and occurs often enough to justify the intervention.

## Claim boundary

A scored run proves detector behavior only against the supplied frozen human labels. It does **not** prove general population accuracy, realized labor/time savings, customer ROI, or production-scale reliability.
