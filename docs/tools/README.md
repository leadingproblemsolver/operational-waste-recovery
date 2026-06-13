# Tool Integration Guide

MODE: MANUAL
BRAAT BLOCK: Tool integration discipline
MISSION: Explain what tool, when to integrate it, and where it fits in the pipeline.

Do not integrate a tool because it is fashionable. Integrate only when a resource recovery metric cannot improve without it.

## Active tools now

| Tool | Status | What it does | Where in pipeline | When to use |
|---|---:|---|---|---|
| JSONL | active | Portable event stream | `pipeline.ingest` | Always first proof format |
| SQLite | active | Inspectable local storage | `storage.sqlite_store` | Default local proof DB |
| CLI | active | Proof path runner | `owrp.cli` | Required for ingest/status/validate/query |

## Deferred tools

| Tool | Status | What it does | Where it will fit | Integration gate |
|---|---:|---|---|---|
| GitHub API | deferred | PRs, commits, files touched | observation ingestion | Local JSONL proves duplicate work recovery |
| Slack API | deferred | Incident messages and reasoning traces | incident event stream | Manual incident JSONL retrieval becomes painful |
| PagerDuty API | deferred | Alert and incident timeline | incident event stream | Need real MTTR baseline |
| Jira/Linear API | deferred | Ticket updates and remediation | incident event stream | Incident nodes need ticket evidence |
| ClickHouse | deferred | High-volume event storage | storage | SQLite becomes too slow for actual event volume |
| Neo4j/Memgraph | deferred | Graph traversal at scale | incident reasoning graph | SQLite incident edge queries become insufficient |
| OpenAI API | deferred | Optional summarization/capsules | execution_context | Local deterministic capsules are not enough |
| pgvector | deferred | Vector retrieval | retrieval | Token-overlap retrieval stops finding useful matches |
| OpenTelemetry | deferred | runtime spans | observation ingestion | Need production event capture, not sample JSONL |

## Integration rule

Every tool must answer:

```text
What resource does it measure or recover?
Where does it write inspectable proof?
Which CLI command proves it works?
```

If those answers are unclear, do not integrate the tool.
