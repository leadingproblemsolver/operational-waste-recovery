# Recovery Agent — Agents for Humans Submission Pack

## Project name
Recovery Agent

## Track
Professional Agents

## One-line pitch
Recovery Agent uses Strands to detect when coding-agent work is being reconstructed, restore the exact prior evidence, and surface only when one bounded repository action requires human approval.

## Problem
Coding agents make investigation cheap to start but expensive to reconstruct. Across interrupted or multi-session engineering work, developers and agents can reread the same files, rediscover the same failure path, and spend another model run rebuilding context that already exists.

Recovery Agent treats that as a continuity problem: before more work is reconstructed, recover the persisted evidence, prove whether the recovery path is ready, propose one bounded action, and require a human at the actual mutation boundary.

## Who it is for
Developers and technical operators who use coding agents across long, interrupted, or multi-session engineering work.

## Why it matters
The failure is not merely extra tokens. Reconstructed investigation also increases cognitive load and makes it easier to act on partial or stale context. Recovery Agent preserves the earlier evidence and prevents a model from silently converting its own interpretation into repository state.

## End-to-end workflow

```text
coding-agent history + current repo state
→ deterministic OWR repeated-work evidence
→ exact episodes + Recovery Capsule
→ Strands agent orchestration
→ deterministic Recovery Preflight
→ BLOCKED or READY_FOR_PROPOSAL
→ one evidence-linked RecoveryAction
→ Strands HumanInTheLoop
→ DENY = zero mutation
→ APPROVE = executor rereads current persisted evidence
→ one bounded .recovery note
→ execution receipt
→ replay = ALREADY_EXISTS, no overwrite
```

## Judging criteria → proof map

### 1. Technical Implementation
- real Strands `Agent` orchestration;
- five allow-listed read/preflight/proposal tools and exactly one mutating tool;
- native Strands `HumanInTheLoop` guards the mutating tool;
- deterministic preflight can veto model action;
- execution rereads current persisted evidence before mutation;
- path containment and replay-safe no-overwrite behavior;
- dedicated CI plus deterministic hostile judge scenarios;
- credentialed Strands/OpenAI live receipt workflow staged.

### 2. Design
The product experience is deliberately one workflow rather than a dashboard or generic agent framework: recover evidence → inspect readiness → propose one action → human decision → exact receipt. The human sees the agent only when a consequential repository mutation is proposed.

### 3. Potential Impact
The target problem is concrete: repeated/reconstructed engineering investigation across coding-agent sessions. The system restores prior context and makes the next action inspectable rather than claiming generic productivity gains. No realized time/cost savings are claimed without measurement.

### 4. Creativity & Originality
Recovery Agent is not another coding copilot that generates more code. It acts as a continuity control layer that identifies already-completed cognition, restores evidence, and gates one bounded next action against current truth.

### 5. Presentation
The demo is structured around one successful run plus two hostile branches: denial and stale evidence. The judge can see Strands orchestration, the HITL pause, the bounded repository action, and the receipt rather than relying on narration.

## Built with
- Strands Agents SDK
- Strands `HumanInTheLoop`
- Python
- pre-existing Operational Waste Recovery as the deterministic evidence engine
- Git repository state inspection
- GitHub Actions
- OpenAI model provider through Strands for the explicit credentialed demo path

## Pre-existing work disclosure
This hackathon project was created during the Agents for Humans submission period, but it incorporates pre-existing work as follows:

- **Operational Waste Recovery / ReworkTrace:** canonical coding-agent event persistence, deterministic repeated-work analysis, evidence projection and Recovery Capsule generation. Reused baseline is pinned to commit `e1c8bc8f3d9d57b87ba8adce62fe7f8ea78bc6a7`.
- **Reality Handoff:** pre-existing design work informed the evidence → readiness → bounded action → approval → verification pattern. Its source package is not copied into this subproject.
- **Agent Reliability Preflight / DriftGuard:** pre-existing design work informed the fail-closed rule that deterministic blockers outrank semantic model judgment. Its source package is not copied into this subproject.

New hackathon work includes the Strands orchestration/tool layer, Recovery Preflight for this workflow, action/receipt contracts, HITL boundary, bounded repository action, stale-evidence/replay/path handling, judge scenarios, credentialed live-model path, architecture and submission material.

## Machine-checkable judge scenarios
The deterministic judge receipt executes three isolated scenarios:

1. **approved positive** — READY → NEEDS_HUMAN → EXECUTED → replay ALREADY_EXISTS;
2. **human denied** — proposal exists but mutating tool is not invoked → zero mutation;
3. **stale evidence after proposal/approval** — persisted capsule identity changes → executor rejects → zero mutation.

The receipt explicitly does not claim LLM reasoning quality, customer use, realized savings, or hackathon placement.

## Source
https://github.com/leadingproblemsolver/operational-waste-recovery/tree/hackathon/agents-for-humans-recovery-agent/hackathons/agents-for-humans/recovery-agent

The repository uses the MIT license at the repository root.

## Live demo
LIVE_DEMO_URL_TODO

A live demo is optional under the contest rules but should be added if the credentialed/deployment receipt is produced because it strengthens Technical Implementation.

## Demo video
DEMO_VIDEO_URL_TODO

## ≤5-minute video sequence

### 0:00–0:35 — Problem / audience / proof target
> Coding agents can reconstruct investigations that already happened. Recovery Agent restores the exact prior evidence and surfaces only when one bounded repository action needs a human decision.

Show the public PR and pre-existing-work disclosure.

### 0:35–1:05 — Architecture
Show:

```text
history + repo
→ OWR evidence
→ Strands
→ deterministic preflight
→ one action
→ HumanInTheLoop
→ executor rereads evidence
→ receipt
```

State: model orchestration is not evidence authority and human approval is necessary but not sufficient if the evidence has gone stale.

### 1:05–2:30 — Successful Strands run
Run the credentialed Strands agent. Keep the tool path visible:
- inspect history;
- inspect repository;
- load evidence;
- preflight;
- propose action;
- visible `HumanInTheLoop` approval;
- execute;
- show exact returned receipt and `.recovery` artifact.

### 2:30–3:15 — Denial
Show the denial branch. The key visible outcome is **zero mutation**.

### 3:15–4:00 — Stale evidence
Show or replay the deterministic judge receipt where evidence changes between proposal and execution. Execution must reject even after approval, with the repository unchanged.

### 4:00–4:35 — External proof
Show exact-head green CI, judge receipt artifact, public repository and—if produced—the live deployment URL/credentialed receipt.

### 4:35–4:55 — Close
> Recovery Agent gives Strands autonomy over orchestration, not permission to invent evidence or bypass a human. The system surfaces only at the bounded decision point and proves what happened afterward.

## Current proof state
Already verified:
- public draft PR;
- Strands orchestration/tool contract;
- native HITL configuration;
- deterministic preflight;
- approved/denied/stale/replay behavior;
- dedicated CI green on the latest verified implementation head;
- OWR core CI/runtime proof remains green alongside the hackathon branch;
- credentialed live-model workflow staged.

Still pending and therefore not claimed:
- credentialed Strands model receipt;
- public live demo/deployment URL;
- public ≤5-minute video;
- Devpost submitted receipt;
- judge response / placement.

## Claim boundary
Repeated-work similarity is evidence of recurrence, not proof that labor or money was wasted. Recovery Agent does not claim realized savings, production scale, customer adoption, or placement without separate receipts.
