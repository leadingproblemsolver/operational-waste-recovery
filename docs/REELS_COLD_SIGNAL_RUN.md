# Reels Cold-Signal Run — Batch A

## Objective

Test one narrow claim on one cold distribution surface:

> A technical viewer who sees concrete evidence of repeated AI/engineering work will take a measurable step toward inspecting or running the proof.

This is not a brand campaign and not a PMF claim. Instagram Reels is the only distribution surface in this phase.

## Proof command

From the repository root:

```bash
python scripts/reel_proof.py
```

Expected deterministic sample receipt:

- 3 synthetic telemetry events ingested;
- 1 duplicate pair detected;
- 1,500 avoidable tokens measured for that duplicate pair;
- $0.015 avoidable model cost measured for that duplicate pair;
- 1 reusable context capsule generated for `payments-api`.

These are deterministic measurements over the bundled synthetic sample only. They are not realized labor savings, ROI, or production-adoption evidence.

## What to record

Keep the proof sequence visible and fast:

1. Show the two near-duplicate Redis debugging prompts in `data/sample_events.jsonl`.
2. Run `python scripts/reel_proof.py`.
3. Hold on `duplicate_pairs: 1` and `avoidable_tokens: 1500`.
4. Hold on the generated `payments-api` context capsule.
5. CTA: `See the proof / run the scan`.

Do not spend reel time on architecture, logos, generic AI claims, setup explanation, or a feature list.

## Controlled Batch A

Everything except the opening hook stays fixed: same proof, same CTA, same product, same account, same general duration.

### A1 — pain

Hook:

`AI made coding faster, but I noticed I was solving the same problems twice.`

Then immediately show the two Redis prompts and proof command.

### A2 — proof

Hook:

`I fed a tiny engineering-work history into this and it caught the duplicate immediately.`

Then show the output before explaining what the tool is.

### A3 — challenge

Hook:

`How much of your AI-assisted work is actually work you already did?`

Then show the duplicate pair and generated context capsule.

## Evidence priority

Judge the batch in this order:

`payment > repeat use > first-value event > link click > profile visit > qualified comment > save > share > views`

Views alone cannot validate the wedge.

## Decision rules

- Payment or repeat use -> continue the winning wedge/hook.
- First-value use without return/payment -> preserve acquisition; test return behavior.
- Link clicks without first value -> fix activation, not distribution.
- Saves/profile visits/qualified comments without clicks -> fix proposition or CTA.
- All three reels with weak reach -> iterate hook/format; do not kill the product from low distribution.
- Meaningful cold reach with zero qualified behavior -> kill/change the current angle or wedge before adding MarketOS, SEO, or multi-channel distribution.

## Expansion gate

Do not integrate MarketOS, SEO tooling, multi-channel distribution, or a full Reel ontology/compiler until actual receipts identify one of those as the active bottleneck.
