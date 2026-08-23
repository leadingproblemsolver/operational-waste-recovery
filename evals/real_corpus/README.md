# Real-corpus repeated-work evaluation

This eval measures the existing deterministic OWR repeated-work detector against a frozen, human-validated corpus. It does **not** use model-generated labels as ground truth and it does not reinterpret inferred savings as observed outcomes.

## Required input boundary

Use sanitized real coding-agent history. Provider adapters must preserve:

- stable event id
- ISO timestamp
- repository identity
- literal prompt/task text needed by the detector
- explicit session/thread id in `metadata.session_id` (or another named key passed to the queue generator)
- provenance sufficient to recover the source event during review

Do not fabricate missing token counts, costs, session ids, or source evidence. If a provider format does not expose a field required by the canonical interaction schema, the adapter must either derive it by an explicitly documented deterministic rule or reject/mark the record rather than inventing a value.

## Evaluation sequence

```text
real sanitized provider history
→ provider adapter
→ normal OWR ingest
→ deterministic duplicate analysis
→ complete same-repo human label queue
→ human labels + evidence
→ freeze label SHA-256 manifest
→ score TP / FP / FN / TN
→ precision / recall / F1
→ confidence-stratified precision
→ inspect exact FP/FN failure classes
→ make at most one principled detector change
→ evaluate again against held-out frozen evidence
```

## 1. Generate the review queue

After the real corpus has been ingested into an isolated OWR root:

```bash
PYTHONPATH=src python scripts/prepare_real_corpus_label_queue.py \
  --root /path/to/isolated-eval-root \
  --output artifacts/label_queue.jsonl
```

The generator emits every pair inside each repository, matching the detector's comparison scope. It does not sample only likely positives. Cross-session pairs retain both source session ids.

## 2. Human-label every row

Populate exactly one label:

- `repeated_work` — materially the same work was reconstructed/re-executed rather than legitimately advanced
- `legitimate_revisit` — superficially similar work was intentionally revisited because new state/evidence required it
- `non_duplicate` — not materially the same work
- `ambiguous` — available evidence is insufficient for a defensible binary judgment

Every row also requires a short `evidence` field explaining the observable reason for the judgment.

`ambiguous` is not forced into positive/negative ground truth. It is reported but excluded from precision/recall.

## 3. Freeze before tuning

```bash
PYTHONPATH=src python scripts/freeze_real_corpus_labels.py \
  --labels artifacts/labels.jsonl \
  --source "sanitized Codex history" \
  --output artifacts/eval_dataset_manifest.json
```

Default release floor:

- at least 30 distinct work episodes
- at least 5 distinct sessions
- every label has evidence
- manifest SHA-256 matches the canonical label set

If the labels change after freezing, the hash no longer matches and the evaluation must be re-frozen before any result is published.

## 4. Score the detector

```bash
PYTHONPATH=src python scripts/evaluate_real_corpus.py \
  --root /path/to/isolated-eval-root \
  --labels artifacts/labels.jsonl \
  --manifest artifacts/eval_dataset_manifest.json \
  --output artifacts/evaluation_report.json \
  --release-floor
```

The evaluator refuses the default measurement if a persisted detector prediction is missing a human label. This prevents selective precision reporting.

## Claim boundary

A passing report supports only claims about the frozen labeled corpus and the exact detector revision measured. It does not by itself prove:

- production traffic accuracy
- accuracy on unseen provider formats
- organization-wide time/cost savings
- realized ROI
- absence of unlabeled real-world failure modes

Publish the actual metric values even if they are weak. The purpose of this eval is to expose the detector's failure surface, not to manufacture a favorable benchmark.
