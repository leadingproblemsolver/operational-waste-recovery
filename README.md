# OWRP — Operational Waste Recovery Platform

OWRP is a local-first telemetry system for measuring and recovering expensive technical organizational resources.

It does not start as a SaaS product, dashboard, agent, or AI memory layer.

It starts as a proof ledger.

The first proof target is:

```text
raw JSONL event
→ canonical interaction event
→ SQLite storage
→ duplicate/context waste detection
→ recovery calculation
→ local report
```

## Core objective

OWRP measures operational waste and converts it into recoverable resources:

```text
LLM tokens
LLM cost
engineer minutes
incident investigation time
context reconstruction overhead
```

The system only claims value when the waste is:

```text
measured
stored
inspectable
reproducible
reported
```

## Non-negotiables

```text
No dashboard before measurement proof.
No external integrations before local JSONL proof.
No unused abstractions.
No fake paths.
No fake functions.
No circular imports.
No self-imports.
No architecture that does not exist.
```

## Project structure

```text
src/owrp/
├── core/
│   ├── models.py
│   ├── hashing.py
│   ├── paths.py
│   ├── config.py
│   └── resource_accounting.py
│
├── pipeline/
│   ├── ingest.py
│   ├── deduplicate.py
│   ├── validate.py
│   └── reports.py
│
├── storage/
│   ├── sqlite_store.py
│   ├── duplicate_store.py
│   └── schema.sql
│
├── retrieval/
│   ├── query.py
│   └── similar_incidents.py
│
├── execution_context/
│   └── capsules.py
│
└── cli.py
```

## Folder roles

### `core/`

Defines the shared units of the machine.

Examples:

```text
InteractionEvent
hashing helpers
resource accounting formulas
paths
config
```

Rule:

```text
core/ may be imported by others.
core/ must not import pipeline, storage, retrieval, or execution_context.
```

### `pipeline/`

Transforms data.

Examples:

```text
ingest JSONL
validate records
deduplicate events
generate reports
```

### `storage/`

Persists proof.

Examples:

```text
SQLite database
interaction_events table
duplicate_events table
```

### `retrieval/`

Finds useful past records.

Examples:

```text
query local events
retrieve similar incidents
```

### `execution_context/`

Builds smaller reusable context outputs.

Examples:

```text
context capsules
known issue summaries
reduced prompt context
```

## Input and output locations

### Input

Put raw JSONL files here:

```text
data/sample_events.jsonl
```

or:

```text
data/input/*.jsonl
```

### Outputs

```text
data/owrp.sqlite
logs/owrp.log
reports/weekly_recovery.json
reports/weekly_recovery.md
```

## Canonical JSONL event format

Each JSONL line should represent one LLM work event.

Example:

```json
{"event_id":"evt_001","timestamp":"2026-06-12T10:00:00Z","user_id":"u_001","repo_id":"repo_owrp","source":"manual_jsonl","model_name":"gpt-4.1-mini","prompt_tokens":1200,"completion_tokens":300,"total_tokens":1500,"cost_usd":0.01,"classification":"debugging","files_read":["src/owrp/core/models.py"],"files_modified":[]}
```

Minimum important fields:

```text
event_id
timestamp
user_id
repo_id
source
model_name
prompt_tokens
completion_tokens
total_tokens
cost_usd
classification
files_read
files_modified
```

## Setup

Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install requirements:

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Environment

Create `.env` from `.env.example`.

Required local defaults:

```env
OWRP_DB_PATH=data/owrp.sqlite
OWRP_LOG_PATH=logs/owrp.log
OWRP_REPORT_PATH=reports/weekly_recovery.json
OWRP_SAMPLE_INPUT=data/sample_events.jsonl
```

Optional:

```env
OPENAI_API_KEY=
```

The OpenAI key is not required for local proof.

## Local proof path

Run from repo root:

```powershell
python -m owrp.cli ingest --input data/sample_events.jsonl
python -m owrp.cli status
python -m owrp.cli validate
python -m owrp.cli report
python -m owrp.cli query "debugging" --limit 10
python -m pytest
```

## Expected proof

A successful local run should produce:

```text
data/owrp.sqlite
logs/owrp.log
reports/weekly_recovery.json
```

`status` should show stored interactions.

`validate` should return:

```text
VALIDATE OK
```

`query` should return local matches after ingestion.

## Sprint sequence

```text
00_resource_accounting
01_observation_layer
02_deduplication_engine
03_context_reconstruction
04_recovery_layer
05_incident_reasoning_graph
06_retrieval_cli_proof
07_distribution_reports
08_external_tool_gates
```

## Sprint rules

Each sprint must answer one question:

```text
00 Can we define measurable waste?
01 Can we observe events?
02 Can we detect duplication?
03 Can we detect repeated context reconstruction?
04 Can we calculate recovered resources?
05 Can we represent incident reasoning?
06 Can we retrieve useful local evidence?
07 Can we publish reports?
08 Can we safely integrate external tools?
```

## External tools policy

External tools are gated.

Do not integrate them until local proof works.

### Allowed later

```text
OpenAI
LiteLLM
Langfuse
OpenTelemetry
GitHub
Slack
PagerDuty
Jira
Linear
Neo4j
ClickHouse
```

### Not allowed before local proof

```text
dashboard
SaaS auth
billing
Kubernetes
microservices
vector database
graph database
Slack bot
PagerDuty app
VSCode extension
```

## Git hygiene

Do not commit:

```text
.env
data/owrp.sqlite
logs/owrp.log
__pycache__/
*.pyc
src/owrp.egg-info/
```

These should be covered by `.gitignore`.

## Definition of done

The project is locally functional when this chain works:

```text
ingest
→ status
→ validate
→ report
→ query
→ pytest
```

The project is not done because the architecture exists.

It is done only when the local proof path produces inspectable output.
