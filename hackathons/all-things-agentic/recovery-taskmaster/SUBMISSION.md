# Recovery Taskmaster — Final Devpost Pack

## Project overview — paste into Devpost

**Project name**  
Recovery Taskmaster

**Tagline**  
Gemini + ADK turns persisted evidence into one bounded action and independently verified settlement.

**Category**  
Taskmaster

**Repository**  
https://github.com/leadingproblemsolver/operational-waste-recovery

**Built with**  
Gemini 3.5 Flash, Google Agent Development Kit (ADK), Vertex AI, Google Cloud Run, FastAPI, Python, SQLite, GitHub Actions, SHA-256 receipts

**Try it out**  
Use the final Cloud Run URL from the live receipt pack. Do not paste a placeholder into Devpost.

**Demo video**  
Use the final public YouTube/Vimeo URL. Keep the evaluated content under 4 minutes.

---

## One-line pitch

Recovery Taskmaster is a Gemini 3.5 + Google ADK proof-carrying execution agent that detects already-completed investigation, reconstructs the exact persisted evidence, performs exactly one bounded recovery action, and independently rereads the resulting artifact before terminating at `VERIFIED`.

## Inspiration

The friction is execution continuity. Long or interrupted coding-agent sessions repeatedly lose operational context: the same files are reread, the same failure path is rediscovered, and useful work resumes only after earlier investigation is reconstructed.

Instead of solving that with another prompt, Recovery Taskmaster treats continuity loss as a complete workflow that an autonomous agent must finish.

This is also the execution pattern we want to preserve in our broader Logistinfra direction: evidence must survive into action, authority must stay bounded, and a workflow is not settled until external state has been reread and verified. The hackathon submission stays deliberately narrow: coding continuity is the reproducible BYOF case; proof-carrying execution is the reusable systems contribution.

## What it does

For one requested `run_id`, the agent autonomously:

1. prepares a deterministic sanitized coding-history + isolated workspace fixture;
2. reads the strongest persisted repeated-work finding;
3. inspects the exact evidence episodes and Recovery Capsule;
4. blocks if required evidence is missing;
5. materializes exactly one `.recovery/recovery-<finding>.md` artifact;
6. independently rereads that artifact and recomputes its SHA-256;
7. terminates only at `VERIFIED` or an explicit `BLOCKED` / `FAILED` state.

The output is not advice. It is a completed state transition with an independently checked receipt.

## Why this is agentic rather than chat

Gemini decides how to complete the workflow through Google ADK, but it is never trusted to establish evidence truth or certify its own side effects.

The agent has exactly four tools:

- `prepare_demo_run`
- `inspect_recovery_evidence`
- `materialize_recovery_capsule`
- `verify_recovery_receipt`

It has no arbitrary shell, no arbitrary filesystem tool, no path-selection authority, no overwrite authority, and no ability to manufacture the final hash.

The agent therefore owns **workflow completion**, while deterministic execution boundaries own **evidence, action scope and settlement truth**.

## Architecture / execution contract

```text
Judge / operator
      ↓
Cloud Run ADK service
      ↓
Gemini 3.5 Flash
      ↓
prepare persisted evidence
      ↓
inspect exact evidence
      ↓
materialize one bounded recovery action
      ↓
independent external reread
      ↓
VERIFIED | BLOCKED | FAILED
```

The reusable execution contract is:

```text
persisted evidence → current state → scoped action → execution → reread → verified settlement → receipt
```

## How we built it

**Contest-specific stack**

- Gemini 3.5 Flash (`gemini-3.5-flash`)
- Google ADK
- Vertex AI
- Google Cloud Run
- FastAPI ADK service
- four scoped Python tools
- isolated `/tmp/recovery-taskmaster/<run_id>` workspaces
- GitHub Actions deployment / live proof workflow
- SHA-256 action and verification receipts

**Pre-existing dependency, explicitly disclosed**

Operational Waste Recovery is pinned at commit `e1c8bc8f3d9d57b87ba8adce62fe7f8ea78bc6a7`. It supplies canonical persistence, deterministic repeated-work detection, evidence review and Recovery Capsule generation.

The Gemini/ADK agent layer, autonomous workflow, scoped tools, action verification, Cloud Run service/deployment path, tests and hackathon submission material were created for this contest.

Reality Handoff and Agent Reliability Preflight informed the fail-closed design principle that deterministic evidence gates outrank model assertions; their source is not copied into the submission.

## Data sources and truth boundary

The public judge/demo fixture is intentionally synthetic and sanitized. It contains two repeated debugging investigations over the same retry-path source file so the workflow can be reproduced without exposing private history.

The submission does **not** relabel synthetic evidence as real-user data and does not claim customer adoption, realized savings, production scale, logistics-operator deployment or hackathon placement.

Inside the run, persisted OWR state determines whether a finding and Recovery Capsule exist. Gemini cannot create finding IDs, source evidence, the output path or the verification digest.

## Architectural discipline

The system is designed around narrow authority and explicit failure semantics:

- persisted state is authoritative;
- `run_id` is validated;
- every path is contained under the isolated run workspace;
- model tools are strictly scoped;
- missing evidence produces `BLOCKED`, not a guessed action;
- the sole write target is deterministic;
- replay produces `ALREADY_EXISTS` and preserves the original artifact;
- the verification tool independently rereads the file;
- hash mismatch produces `FAILED`;
- observed recurrence remains separate from inferred avoidable work.

State machine:

```text
OBSERVED
→ EVIDENCE_PRESENT | BLOCKED
→ ACTION_READY
→ EXECUTED | ALREADY_EXISTS
→ INDEPENDENT_REREAD
→ VERIFIED | FAILED
```

## Challenges

The central challenge was allowing meaningful autonomy without giving the model broad machine authority. The solution was to make Gemini autonomous over **workflow ordering and completion**, while deterministic tools retain authority over evidence existence, path containment, the only permitted mutation and final settlement verification.

A second challenge was making the proof judgeable. The project therefore emits machine-checkable receipts tied to the exact Git SHA, Cloud Run revision, health response, live tool trace and terminal verification state.

## Accomplishments

Repository-level proof already includes:

- successful bounded action test;
- independent SHA reread verification;
- replay / idempotency test;
- missing-evidence block with zero mutation;
- workspace escape rejection;
- exact Gemini model + four-tool ADK contract test;
- Cloud Run-compatible FastAPI service and container path;
- public architecture and reproducible setup documentation;
- exact contest/pre-existing-work disclosure.

Only promote the following claims after their receipts actually exist:

```text
credentialed Gemini/ADK run       → pending until green live receipt
public Cloud Run URL              → pending until green live receipt
live remote VERIFIED terminal     → pending until green live receipt
public demo video                 → pending until uploaded
Devpost submitted receipt         → pending until submitted
judge result / placement          → never pre-claim
```

## What we learned

Agentic reliability improves when autonomy is separated from authority. A model can be free to complete the workflow while deterministic boundaries decide whether evidence exists, where an action may occur, whether it may be repeated and whether the resulting external state actually matches the claimed receipt.

That pattern is more valuable to us than adding more agents: `evidence → action → reread → verified settlement` is a reusable execution primitive for larger operational systems.

## What's next

The immediate next step is not feature expansion. It is proof completion: deploy the exact submission head to Cloud Run, capture one remote Gemini/ADK run that reaches `VERIFIED`, record the unedited proof of action, submit, and freeze the hackathon artifact pending external judgment.

After submission, the same execution contract can be tested against real operational exception workflows as part of Logistinfra, but that is explicitly outside the current hackathon claim boundary.

---

# Judge score maximization map

## 40% — Innovation & Operational Utility

Make the judge see, in this order:

```text
real personal friction
→ agent intercepts the multi-step chore
→ no human manually orders the tools
→ real file mutation occurs
→ workflow terminates only after independent verification
```

Do not spend demo time describing future logistics use. One sentence of strategic transferability is enough.

## 30% — Architectural Discipline & Tech Stack

Show these concrete engineering decisions:

```text
Gemini 3.5 Flash
Google ADK
Vertex AI
Cloud Run
persisted SQLite evidence
four isolated tools
bounded filesystem authority
fail-closed missing evidence
idempotent replay
independent SHA reread
```

The architectural headline is:

**The model controls orchestration; deterministic boundaries control truth, authority and settlement.**

## 30% — Demo & Production Readiness

The video must visibly prove:

```text
public repository
architecture diagram
Google Cloud / Cloud Run deployment
exact public service URL or Cloud Run console
unedited live agent execution
actual tool calls
real bounded file action
VERIFIED hash reread
exact revision / receipt evidence
```

Do not submit a slideshow-only demo.

---

# <=4-minute final demo script

## 0:00–0:25 — Friction + success criterion

Say:

> Interrupted coding-agent work often reconstructs investigation that already happened. Recovery Taskmaster turns that continuity failure into an autonomous execution workflow. Success is not a response: the agent must create one evidence-linked recovery artifact and independently verify the resulting state.

Show the repository root Taskmaster callout and pre-existing-work disclosure.

## 0:25–0:50 — Architecture

Show the Mermaid architecture and say:

> Gemini 3.5 runs through Google ADK on Cloud Run. Gemini controls orchestration. Persisted evidence, path containment, the only permitted mutation, replay semantics and final SHA verification remain deterministic.

## 0:50–2:20 — Unedited live run

Show Cloud Run / Google Cloud, then invoke:

```text
Complete a recovery workflow for run_id judge-demo-01. Do the work end to end and stop only at VERIFIED or an explicit blocked state.
```

Keep the complete tool trace visible:

```text
prepare_demo_run
→ inspect_recovery_evidence
→ materialize_recovery_capsule
→ verify_recovery_receipt
→ VERIFIED
```

## 2:20–2:50 — Proof of action

Show:

```text
bounded .recovery target path
finding/evidence IDs
EXECUTED
SHA-256 receipt
overwritten: false
expected_sha256 == actual_sha256
VERIFIED
```

## 2:50–3:15 — Failure tolerance

Show or point to green tests proving:

```text
missing finding → BLOCKED / zero mutation
replay → ALREADY_EXISTS / same hash / no overwrite
invalid run_id → workspace escape rejected
hash mismatch → FAILED
```

## 3:15–3:40 — Production proof

Show:

```text
Cloud Run service
exact revision
public URL
/healthz → 200
GitHub Actions exact-head live receipt
Cloud Run logs / trace
receipt-index.json
```

## 3:40–3:55 — Close

Say:

> Recovery Taskmaster demonstrates proof-carrying autonomy: the model can finish the workflow, but it cannot invent the evidence, escape its authority boundary or certify its own work. Every successful action ends in independently verified settlement.

Stop.

---

# Submission gate

Do not press final submit until all mandatory items below are true:

```text
[ ] Taskmaster selected as the single category
[ ] public repository URL entered
[ ] architecture diagram visible in README
[ ] reproducible setup instructions visible
[ ] pre-existing OWR disclosure visible
[ ] Gemini 3.5 / Google ADK / Cloud Run named explicitly
[ ] final Cloud Run receipt exists OR video clearly proves Google Cloud deployment
[ ] public YouTube/Vimeo demo URL entered
[ ] demo <= 4 minutes
[ ] project description matches only proven behavior
[ ] final submission saved and submitted
```

Optional score additions that do not distort the build:

```text
[ ] one public social post with #AllThingsAgenticHackathon (+0.2 max)
[ ] one public technical build post explicitly saying it was created for this hackathon (+0.2 max)
```

Do **not** integrate additional Google AI models solely for bonus points. The existing deterministic verifier is architecturally stronger than replacing verification with another model.

---

# Social post — ready to publish after the live receipt exists

> Built Recovery Taskmaster for the #AllThingsAgenticHackathon: a Gemini 3.5 + Google ADK execution agent that recovers persisted evidence, performs one bounded recovery action, and independently rereads the result before it can declare the workflow complete. The core design rule is simple: the model controls orchestration; deterministic boundaries control evidence, authority, and settlement. Built on Vertex AI + Cloud Run. Repo/demo: [ADD FINAL LINKS].

---

# Claim boundary

A green hosted demo proves that Gemini through Google ADK completed this bounded workflow on Google Cloud, created the recovery artifact, and independently verified its receipt. It does **not** prove customer adoption, real-user corpus performance, realized financial savings, production scale, logistics-operator deployment, or hackathon placement.
