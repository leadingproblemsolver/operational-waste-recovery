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

**Latest Google Cloud receipt**  
https://github.com/leadingproblemsolver/operational-waste-recovery/blob/proof/taskmaster-google-live-status/proof/taskmaster-google-live-latest.json

**Try it out**  
Use the public Cloud Run URL from the final green live receipt.

**Demo video**  
Use the final public YouTube/Vimeo URL. Only the first 4 minutes are evaluated.

---

## One-line pitch

**Recovery Taskmaster is a Gemini 3.5 + Google ADK autonomous execution agent that reconstructs persisted evidence, performs one bounded recovery action, and refuses to declare success until host code independently reconciles and verifies the resulting state.**

## Inspiration

The friction is execution continuity. Long or interrupted coding-agent sessions often reconstruct work that already happened: the same files are reread, the same failure path is rediscovered, and useful work resumes only after earlier investigation is rebuilt.

Retries create a more dangerous edge. A side effect can happen, the worker can die before recording success, and the next worker can repeat the action because local state is ambiguous.

Recovery Taskmaster turns that failure class into a complete Taskmaster workflow rather than another prompt.

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

1. prepares a deterministic sanitized coding-history + isolated workspace fixture;
2. reconstructs the strongest persisted repeated-work finding;
3. inspects the exact evidence and Recovery Capsule;
4. performs exactly one bounded recovery mutation;
5. independently rereads the result;
6. terminates only at `VERIFIED`, `BLOCKED`, or `FAILED`.

The output is not advice. It is a completed state transition with a machine-checkable receipt.

## The differentiator: reconcile before retry

The strongest failure test deliberately creates the distributed-systems ambiguity window:

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

That is the core design rule: **a tool call is not the same thing as a safely settled external state.**

## Why this is agentic rather than chat

Gemini chooses how to progress the workflow through Google ADK, but it cannot establish its own truth or certify its own side effects.

The four tools are:

- `prepare_demo_run`
- `inspect_recovery_evidence`
- `materialize_recovery_capsule`
- `verify_recovery_receipt`

The model has no arbitrary shell, arbitrary filesystem authority, output-path selection, overwrite authority, finding fabrication, or final-hash authority.

**Gemini orchestrates. Host code controls evidence, legal transitions, mutation scope, ambiguous-execution reconciliation, and settlement truth.**

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

Contest-specific runtime:

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

## Real external-system reconciliation proof

The judge workflow keeps its action deliberately bounded and deterministic. Separately, the repository includes a hostile proof harness against the **GitHub Contents API**:

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

### 1. Autonomy without broad machine authority

The main design challenge was allowing Gemini to finish the workflow without allowing it to invent evidence, choose arbitrary paths, execute arbitrary commands, or self-certify success. The solution is four narrow tools plus a host-owned state machine.

### 2. The ambiguous side-effect window

Retries are easy when failure is known. They are dangerous when an external effect may have succeeded but local acknowledgement was lost. `ACTION_PENDING` makes that ambiguity durable so a fresh process must reconcile reality before retrying.

### 3. Making the proof judgeable

The project emits exact Git SHA, Cloud Run URL/revision, live Gemini/ADK trace, Cloud Run logs and a bounded JSON receipt. A cosmetic health endpoint is not treated as the proof; the decisive condition is the deployed agent actually reaching `VERIFIED`.

## Accomplishments

Repository-level proof includes:

- host-enforced `OBSERVED → EVIDENCE_READY → ACTION_PENDING → EXECUTED → VERIFIED/BLOCKED/FAILED` state semantics;
- successful bounded action path;
- independent SHA reread verification;
- replay / no-overwrite behavior;
- missing-evidence and unauthorized-finding blocks;
- workspace escape rejection;
- hash-mismatch failure;
- hostile post-action crash recovery with `action_count == 1`;
- real GitHub external reconciliation harness;
- exact Gemini 3.5 + four-tool ADK contract tests;
- Cloud Run-compatible service/container;
- keyless GitHub OIDC → Google WIF authentication;
- public architecture, reproducible setup and claim boundaries.

Only promote hosted claims after the final receipt says `VERIFIED`.

## Pre-existing work disclosure

Operational Waste Recovery is an explicitly disclosed pre-existing dependency pinned at commit `e1c8bc8f3d9d57b87ba8adce62fe7f8ea78bc6a7`. It supplies persistence, deterministic repeated-work detection, evidence review and Recovery Capsule generation.

Contest-specific work includes the Gemini/ADK Taskmaster application layer, four bounded tool contracts, host-owned execution state machine, ambiguous-crash reconciliation path, Cloud Run service/deployment proof, external reconciliation harness, tests, receipts and submission material.

Reality Handoff and Agent Reliability Preflight informed the fail-closed design principle; their source is not copied into this submission.

## What we learned

Agentic reliability improves when autonomy is separated from authority. The model can be free to complete the workflow while deterministic boundaries decide what evidence exists, what transition is legal, where an action may occur, whether an ambiguous action must be reconciled, and whether the result actually matches the claimed receipt.

The important invariant is:

> **Do not retry uncertainty. Reconcile it.**

## What's next

For the hackathon, the next step is completion rather than feature expansion: capture the green remote Gemini/ADK `VERIFIED` receipt, record the <=4 minute proof-of-action video, submit, and freeze the artifact.

After judging, the same execution contract can be tested against broader operational exception workflows. That is outside the current hackathon claim boundary.

---

# Judge score maximization map

## 40% — Innovation & Operational Utility

Make the judge understand this before architecture:

```text
interrupted/retried agent
→ prior work or side effect becomes uncertain
→ agent reconstructs persisted evidence
→ completes the missing chore autonomously
→ checks reality before declaring success
```

Do not lead with ontology, settlement terminology, future logistics plans, or a feature list.

## 30% — Architectural Discipline & Tech Stack

Show only the decisions that differentiate the project:

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

Architectural headline:

> **The model chooses the next scoped action; host code controls truth, authority and settlement.**

## 30% — Demo & Production Readiness

The video must visibly prove:

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

The official rubric values this proof more than additional features.

---

# <=4-minute final demo script

## 0:00–0:25 — Friction

Say:

> AI agents can lose continuity after interruption or retry. That wastes time by repeating investigation, and in the worst case can repeat a side effect that already happened. Recovery Taskmaster checks persisted reality before it acts or retries.

Show the repo opening.

## 0:25–0:50 — Architecture

Say:

> Gemini 3.5 runs through Google ADK on Cloud Run. Gemini chooses the next scoped tool, but host code owns evidence truth, legal state transitions, the only permitted mutation, reconciliation and final verification.

Show the architecture and state machine:

```text
OBSERVED → EVIDENCE_READY → ACTION_PENDING → EXECUTED → VERIFIED
```

## 0:50–2:25 — Unedited live proof of action

Show Cloud Run exact service/revision, then invoke:

```text
Complete a recovery workflow for run_id judge-demo-01.
Do the work end to end and stop only at VERIFIED or an explicit blocked state.
```

Keep the real tool trace visible:

```text
prepare_demo_run
→ inspect_recovery_evidence
→ materialize_recovery_capsule
→ verify_recovery_receipt
→ VERIFIED
```

## 2:25–2:55 — Receipt

Show:

```text
bounded target path
finding/evidence IDs
action_count
expected SHA-256
observed SHA-256
VERIFIED
```

## 2:55–3:30 — The differentiating failure case

Show the hostile test/receipt:

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

> Most demos prove that a tool was called. This test proves the runtime does not blindly repeat an action when success is ambiguous.

## 3:30–3:50 — Production proof + disclosure

Show:

```text
Cloud Run URL + ready revision
GitHub Actions live receipt
public repo
pre-existing OWR disclosure
```

Say:

> The judge fixture is synthetic and sanitized for reproducibility. The agent layer, host state machine, recovery semantics and Google Cloud deployment are contest-specific work.

## 3:50–3:58 — Close

Say:

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
[x] Cloud Run deployment path + keyless auth
[ ] final live receipt says VERIFIED
[ ] public <=4 minute YouTube/Vimeo demo
[ ] final Devpost fields saved and submitted
```

Optional only after the three mandatory unchecked items:

```text
[ ] public social post with #AllThingsAgenticHackathon (+0.2 max)
[ ] public technical build post explicitly created for this hackathon (+0.2 max)
```

Do not add extra agents, providers, frontend polish or another model before submission unless the final live run proves they are necessary.

## Claim boundary

A green hosted receipt proves that the exact source was deployed to Google Cloud Run and that Gemini through Google ADK completed the bounded judge workflow to a captured `VERIFIED` terminal state. The controlled hostile tests demonstrate specific retry/reconciliation invariants.

It does not prove customer adoption, real-user corpus performance, realized financial savings, production scale, universal exactly-once semantics, logistics deployment or hackathon placement.
