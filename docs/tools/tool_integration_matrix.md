# Tool Integration Matrix

MODE: MANUAL
BRAAT BLOCK: External dependency gate
MISSION: Prevent overarchitecture by forcing tools through measurable gates.

| Tool | Resource recovered | Earliest sprint | Pipeline location | Implement only after |
|---|---|---:|---|---|
| GitHub | engineer hours, duplicated debugging | 08 | ingestion adapter before `pipeline.ingest` | JSONL duplicate detection is useful |
| Slack | incident cognition | 08 | incident event stream | Incident ontology works on sample incidents |
| PagerDuty | MTTR | 08 | incident event stream | MTTR field exists in incident metadata |
| Jira | remediation history | 08 | incident event stream | Incidents need ticket linkage |
| Linear | remediation history | 08 | incident event stream | Same as Jira, not both at once |
| Datadog | observations and metrics | 09 | incident event stream | Human-entered observations are insufficient |
| Grafana | dashboards referenced | 09 | incident event stream | Need referenced metric panels |
| Kibana | logs referenced | 09 | incident event stream | Need log search history |
| ClickHouse | event volume handling | 10 | storage replacement | SQLite status/query becomes slow |
| Neo4j | graph traversal | 10 | incident graph storage | SQLite edge traversal becomes hard |
| pgvector | semantic retrieval | 11 | retrieval | lexical retrieval misses repeated work |
| OpenAI | capsule summarization | 11 | execution_context | deterministic capsules produce low signal |

Do not add a second tool in the same category before the first one has proof output.
