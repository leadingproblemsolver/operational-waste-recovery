# Recovery Taskmaster — Final Devpost Pack

## Project overview — paste into Devpost

**Project name**  
Recovery Taskmaster

**Tagline**  
An agent that checks reality before retrying: Gemini + ADK recovers persisted work, takes one bounded action, and independently verifies the result.

**Category**  
Taskmaster

**Repository**  
https://github.com/leadingproblemsolver/operational-waste-recovery

**Built with**  
Gemini 3.5 Flash, Google Agent Development Kit (ADK), Vertex AI, Google Cloud Run, FastAPI, Python, SQLite, GitHub Actions, Workload Identity Federation, SHA-256 receipts

**Verified Cloud Run service**  
https://recovery-taskmaster-dzoo5fey5q-ww.a.run.app

**Verified Cloud Run revision**  
`recovery-taskmaster-00002-2v6`

**Verified source commit**  
`74a01bcf11bc5c6a09462377f65bd6d8b1707a84`

**Live receipt**  
https://github.com/leadingproblemsolver/operational-waste-recovery/blob/proof/taskmaster-google-live-status/proof/taskmaster-google-live-latest.json

**Demo video**  
Add the final public YouTube/Vimeo URL. Only the first 4 minutes are evaluated.

---

## One-line pitch

**Recovery Taskmaster is a Gemini 3.5 + Google ADK autonomous execution agent that reconstructs persisted evidence, performs one bounded recovery action, and refuses to declare success until host code independently reconciles and verifies the resulting state.**

## Inspiration

Interrupted or retried coding-agent work often reconstructs investigation that already happened. That wastes time. The dangerous edge is worse: a side effect can succeed, the worker can die before recording success, and a fresh worker can blindly repeat the action.

Recovery Taskmaster turns that failure class into a complete workflow rather than another prompt.

## What it does

For one requested `run_id`, Gemini works through four scoped ADK tools while deterministic host code owns the execution contract:

```text
OBSERVED
→ EVIDENCE_READY
→ ACTION_PENDING
→ EXECUTED
→ VERIFIED | FAILED

missing/unauthorized evidence or illegal transition → BLOCKED
```

The agent autonomously:

1. reconstructs persisted repeated-work evidence;
2. inspects the exact evidence and Recovery Capsule;
3. performs exactly one bounded recovery mutation;
4. independently rereads the result;
5. terminates only at `VERIFIED`, `BLOCKED`, or `FAILED`.

The output is not advice. It is a completed state transition with a machine-checkable receipt.

## The differentiator: reconcile before retry

The hostile crash test deliberately creates the ambiguous side-effect window:

```text
persist ACTION_PENDING
→ perform side effect
→ crash before EXECUTED is persisted
→ start fresh process
→ observe ACTION_PENDING
→ reread target before retry
→ effect already exists
→ do not execute again
→ verify expected SHA == observed SHA
→ VERIFIED with action_count == 1
```

**A tool call is not the same thing as a safely settled external state.**

## Why this is agentic rather than chat

Gemini chooses how to progress the workflow through Google ADK, but it cannot establish its own truth or certify its own side effects.

The four tools are:

- `prepare_demo_run`
- `inspect_recovery_evidence`
- `materialize_recovery_capsule`
- `verify_recovery_receipt`

The model has no arbitrary shell, arbitrary filesystem authority, output-path selection, overwrite authority, finding fabrication, or final-hash authority.

> **Gemini orchestrates. Host code controls evidence, legal transitions, mutation scope, ambiguous-execution reconciliation, and settlement truth.**

## Architecture

```text
Operator
  ↓
Google Cloud Run ADK service
  ↓
Gemini 3.5 Flash
  ↓
scoped tool call
  ↓
Host-owned state machine
  ↓
persisted evidence / bounded action target
  ↓
independent reread
  ↓
VERIFIED | BLOCKED | FAILED
```

Reusable execution contract:

```text
persisted evidence
→ host-enforced current state
→ bounded action
→ reconcile / independent reread
→ verified settlement
→ durable receipt
```

## Google stack

- Gemini 3.5 Flash (`gemini-3.5-flash`)
- Google ADK
- Vertex AI
- Google Cloud Run
- FastAPI ADK service
- four scoped Python tools
- isolated `/tmp/recovery-taskmaster/<run_id>` workspaces
- GitHub Actions deployment/live-proof workflow
- SHA-256 action and verification receipts

Cloud authentication is keyless:

```text
GitHub OIDC
→ Google Workload Identity Federation
→ recovery-taskmaster-deployer@signalops-506419.iam.gserviceaccount.com
```

No long-lived service-account JSON key is required by the live workflow.

## Verified Google Cloud proof

The latest live workflow completed successfully:

```text
proof_status: VERIFIED
workflow_status: success
source_commit_sha: 74a01bcf11bc5c6a09462377f65bd6d8b1707a84
cloud_run_revision: recovery-taskmaster-00002-2v6
verified_terminal_observed: true
```

The workflow deployed the exact source to Google Cloud Run, captured the public service URL/revision, invoked the deployed Gemini/ADK service, observed terminal `VERIFIED`, captured Cloud Run logs, and published the receipt pack.

`/healthz` still returned 404, but that probe is intentionally advisory because it does not affect the actual judged functionality: the deployed agent execution itself completed successfully.

## Real external-system reconciliation proof

A separate hostile harness applies the same ambiguity boundary to the **GitHub Contents API**:

```text
persist ACTION_PENDING
→ perform one real remote GitHub mutation
→ terminate before local success settlement
→ fresh process GETs remote state before retry
→ verify content hash
→ require exactly one remote mutation commit
→ emit receipt
→ clean up ephemeral proof branch
```

This demonstrates the same reconcile-before-retry boundary against a queryable external system without claiming universal exactly-once semantics.

## Challenges

### Autonomy without broad machine authority

The main design challenge was allowing Gemini to finish the workflow without allowing it to invent evidence, choose arbitrary paths, execute arbitrary commands, or self-certify success. The solution is four narrow tools plus a host-owned state machine.

### The ambiguous side-effect window

Retries are easy when failure is known. They are dangerous when an external effect may have succeeded but local acknowledgement was lost. `ACTION_PENDING` makes that ambiguity durable so a fresh process must reconcile reality before retrying.

### Making the proof judgeable

The project emits the exact Git SHA, Cloud Run URL/revision, live Gemini/ADK trace, Cloud Run logs and a bounded JSON receipt. The decisive proof is not a cosmetic endpoint; it is the deployed agent actually reaching `VERIFIED`.

## Accomplishments

- host-enforced `OBSERVED → EVIDENCE_READY → ACTION_PENDING → EXECUTED → VERIFIED/BLOCKED/FAILED` semantics;
- successful bounded action path;
- independent SHA reread verification;
- replay / no-overwrite behavior;
- missing-evidence and unauthorized-finding blocks;
- workspace escape rejection;
- hash-mismatch failure;
- hostile post-action crash recovery with `action_count == 1`;
- real GitHub external reconciliation harness;
- Gemini 3.5 + four-tool ADK contract tests;
- keyless GitHub OIDC → Google WIF authentication;
- **verified remote Gemini/ADK execution on Google Cloud Run**;
- public architecture, reproducible setup and claim boundaries.

## Pre-existing work disclosure

Operational Waste Recovery is an explicitly disclosed pre-existing dependency pinned at commit `e1c8bc8f3d9d57b87ba8adce62fe7f8ea78bc6a7`. It supplies persistence, deterministic repeated-work detection, evidence review and Recovery Capsule generation.

Contest-specific work includes the Gemini/ADK Taskmaster layer, four bounded tool contracts, host-owned execution state machine, ambiguous-crash reconciliation path, Cloud Run service/deployment proof, external reconciliation harness, tests, receipts and submission material.

## What we learned

Agentic reliability improves when autonomy is separated from authority. The model can complete the workflow while deterministic boundaries decide what evidence exists, what transition is legal, where an action may occur, whether ambiguity must be reconciled, and whether the result actually matches the claimed receipt.

> **Do not retry uncertainty. Reconcile it.**

## What's next

For the hackathon, no more product building is required. The remaining work is only:

```text
record <=4 minute proof-of-action video
→ add public video URL
→ submit Devpost
→ freeze
```

---

# Judge score maximization map

## 40% — Innovation & Operational Utility

Lead with:

```text
interrupted/retried agent
→ prior work or side effect becomes uncertain
→ agent reconstructs persisted evidence
→ completes the missing chore autonomously
→ checks reality before declaring success
```

Do not lead with ontology, future logistics plans, or a feature list.

## 30% — Architectural Discipline & Tech Stack

Show:

```text
Gemini 3.5 Flash + Google ADK
Vertex AI + Cloud Run
four scoped tools
host-owned state machine
ACTION_PENDING before mutation
reconcile-before-retry
bounded path authority
independent reread / SHA verification
keyless OIDC/WIF authentication
```

## 30% — Demo & Production Readiness

Show undeniable proof:

```text
public repository
architecture diagram
Google Cloud Run exact service/revision
unedited live Gemini/ADK execution
actual tool sequence
bounded action
VERIFIED terminal state
receipt / hash equality
hostile ACTION_PENDING crash case
```

---

# <=4-minute final demo script

## 0:00–0:25 — Friction

> AI agents can lose continuity after interruption or retry. That wastes time by repeating investigation, and in the worst case can repeat a side effect that already happened. Recovery Taskmaster checks persisted reality before it acts or retries.

Show the repo opening.

## 0:25–0:50 — Architecture

> Gemini 3.5 runs through Google ADK on Cloud Run. Gemini chooses the next scoped tool, but host code owns evidence truth, legal state transitions, the only permitted mutation, reconciliation and final verification.

Show:

```text
OBSERVED → EVIDENCE_READY → ACTION_PENDING → EXECUTED → VERIFIED
```

## 0:50–2:25 — Unedited live proof of action

Show Cloud Run revision `recovery-taskmaster-00002-2v6`, then invoke:

```text
Complete a recovery workflow for run_id judge-demo-01.
Do the work end to end and stop only at VERIFIED or an explicit blocked state.
```

Keep the real tool sequence visible:

```text
prepare_demo_run
→ inspect_recovery_evidence
→ materialize_recovery_capsule
→ verify_recovery_receipt
→ VERIFIED
```

## 2:25–2:55 — Receipt

Show the bounded target, action count, expected SHA, observed SHA and `VERIFIED`.

## 2:55–3:30 — Differentiating failure case

Show:

```text
ACTION_PENDING
→ side effect exists
→ simulated process death
→ fresh process
→ reconcile before retry
→ action_count == 1
→ VERIFIED
```

Say:

> Most demos prove that a tool was called. This proves the runtime does not blindly repeat an action when success is ambiguous.

## 3:30–3:50 — Production proof + disclosure

Show the exact Cloud Run URL/revision, green live receipt, public repo and pre-existing OWR disclosure.

## 3:50–3:58 — Close

> Recovery Taskmaster is proof-carrying autonomy: do not retry uncertainty—reconcile it.

Stop.

---

# Submission gate

```text
[x] Taskmaster category
[x] public repository
[x] clean architecture diagram
[x] reproducible setup
[x] pre-existing-work disclosure
[x] Gemini 3.5 + Google ADK + Google Cloud stack
[x] host-state / crash-reconciliation proof
[x] exact Cloud Run deployment receipt
[x] remote Gemini/ADK run reaches VERIFIED
[ ] public <=4 minute YouTube/Vimeo demo
[ ] final Devpost fields saved and submitted
```

Optional only after submission-critical work:

```text
[ ] public social post with #AllThingsAgenticHackathon (+0.2 max)
[ ] public technical build post explicitly created for this hackathon (+0.2 max)
```

Do not add extra agents, providers, frontend polish or another model before submission.

## Claim boundary

The green hosted receipt proves that the exact source was deployed to Google Cloud Run and that Gemini through Google ADK completed the bounded judge workflow to a captured `VERIFIED` terminal state. Controlled hostile tests demonstrate specific retry/reconciliation invariants.

It does not prove customer adoption, real-user corpus performance, realized financial savings, production scale, universal exactly-once semantics, logistics deployment or hackathon placement.
