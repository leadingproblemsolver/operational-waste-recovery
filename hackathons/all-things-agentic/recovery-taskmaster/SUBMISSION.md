# Recovery Taskmaster — Submission Pack

## One-line pitch

Recovery Taskmaster is a Gemini + Google ADK coding-continuity agent that detects already-completed investigation, restores the exact evidence into an isolated workspace, takes one bounded recovery action, and independently verifies the result before declaring the workflow complete.

## Inspiration

Coding agents make it cheap to start work and surprisingly expensive to remember what already happened. Across long or interrupted engineering sessions, the same investigation can be reconstructed: files are reread, the same failure path is rediscovered, and context is rebuilt before useful work resumes. Recovery Taskmaster treats that lost continuity as an operational workflow problem rather than another prompt problem.

## What it does

Given a run ID, Recovery Taskmaster autonomously completes one recovery workflow:

1. creates a sanitized coding-history + workspace fixture;
2. uses persisted Operational Waste Recovery evidence to identify the strongest repeated-work finding;
3. inspects the exact source episodes and Recovery Capsule;
4. stops if required evidence is missing;
5. materializes exactly one `.recovery/recovery-<finding>.md` artifact inside the bounded workspace;
6. independently rereads the file and verifies its SHA-256 receipt;
7. terminates only at `VERIFIED` or an explicit blocked/failure state.

The result is not a recommendation. It is a completed, inspectable action with a receipt.

## How we built it

**Contest-specific stack**
- Gemini 3.5
- Google Agent Development Kit (ADK)
- FastAPI ADK service
- Cloud Run
- four scoped Python tools
- isolated `/tmp/recovery-taskmaster/<run_id>` workspaces
- SHA-256 action receipts

**Pre-existing dependency, explicitly disclosed**
Operational Waste Recovery is pinned at commit `e1c8bc8f3d9d57b87ba8adce62fe7f8ea78bc6a7`. It supplies canonical persistence, deterministic repeated-work detection, evidence projection, and Recovery Capsule generation. The Google ADK/Gemini Taskmaster application layer, autonomous workflow, scoped tools, receipt verification, Cloud Run packaging, tests, and submission work are new for this contest.

Reality Handoff and Agent Reliability Preflight informed the proof-carrying/fail-closed design pattern; their source packages are not copied into this project.

## Architectural discipline

The LLM is not trusted to establish facts about the history or its own side effects.

- persisted OWR data decides whether a finding/capsule exists;
- `run_id` is validated and every filesystem path is contained under the isolated run root;
- the model gets no arbitrary filesystem or shell tool;
- the only write tool has a fixed target shape under `.recovery/`;
- replay preserves the original note rather than overwriting it;
- the verification tool independently rereads the action artifact and recomputes its hash;
- observed recurrence remains separate from inferred avoidable work.

## Challenges

The key design challenge was preserving meaningful autonomy without giving the agent broad machine authority. The solution was to make the agent autonomous over **workflow ordering and completion**, while deterministic tools retain authority over evidence existence, path boundaries, the only permitted mutation, and final verification.

## Accomplishments

Current repository-level receipts:
- bounded workflow tests for successful action, replay, blocked evidence, and workspace escape rejection;
- explicit ADK model/tool contract test;
- Cloud Run container build and `/healthz` smoke in CI;
- public draft PR that cleanly separates contest-specific work from the pinned pre-existing OWR baseline.

Do not replace this section with stronger claims until the corresponding receipts exist:
- credentialed Gemini run — pending
- public Cloud Run URL — pending
- live Cloud execution ending `VERIFIED` — pending
- public demo video — pending
- Devpost submitted receipt — pending
- judge result/placement — not claimed

## What we learned

A useful agentic control plane does not need unrestricted tools. For this workflow, autonomy becomes easier to trust when the possible state transitions are narrow and externally verifiable: `OBSERVED → action → receipt → independently VERIFIED`, with explicit `BLOCKED/FAILED` exits.

## What's next

For the submission, the remaining work is receipt production rather than feature expansion: deploy the exact branch to Cloud Run, perform one credentialed Gemini/ADK run, capture the `VERIFIED` terminal state and Google Cloud execution evidence, record the demo, and submit.

---

# ≤4-minute demo sequence

## 0:00–0:25 — Problem + proof target

Show the public PR and say:

> Coding agents often reconstruct investigation that already happened. Recovery Taskmaster turns that lost continuity into a bounded autonomous workflow. The success criterion is not a chatbot response: the agent must create one evidence-linked recovery artifact and independently verify its receipt.

Show the pre-existing-work disclosure briefly.

## 0:25–0:50 — Architecture

Show the README Mermaid diagram:

`Cloud Run → Gemini 3.5 / ADK → prepare → inspect persisted evidence → materialize → independently verify SHA → VERIFIED`

State explicitly:

> Gemini controls orchestration. Deterministic tools control evidence truth, paths, mutation shape, and verification.

## 0:50–2:20 — Live Google Cloud run

Open the actual Cloud Run ADK service.

Prompt:

```text
Complete a recovery workflow for run_id judge-demo-01. Do the work end to end and stop only at VERIFIED or an explicit blocked state.
```

Keep the tool trace visible. The judge should see:
- `prepare_demo_run`
- `inspect_recovery_evidence`
- `materialize_recovery_capsule`
- `verify_recovery_receipt`
- terminal `VERIFIED`

Do not cut away from the action sequence if avoidable.

## 2:20–2:50 — Undeniable action proof

Show the materialization receipt:
- bounded target path
- SHA-256
- evidence IDs
- `overwritten: false`

Then show the verification result where `expected_sha256 == actual_sha256` and status is `VERIFIED`.

## 2:50–3:15 — Failure/replay proof

Run or show CI evidence for:
- invalid/missing finding → `BLOCKED`, zero action;
- replay → `ALREADY_EXISTS`, same hash, no overwrite;
- invalid `run_id` cannot escape the workspace.

## 3:15–3:40 — Production receipt

Show:
- Cloud Run service URL;
- `/healthz` returning `200` and `recovery_taskmaster`;
- Google Cloud service/revision or execution trace;
- green GitHub Actions run for the exact submission head.

## 3:40–3:55 — Close

> Recovery Taskmaster demonstrates a narrower form of reliable autonomy: the model is free to complete the workflow, but it cannot invent the evidence, escape the action boundary, or certify its own work.

Stop. No roadmap montage or unrelated artifact tour.
