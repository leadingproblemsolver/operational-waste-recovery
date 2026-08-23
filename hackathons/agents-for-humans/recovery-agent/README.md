# Recovery Agent — Agents for Humans

**Track:** Professional Agents  
**Core:** coding-agent history + repository state → repeated-work evidence → Recovery Capsule → deterministic preflight → one bounded next action → human approval → execution receipt.

Recovery Agent is not another coding copilot. It detects when a developer or coding agent is about to reconstruct investigation that has already happened, restores the evidence, and surfaces only when one bounded repository action needs approval.

## End-to-end behavior

```mermaid
flowchart LR
    A[Coding-agent history] --> B[OWR deterministic analysis]
    R[Current Git repo state] --> S[Strands Recovery Agent]
    B --> C[Observed repeated-work finding]
    C --> D[Exact episodes + Recovery Capsule]
    D --> S
    S --> P{Deterministic Recovery Preflight}
    P -->|BLOCKED| X[Stop: missing evidence/dependency]
    P -->|READY| Q[One Recovery Action proposal]
    Q --> H{HumanInTheLoop approval}
    H -->|deny| N[Stop: zero mutation]
    H -->|approve| E[Write one evidence-linked recovery note]
    E --> V[Action receipt / replay-safe ALREADY_EXISTS]
```

## Why Strands

Strands owns the agent loop and tool orchestration. Read-only evidence tools and deterministic proposal/preflight tools are allow-listed. `execute_approved_recovery_action` is deliberately the only mutating tool and is not allow-listed, so Strands `HumanInTheLoop` must approve it before execution.

The model does **not** determine whether evidence exists, whether a finding is persisted, whether preflight passes, or whether a side effect occurred. Those boundaries remain deterministic and receipt-backed.

## Install

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

AWS credentials/configuration are required for the default Strands model path. The deterministic core tests do not call a model.

## Run

First ingest coding-agent history with the reused OWR engine. Then run:

```bash
recovery-agent \
  --owr-root /path/to/owr-state \
  --repo /path/to/git/repo \
  --prompt "Recover the strongest repeated investigation and prepare one bounded next action."
```

Expected journey:

1. Strands calls `inspect_coding_history`.
2. Strands calls `inspect_repository`.
3. It chooses at most one persisted finding.
4. It calls `get_recovery_evidence`.
5. It calls `run_recovery_preflight`.
6. If preflight is ready, it calls `propose_bounded_recovery_action`.
7. Before `execute_approved_recovery_action`, Strands `HumanInTheLoop` prompts the human.
8. Denial stops with zero mutation; approval writes exactly one `.recovery/recovery-<finding>.md` note.
9. The tool returns an `EXECUTED` or replay-safe `ALREADY_EXISTS` receipt.

## Failure behavior

- no repeated-work finding → `NO_ACTION` at the agent level
- missing persisted finding → preflight `BLOCKED`
- missing Recovery Capsule → preflight `BLOCKED`
- unreadable/non-Git repository → preflight `BLOCKED`
- path escape attempt → rejected
- evidence changes between proposal and execution → rejected
- duplicate execution → existing note preserved; no overwrite
- human denial → Strands prevents mutating tool execution

## Pre-existing work disclosure

This hackathon subproject was created during the **Agents for Humans** submission period.

It incorporates and depends on pre-existing work as follows:

- **Operational Waste Recovery / ReworkTrace (pre-existing):** canonical coding-agent event storage, deterministic repeated-work analysis, evidence review projection, SQLite persistence, and Recovery Capsule generation. This project pins the reused baseline at OWR commit `e1c8bc8f3d9d57b87ba8adce62fe7f8ea78bc6a7`.
- **Reality Handoff Agent (pre-existing design work):** the evidence → deterministic readiness → exact bounded action → human approval → verification/handoff pattern informed this agent's control boundary. No Reality Handoff source package is copied into this subproject.
- **Agent Reliability Preflight / DriftGuard (pre-existing design work):** the fail-closed principle that deterministic blockers outrank semantic model judgment informed `run_recovery_preflight`. No DriftGuard source package is copied into this subproject.

### New work for Agents for Humans

- Strands `Agent` orchestration
- Strands tool surface around OWR evidence + repo state
- deterministic Recovery Preflight for this workflow
- `RecoveryAction` / `ActionReceipt` contracts
- Strands `HumanInTheLoop` approval boundary
- bounded repository Recovery Note action
- replay/evidence-drift/path-containment failure handling
- hackathon-specific tests, demo, architecture, and deployment work

## Evidence boundary

Repeated-work similarity is evidence of recurrence, not proof of wasted labor. Token/cost fields remain bounded estimates where applicable. Recovery Agent never claims realized ROI or savings without external measurement.
