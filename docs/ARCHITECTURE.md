# Architecture

```text
canonical / OpenAI-style / mapped generic JSONL
→ bounded parser and provider adapter
→ secret rejection or optional pre-storage redaction
→ immutable validated Interaction records
→ atomic idempotent SQLite upsert
→ repo-scoped lexical duplicate analysis
→ deterministic context capsules and recovery reports
→ CLI / JSON / CSV / read-only HTTP API
```

## Boundaries

- `adapters.py` maps external records to the canonical interaction contract.
- `privacy.py` detects credential-like material and performs explicit redaction.
- `pipeline/ingest.py` owns size limits, parsing, atomicity, and rejection reporting.
- `storage/sqlite_store.py` owns persistence, analysis, query, repository summaries, and purge.
- `pipeline/reports.py` renders evidence-bounded JSON and Markdown reports.
- `server.py` is read-only and token-gated beyond loopback.

No vector database, message broker, external LLM, graph database, or SaaS service is required by the active runtime.


```mermaid
flowchart LR
    %% USER / ENTRY
    U[Operator<br/>single recovery request]

    %% GOOGLE RUNTIME
    subgraph GC[Google Cloud Runtime]
        CR[Cloud Run<br/>Google ADK Service]
        G[Gemini 3.5 Flash<br/>Agent Orchestrator]
    end

    %% AGENT TOOLS
    subgraph T[Scoped ADK Tool Surface]
        P[prepare_demo_run]
        E[inspect_recovery_evidence]
        M[materialize_recovery_capsule]
        V[verify_recovery_receipt]
    end

    %% HOST CONTROL
    subgraph HST[Deterministic Host Control]
        O[(Persisted OWR<br/>SQLite Evidence)]
        SM[Host State Machine<br/>OBSERVED → EVIDENCE_READY<br/>→ ACTION_PENDING → EXECUTED]
        W[Bounded Recovery Target]
        R{Independent<br/>Reread + Settlement}
    end

    %% TERMINAL STATES
    OK[VERIFIED<br/>+ Receipt]
    BL[BLOCKED]
    FL[FAILED]

    %% MAIN FLOW
    U --> CR
    CR --> G

    G --> P
    P --> O

    G --> E
    E --> O

    G --> M
    M --> SM

    SM -->|persist ACTION_PENDING<br/>before mutation| W

    G --> V
    V --> W
    V --> R

    R -->|expected state matches| OK
    R -->|missing / unauthorized evidence| BL
    R -->|state mismatch| FL

    %% AMBIGUOUS EXECUTION RECOVERY
    W -. side effect may succeed<br/>before worker crash .-> SM
    SM -. fresh process reconciles<br/>target before retry .-> R
```

Gemini / Google ADK owns:
- choosing the next scoped tool
- orchestrating the multi-step workflow

Deterministic host code owns:
- evidence existence
- finding authorization
- legal state transitions
- path containment
- the permitted mutation
- ACTION_PENDING persistence
- reconcile-before-retry
- final verification

```mermaid
stateDiagram-v2
    [*] --> OBSERVED
    OBSERVED --> EVIDENCE_READY: inspect persisted evidence
    EVIDENCE_READY --> ACTION_PENDING: authorize + persist ambiguity boundary
    ACTION_PENDING --> EXECUTED: execute or reconcile existing effect
    EXECUTED --> VERIFIED: independent reread matches
    OBSERVED --> BLOCKED: evidence invalid / missing
    EVIDENCE_READY --> BLOCKED: unauthorized
    EXECUTED --> FAILED: reread mismatch
    VERIFIED --> [*]
    BLOCKED --> [*]
    FAILED --> [*]
```
